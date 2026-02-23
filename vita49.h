/* SPDX-License-Identifier: LGPL-2.1-or-later */
/*
 * libiio - Library for interfacing industrial I/O (IIO) devices
 *
 * Copyright (C) 2026 Analog Devices, Inc.
 * Author: Travis Collins <travis.collins@analog.com>
 */

#ifndef __VITA49_H__
#define __VITA49_H__

#include <stdint.h>

/* VITA 49.2 Packet Types */
enum vrt_packet_type {
	VRT_PKT_TYPE_IF_DATA_NO_SID = 0x0,
	VRT_PKT_TYPE_IF_DATA_WITH_SID = 0x1,
	VRT_PKT_TYPE_EXT_DATA_NO_SID = 0x2,
	VRT_PKT_TYPE_EXT_DATA_WITH_SID = 0x3,
	VRT_PKT_TYPE_IF_CONTEXT = 0x4,
	VRT_PKT_TYPE_EXT_CONTEXT = 0x5,
	VRT_PKT_TYPE_COMMAND = 0x6,
	VRT_PKT_TYPE_EXT_COMMAND = 0x7,
};

/* TSI - Timestamp Integer */
enum vrt_tsi {
	VRT_TSI_NONE = 0,
	VRT_TSI_UTC = 1,
	VRT_TSI_GPS = 2,
	VRT_TSI_OTHER = 3,
};

/* TSF - Timestamp Fractional */
enum vrt_tsf {
	VRT_TSF_NONE = 0,
	VRT_TSF_SAMPLE_COUNT = 1,
	VRT_TSF_REAL_TIME = 2,
	VRT_TSF_FREE_RUNNING = 3,
};

/* VRT Packet Header (32 bits) */
struct vrt_header {
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
	uint32_t packet_size_words:16;  /* Packet Size in 32-bit words */
	uint32_t packet_count:4;        /* Packet Count (0-15 sequence counter) */
	uint32_t ts_fractional_format:2; /* Timestamp Fractional (TSF) Format */
	uint32_t ts_integer_format:2;   /* Timestamp Integer (TSI) Format */
	uint32_t reserved:2;            /* Reserved bits (must be 0) */
	uint32_t has_trailer:1;         /* Trailer Included Indicator (T bit) */
	uint32_t has_class_id:1;        /* Class ID Included Indicator (C bit) */
	uint32_t packet_type:4;         /* VRT Packet Type */
#else
	uint32_t packet_type:4;         /* VRT Packet Type */
	uint32_t has_class_id:1;        /* Class ID Included Indicator (C bit) */
	uint32_t has_trailer:1;         /* Trailer Included Indicator (T bit) */
	uint32_t reserved:2;            /* Reserved bits (must be 0) */
	uint32_t ts_integer_format:2;   /* Timestamp Integer (TSI) Format */
	uint32_t ts_fractional_format:2; /* Timestamp Fractional (TSF) Format */
	uint32_t packet_count:4;        /* Packet Count (0-15 sequence counter) */
	uint32_t packet_size_words:16;  /* Packet Size in 32-bit words */
#endif
};

/* VRT Trailer (32 bits) */
struct vrt_trailer {
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
	uint32_t associated_context_packet_count:7;      /* Count of linked Context packets */
	uint32_t context_packet_count_enable:1;          /* E bit: Associated Context Packet Count is valid */
	uint32_t state_and_event_indicators:12;          /* State and Event indicators (e.g., AGC, Cal Error) */
	uint32_t indicator_enables:12;                   /* Enables: Validates corresponding indicators */
#else
	uint32_t indicator_enables:12;                   /* Enables: Validates corresponding indicators */
	uint32_t state_and_event_indicators:12;          /* State and Event indicators (e.g., AGC, Cal Error) */
	uint32_t context_packet_count_enable:1;          /* E bit: Associated Context Packet Count is valid */
	uint32_t associated_context_packet_count:7;      /* Count of linked Context packets */
#endif
};

#endif /* __VITA49_H__ */
