#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""
A Python script demonstrating how to use the 'iio' module to receive raw UDP 
VITA 49.2 packets and use the VRTPacket class to parse and extract their contents.
"""

import socket
import argparse
import sys
import iio

def main():
    parser = argparse.ArgumentParser(description="VITA 49.2 Packet Examiner Example")
    parser.add_argument("--port", type=int, default=1235, help="UDP Port to listen on (default 1235)")
    args = parser.parse_args()

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", args.port))
    sock.settimeout(10.0)

    print(f"Listening for VITA 49.2 packets on UDP port {args.port}...")

    try:
        data, addr = sock.recvfrom(2048)
        print(f"\nReceived {len(data)} bytes from {addr}")

        # Construct a VRTPacket instance from the raw payload
        try:
            pkt = iio.VRTPacket(data)
        except NotImplementedError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Failed to parse packet: {e}")
            sys.exit(1)

        print("\n--- VITA 49.2 Packet Parsed ---")
        print(f"Packet Type: {pkt.packet_type}")
        print(f"Packet Size: {pkt.packet_size_words} words ({pkt.packet_size_words * 4} bytes)")
        
        if pkt.has_stream_id:
            print(f"Stream ID: 0x{pkt.stream_id:08X}")
        
        if pkt.has_class_id:
            print(f"Class ID: 0x{pkt.class_id:016X}")
            
        print(f"Payload Size: {pkt.payload_size_words} words")

        if pkt.packet_type == 4:
            cif = pkt.cif_fields()
            if cif:
                print(f"CIF0 (Word 0): 0x{cif.cif0:08X}")
                
                if cif.has_bandwidth:
                    print(f"Found Bandwidth in payload: {cif.bandwidth} Hz")
                if cif.has_sample_rate:
                    print(f"Found Sample Rate in payload: {cif.sample_rate} Hz")
                if cif.has_rf_reference_frequency:
                    print(f"Found RF Reference Frequency: {cif.rf_reference_frequency} Hz")

    except socket.timeout:
        print("\nTimeout waiting for a packet.")
    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
