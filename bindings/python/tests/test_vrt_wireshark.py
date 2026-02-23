import pytest
import subprocess
import time
import os
import pyshark

@pytest.fixture(scope="module")
def vrt_simulator():
    # Start the C-based simulator in the background
    bin_path = os.path.join(os.path.dirname(__file__), "../../../build/vrt_simulator")
    proc = subprocess.Popen([bin_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1) # wait for simulator to be ready
    yield proc
    proc.terminate()
    proc.wait()

import socket
from scapy.all import IP, UDP, wrpcap

def test_vrt_wireshark_capture(vrt_simulator):
    """
    Test that the vrt_simulator generates valid VITA 49 packets
    according to Wireshark's built-in VRT dissector.
    """
    # Create a UDP socket to receive the packets
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 1234))
    sock.settimeout(2.0)
    
    # Receive one packet
    try:
        data, addr = sock.recvfrom(2048)
    except socket.timeout:
        pytest.fail("Failed to receive UDP packet from simulator")
    finally:
        sock.close()
        
    # Create a pcap file using Scapy
    # We wrap the payload in IP/UDP headers to simulate a full packet for Wireshark
    pkt = IP(dst='127.0.0.1', src='127.0.0.1')/UDP(dport=1234, sport=addr[1])/data
    pcap_path = os.path.join(os.path.dirname(__file__), "test_vrt.pcap")
    wrpcap(pcap_path, pkt)
    
    # Process the pcap with pyshark
    capture = pyshark.FileCapture(
        pcap_path,
        decode_as={'udp.port==1234': 'vrt'}
    )
    
    # Read the first packet
    # FileCapture is an iterator
    pyshark_pkt = capture[0]
    
    # Verify UDP layer exists
    assert hasattr(pyshark_pkt, 'udp'), "Packet is not UDP"
    assert pyshark_pkt.udp.dstport == '1234'
    
    # Verify VRT layer exists (Wireshark recognized it as VITA 49)
    assert hasattr(pyshark_pkt, 'vrt'), "Packet was not recognized as VRT by Wireshark"
    
    # Check some basic VRT fields from the IF context packet
    assert pyshark_pkt.vrt.type == '4', f"Expected VRT Context packet (Type 4), got {pyshark_pkt.vrt.type}"
    assert pyshark_pkt.vrt.sid == '0x12345678', f"Expected Stream ID 0x12345678, got {pyshark_pkt.vrt.sid}"
    
    # Optional: check class ID elements since simulator sends OUI 0x0012A200 and Class Code 1
    assert hasattr(pyshark_pkt.vrt, 'oui')
    assert pyshark_pkt.vrt.oui == '0x12a200', f"Expected OUI 0x0012A200, got {pyshark_pkt.vrt.oui}"
    
    # In vrt_simulator.c, we send CIF0 with sample rate (bit 21) and bandwidth (bit 30)
    assert pyshark_pkt.vrt.cif0_samplerate == 'True'
    assert hasattr(pyshark_pkt.vrt, 'context_samplerate')
    
    # Cleanup
    capture.close()
    if os.path.exists(pcap_path):
        os.remove(pcap_path)
