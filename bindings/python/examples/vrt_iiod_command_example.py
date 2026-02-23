import socket
import struct
import time
import argparse

def send_vrt_command(host="127.0.0.1", port=1235, sample_rate=100e6, bandwidth=80e6):
    """
    Constructs a VITA-49.2 IF Context packet directing iiod to 
    change 'sampling_frequency' and 'rf_bandwidth' properties.
    """
    
    # Header logic
    # packet_type = 4 (Context)
    # has_class_id = 1 (Class ID present)
    # packet_size_words = 10 words (40 bytes)
    # For a big-endian network word, header is:
    # 0100 (Type) | 1 (c) | 0 (t) | 00 (reserved) | 00 (tsi) | 00 (tsf) | 0000 (pkt_count) | 0000000000001010 (size)
    # -> 0b01001000000000000000000000001010 = 0x4800000a
    # Wait, in vrt_simulator.c: hdr->packet_size_words = 10 -> 0x4000000a?
    # Let's just pack it manually based on vrt_simulator.c's bitfields:
    # 0x4100000A (in Little Endian layout translated to Network Byte Order in C simulator might have differences).
    # Assuming standard VITA49.2 layout: Type is top 4 bits.
    header_word = (4 << 28) | (1 << 27) | 10
    
    stream_id = 0x12345678
    oui = 0x0012A200
    class_code = 0x00000001
    
    # CIF0
    # Bit 21 (Sample Rate) and Bit 30 (Bandwidth)
    cif0 = (1 << 21) | (1 << 30)

    print(f"Sending VITA 49.2 Command to {host}:{port}")
    print(f" -> Target Sample Rate: {sample_rate} Hz")
    print(f" -> Target Bandwidth  : {bandwidth} Hz")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Pack the double values
    # struct.pack('>d', float) gives an 8 byte IEEE 754 value in big-endian
    # We unpack it into two 32-bit big-endian words to maintain standard VRT format.
    sr_bytes = struct.pack('>d', sample_rate)
    sr_hi, sr_lo = struct.unpack('>II', sr_bytes)

    bw_bytes = struct.pack('>d', bandwidth)
    bw_hi, bw_lo = struct.unpack('>II', bw_bytes)

    # Build the packet (10 words)
    packet = struct.pack('>IIIIIIIIII',
        header_word,
        stream_id,
        oui,
        class_code,
        cif0,
        sr_hi, sr_lo,
        bw_hi, bw_lo,
        0 # Trailer or optional space
    )

    sock.sendto(packet, (host, port))
    sock.close()
    print("Command Sent!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send VITA-49.2 command packet to iiod")
    parser.add_argument("--host", default="127.0.0.1", help="Target iiod host IP")
    parser.add_argument("--port", type=int, default=1235, help="Target iiod UDP port (default 1235)")
    parser.add_argument("--sr", type=float, default=100000000.0, help="Sample rate in Hz")
    parser.add_argument("--bw", type=float, default=80000000.0, help="Bandwidth in Hz")
    parser.add_argument("--start-iiod", action="store_true", help="Optionally start the local iiod build for testing")
    args = parser.parse_args()

    iiod_proc = None
    if args.start_iiod:
        import subprocess
        import os
        
        iiod_path = os.path.join(os.path.dirname(__file__), "../../../build/iiod/iiod")
        print(f"Starting local iiod at {iiod_path}")
        iiod_proc = subprocess.Popen([iiod_path])
        time.sleep(1) # wait for iiod to start up

    try:
        send_vrt_command(args.host, args.port, args.sr, args.bw)
    finally:
        if iiod_proc:
            print("Terminating local iiod")
            iiod_proc.terminate()
            iiod_proc.wait()
