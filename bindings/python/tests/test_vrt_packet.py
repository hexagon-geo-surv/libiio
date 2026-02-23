import pytest
import struct
import iio

def test_vrt_packet_parsing():
    """Test that the python iio.VRTPacket structure correctly maps memory to the C structure."""
    
    # Manually pack a simple Context packet buffer (10 words)
    # Header: Type 4, Class ID present, Count 0, Size 10
    # 0b 0100 (Type) | 1 (Class) | 0 (Trailer) | 00 (Rsvd) | 00 (TSI) | 00 (TSF) | 0000 (Count) | 0000000000001010 (Size)
    # -> 0x4800000A
    header = 0x4800000A
    stream_id = 0xAABBCCDD
    oui = 0x012345
    class_code = 0x6789ABCD
    class_id_w1 = oui
    class_id_w2 = class_code

    # Payload 6 words
    cif0 = (1 << 21) | (1 << 29)
    
    # 56.0e6 Bandwidth (evaluates first since bit 29 > bit 21)
    bw_bytes = struct.pack('>d', 56e6)
    bw_hi, bw_lo = struct.unpack('>II', bw_bytes)
    
    # 100.0e6 Sample Rate
    sr_bytes = struct.pack('>d', 100e6)
    sr_hi, sr_lo = struct.unpack('>II', sr_bytes)
    
    # Build 10 word packet
    pkt_bytes = struct.pack('>IIIIIIIIII',
        header,       # Word 0
        stream_id,    # Word 1
        class_id_w1,  # Word 2
        class_id_w2,  # Word 3
        cif0,         # Payload 0
        bw_hi, bw_lo, # Payload 1,2
        sr_hi, sr_lo, # Payload 3,4
        0             # Payload 5
    )
    
    vrt = iio.VRTPacket(pkt_bytes)
    
    assert vrt.packet_type == 4
    assert vrt.packet_size_words == 10
    
    assert vrt.has_stream_id is True
    assert vrt.stream_id == stream_id
    
    assert vrt.has_class_id is True
    expected_class_id = (oui << 32) | class_code
    assert vrt.class_id == expected_class_id
    
    assert vrt.payload_size_words == 6
    
    # Assert helpers decode network byte order and IEEE floats from words
    assert vrt.get_payload_word(0) == cif0
    assert vrt.get_payload_double(1) == 56e6
    assert vrt.get_payload_double(3) == 100e6

    # Test new VRTCifFields high-level wrapper
    cif = vrt.cif_fields()
    assert cif is not None
    assert cif.cif0 == cif0
    
    assert cif.has_bandwidth is True
    assert cif.bandwidth == 56e6
    
    assert cif.has_sample_rate is True
    assert cif.sample_rate == 100e6
    
    assert cif.has_temperature is False
    assert cif.temperature is None
