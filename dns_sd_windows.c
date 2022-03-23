// SPDX-License-Identifier: LGPL-2.1-or-later
/*
 * libiio - Library for interfacing industrial I/O (IIO) devices
 *
 * Copyright (C) 2014-2020 Analog Devices, Inc.
 * Author: Adrian Suciu <adrian.suciu@analog.com>
 *
 * Based on https://github.com/mjansson/mdns/blob/ce2e4f789f06429008925ff8f18c22036e60201e/mdns.c
 * which is Licensed under Public Domain
 */

#include <stdio.h>
#include <errno.h>
#include <winsock2.h>
#include <iphlpapi.h>

#include "debug.h"
#include "dns_sd.h"
#include "iio-lock.h"
#include "iio-private.h"
#include "deps/mdns/mdns.h"

#if HAVE_IPV6
static const unsigned char localhost[] = {
	0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 1
};
static const unsigned char localhost_mapped[] = {
	0, 0, 0,    0,    0,    0, 0, 0,
	0, 0, 0xff, 0xff, 0x7f, 0, 0, 1
};

static bool is_localhost6(const struct sockaddr_in6 *saddr6)
{
	const uint8_t *addr = saddr6->sin6_addr.s6_addr;

	return !memcmp(addr, localhost, sizeof(localhost)) ||
		!memcmp(addr, localhost_mapped, sizeof(localhost_mapped));
}
#endif

static bool is_localhost4(const struct sockaddr_in *saddr)
{
	return saddr->sin_addr.S_un.S_un_b.s_b1 == 127 &&
		saddr->sin_addr.S_un.S_un_b.s_b2 == 0 &&
		saddr->sin_addr.S_un.S_un_b.s_b3 == 0 &&
		saddr->sin_addr.S_un.S_un_b.s_b4 == 1;
}

static int open_client_sockets(int *sockets, unsigned int max_sockets)
{
	IP_ADAPTER_UNICAST_ADDRESS *unicast;
	IP_ADAPTER_ADDRESSES *adapter_address = 0;
	PIP_ADAPTER_ADDRESSES adapter;
	ULONG address_size = 8000;
	unsigned int i, ret, num_retries = 4, num_sockets = 0;
	struct sockaddr_in *saddr;
	unsigned long param = 1;
	int sock;

	/* When sending, each socket can only send to one network interface
	 * Thus we need to open one socket for each interface and address family */

	do {
		adapter_address = malloc(address_size);
		if (!adapter_address)
			return -ENOMEM;

		ret = GetAdaptersAddresses(AF_UNSPEC,
					   GAA_FLAG_SKIP_MULTICAST
#if HAVE_IPV6
					   | GAA_FLAG_SKIP_ANYCAST
#endif
					   , 0,
					   adapter_address, &address_size);
		if (ret != ERROR_BUFFER_OVERFLOW)
			break;

		free(adapter_address);
		adapter_address = 0;
	} while (num_retries-- > 0);

	if (!adapter_address || (ret != NO_ERROR)) {
		free(adapter_address);
		IIO_ERROR("Failed to get network adapter addresses\n");
		return num_sockets;
	}

	for (adapter = adapter_address; adapter; adapter = adapter->Next) {
		if (adapter->TunnelType == TUNNEL_TYPE_TEREDO)
			continue;
		if (adapter->OperStatus != IfOperStatusUp)
			continue;

		for (unicast = adapter->FirstUnicastAddress;
		     unicast; unicast = unicast->Next) {
			if (unicast->Address.lpSockaddr->sa_family == AF_INET) {
				saddr = (struct sockaddr_in *)unicast->Address.lpSockaddr;

				if (!is_localhost4(saddr) &&
				    num_sockets < max_sockets) {
					sock = mdns_socket_open_ipv4(saddr);
					if (sock >= 0)
						sockets[num_sockets++] = sock;
				}
			}
#if HAVE_IPV6
			else if (unicast->Address.lpSockaddr->sa_family == AF_INET6) {
				struct sockaddr_in6 *saddr6;

				saddr6 = (struct sockaddr_in6 *)unicast->Address.lpSockaddr;

				if (unicast->DadState == NldsPreferred &&
				    !is_localhost6(saddr6) &&
				    num_sockets < max_sockets) {
					sock = mdns_socket_open_ipv6(saddr6);
					if (sock >= 0)
						sockets[num_sockets++] = sock;
				}
			}
#endif
		}
	}

	free(adapter_address);

	for (i = 0; i < num_sockets; i++)
		ioctlsocket(sockets[i], FIONBIO, &param);

	return num_sockets;
}

