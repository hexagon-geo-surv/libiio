# SPDX-License-Identifier: LGPL-2.1-or-later
#
# libiio - Library for interfacing industrial I/O (IIO) devices
#
# Copyright (C) 2026 Analog Devices, Inc.

import os
import tempfile
import pytest

# We explicitly import the newly created module from the examples directory.
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../examples"))
import vrt_mapping_validate

def test_syntax_validator_valid_config():
    valid_conf_content = """
    # Map Stream 0x12345678, CIF0 Bit 21 to ad9361-phy sampling_frequency
    0x12345678,21,ad9361-phy,channel,voltage0,true,sampling_frequency
    # Comment line
    0x00000001, 5, device2, device, none, none, sample_rate
    """
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(valid_conf_content)
        temp_path = f.name
        
    try:
        mappings, errors = vrt_mapping_validate.validate_mapping_syntax(temp_path)
        assert errors == 0
        assert len(mappings) == 2
        
        # Verify first mapping
        assert mappings[0]['stream_id'] == 0x12345678
        assert mappings[0]['cif0_bit'] == 21
        assert mappings[0]['device_name'] == 'ad9361-phy'
        assert mappings[0]['attr_type'] == 'channel'
        assert mappings[0]['channel_name'] == 'voltage0'
        assert mappings[0]['is_output'] is True
        assert mappings[0]['attr_name'] == 'sampling_frequency'
        
        # Verify second mapping
        assert mappings[1]['stream_id'] == 1
        assert mappings[1]['cif0_bit'] == 5
        assert mappings[1]['attr_type'] == 'device'
        assert mappings[1]['is_output'] is True
    finally:
        os.remove(temp_path)

def test_syntax_validator_invalid_config():
    invalid_conf_content = """
    # Missing fields
    0x12345678,21,ad9361-phy,channel,voltage0,true
    
    # Invalid bit (out of bounds)
    0x12345678, 35, ad9361-phy, channel, voltage0, true, freq
    
    # Invalid boolean
    0x12345678, 1, ad9361-phy, channel, voltage0, yes_maybe, freq

    # Invalid attr_type
    0x12345678, 2, ad9361-phy, magical, voltage0, true, freq
    """
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(invalid_conf_content)
        temp_path = f.name
        
    try:
        mappings, errors = vrt_mapping_validate.validate_mapping_syntax(temp_path)
        assert errors == 4
        # In the original python script design we continue on error and record the error 
        # count but don't append to mapping list for that bad line.
        assert len(mappings) == 0
    finally:
        os.remove(temp_path)