static int query_callback(int sock, const struct sockaddr *from, size_t addrlen,
			  mdns_entry_type_t entry, uint16_t query_id,
			  uint16_t rtype, uint16_t rclass, uint32_t ttl,
			  const void *data, size_t size, size_t name_offset,
			  size_t name_length,
			  size_t record_offset, size_t record_length,
			  void *user_data)
{
	struct dns_sd_discovery_data *dd = user_data;
	char addrbuffer[64];
	char servicebuffer[64];
	char namebuffer[256];
	mdns_record_srv_t srv;

	if (!dd) {
		IIO_ERROR("DNS SD: Missing info structure. Stop browsing.\n");
		goto quit;
	}

	if (rtype != MDNS_RECORDTYPE_SRV)
		goto quit;

	getnameinfo(from, (socklen_t)addrlen, addrbuffer, NI_MAXHOST,
		    servicebuffer, NI_MAXSERV, NI_NUMERICSERV | NI_NUMERICHOST);

	srv = mdns_record_parse_srv(data, size, name_offset, name_length,
				    namebuffer, sizeof(namebuffer));
	IIO_DEBUG("%s : SRV %.*s priority %d weight %d port %d\n", addrbuffer,
		  MDNS_STRING_FORMAT(srv.name), srv.priority, srv.weight, srv.port);

	/* Go to the last element in the list */
	while (dd->next)
		dd = dd->next;

	if (srv.name.length > 1)
	{
		dd->hostname = malloc(srv.name.length);
		if (!dd->hostname)
			return -ENOMEM;

		iio_strlcpy(dd->hostname, srv.name.str, srv.name.length);
	}

	iio_strlcpy(dd->addr_str, addrbuffer, DNS_SD_ADDRESS_STR_MAX);
	dd->port = srv.port;

	IIO_DEBUG("DNS SD: added %s (%s:%d)\n",
		  dd->hostname, dd->addr_str, dd->port);

	/* A list entry was filled, prepare new item on the list */
	dd->next = zalloc(sizeof(*dd->next));
	if (!dd->next)
		IIO_ERROR("DNS SD mDNS Resolver : memory failure\n");

quit:
	return 0;
}

int dnssd_find_hosts(struct dns_sd_discovery_data **ddata)
{
	WORD versionWanted = MAKEWORD(1, 1);
	WSADATA wsaData;
	const char service[] = "_iio._tcp.local";
	size_t records, capacity = 2048;
	struct dns_sd_discovery_data *d;
	unsigned int i, isock, num_sockets;
	void *buffer;
	int sockets[32];
	int transaction_id[32];
	int ret = -ENOMEM;

	if (WSAStartup(versionWanted, &wsaData)) {
		printf("Failed to initialize WinSock\n");
		return -WSAGetLastError();
	}

	IIO_DEBUG("DNS SD: Start service discovery.\n");

	d = zalloc(sizeof(*d));
	if (!d)
		goto out_wsa_cleanup;
	/* pass the structure back, so it can be freed if err */
	*ddata = d;

	d->lock = iio_mutex_create();
	if (!d->lock)
		goto out_wsa_cleanup;

	buffer = malloc(capacity);
	if (!buffer)
		goto out_destroy_lock;

	IIO_DEBUG("Sending DNS-SD discovery\n");

	ret = open_client_sockets(sockets, ARRAY_SIZE(sockets));
	if (ret <= 0) {
		IIO_ERROR("Failed to open any client sockets\n");
		goto out_free_buffer;
	}

	num_sockets = (unsigned int)ret;
	IIO_DEBUG("Opened %d socket%s for mDNS query\n",
		  num_sockets, (num_sockets > 1) ? "s" : "");

	IIO_DEBUG("Sending mDNS query: %s\n", service);

	/* Walk through all the open interfaces/sockets, and send a query */
	for (isock = 0; isock < num_sockets; isock++) {
		ret = mdns_query_send(sockets[isock], MDNS_RECORDTYPE_PTR,
				      service, sizeof(service)-1, buffer,
				      capacity, 0);
		if (ret <= 0)
			IIO_ERROR("Failed to send mDNS query: errno %d\n", errno);

		transaction_id[isock] = ret;
	}

	/* This is a simple implementation that loops for 10 seconds or as long as we get replies
	 * A real world implementation would probably use select, poll or similar syscall to wait
	 * until data is available on a socket and then read it */
	IIO_DEBUG("Reading mDNS query replies\n");

	for (i = 0; i < 10; i++) {
		do {
			records = 0;

			for (isock = 0; isock < num_sockets; isock++) {
				if (transaction_id[isock] <= 0)
					continue;

				records += mdns_query_recv(sockets[isock],
							   buffer, capacity,
							   query_callback, d,
							   transaction_id[isock]);
			}
		} while (records);

		if (records)
			i = 0;

		Sleep(100);
	}

	for (isock = 0; isock < num_sockets; ++isock)
		mdns_socket_close(sockets[isock]);

	IIO_DEBUG("Closed socket%s\n", (num_sockets > 1) ? "s" : "");

	port_knock_discovery_data(&d);
	remove_dup_discovery_data(&d);

	ret = 0;
out_free_buffer:
	free(buffer);
out_destroy_lock:
	iio_mutex_destroy(d->lock);
out_wsa_cleanup:
	WSACleanup();
	return ret;
}

int dnssd_resolve_host(const char *hostname, char *ip_addr, const int addr_len)
{
	return -ENOENT;
}
