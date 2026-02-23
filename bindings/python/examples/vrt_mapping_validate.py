#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# libiio - Library for interfacing industrial I/O (IIO) devices
#
# Copyright (C) 2026 Analog Devices, Inc.

import argparse
import sys
import os

def validate_mapping_syntax(filepath):
    """
    Parses the mapping file and validates basic syntax.
    Returns a list of parsed mappings defined as dictionaries.
    """
    mappings = []
    errors = 0
    warnings = 0

    if not os.path.isfile(filepath):
        print(f"Error: Could not find mapping file '{filepath}'", file=sys.stderr)
        return None, 1

    with open(filepath, 'r') as f:
        for idx, line in enumerate(f):
            line = line.strip()
            # Ignore comments and blanks
            if not line or line.startswith('#'):
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) != 7:
                print(f"Error: Line {idx+1}: Expected 7 comma-separated fields, got {len(parts)}.")
                print(f"  -> '{line}'")
                errors += 1
                continue

            stream_id_str, cif0_str, device, attr_type, channel, is_out_str, attr = parts

            # Validate Stream ID
            try:
                stream_id = int(stream_id_str, 0)
            except ValueError:
                print(f"Error: Line {idx+1}: Invalid stream_id '{stream_id_str}'. Must be integer or hex.")
                errors += 1
                continue

            # Validate CIF0 Bit
            try:
                cif0_bit = int(cif0_str)
                if cif0_bit < 0 or cif0_bit > 31:
                    print(f"Error: Line {idx+1}: cif0_bit '{cif0_bit}' out of range (0-31).")
                    errors += 1
                    continue
            except ValueError:
                print(f"Error: Line {idx+1}: Invalid cif0_bit '{cif0_str}'.")
                errors += 1
                continue
                
            # Validate attr_type
            attr_type_lower = attr_type.lower()
            if attr_type_lower not in ['channel', 'device', 'debug']:
                print(f"Error: Line {idx+1}: Invalid attr_type '{attr_type}'. Use 'channel', 'device', or 'debug'.")
                errors += 1
                continue

            # Validate Output flag
            is_out = False
            is_out_str_lower = is_out_str.lower()
            if is_out_str_lower in ['1', 'true', 't', 'yes', 'y', 'none', '']:
                is_out = True
            elif is_out_str_lower in ['0', 'false', 'f', 'no', 'n']:
                is_out = False
            else:
                print(f"Error: Line {idx+1}: Invalid is_output flag '{is_out_str}'. Use 'true' or 'false'.")
                errors += 1
                continue

            mappings.append({
                'line_num': idx + 1,
                'stream_id': stream_id,
                'stream_id_hex': hex(stream_id),
                'cif0_bit': cif0_bit,
                'device_name': device,
                'attr_type': attr_type_lower,
                'channel_name': channel,
                'is_output': is_out,
                'attr_name': attr
            })

    print(f"[Syntax] Parsed {len(mappings)} mappings with {errors} errors and {warnings} warnings.")
    return mappings, errors

def validate_against_context(mappings, uri):
    """
    Connects to an IIO Context and verifies if the mapped hardware devices,
    channels, and attributes exist.
    """
    try:
        import iio
    except ImportError:
        print("Error: The 'iio' python module is not installed or discoverable.")
        print("Set PYTHONPATH or install libiio bindings to run active validation.")
        return 1
    
    print(f"\n[Active Context Validation] Connecting to IIO context: '{uri}'...")
    try:
        ctx = iio.Context(uri)
    except Exception as e:
        print(f"Error: Failed to connect to IIO context '{uri}': {e}")
        return 1

    print(f"Connected to {ctx.name} context with {len(ctx.devices)} devices.")
    errors = 0

    for m in mappings:
        dev_name = m['device_name']
        attr_type = m['attr_type']
        chn_name = m['channel_name']
        attr_name = m['attr_name']
        is_out = m['is_output']
        line_num = m['line_num']

        print(f"  Validating line {line_num}: Stream {m['stream_id_hex']} -> {dev_name}/[{attr_type}]{chn_name}/{attr_name}")

        dev = ctx.find_device(dev_name)
        if not dev:
            print(f"    [!] Error: Device '{dev_name}' not found in context.")
            errors += 1
            continue
        
        if attr_type == 'channel':
            chn = dev.find_channel(chn_name, is_out)
            if not chn:
                # Fallback direction check
                chn = dev.find_channel(chn_name, not is_out)
                if not chn:
                    print(f"    [!] Error: Channel '{chn_name}' not found on device '{dev_name}'.")
                    errors += 1
                    continue
            
            if attr_name not in chn.attrs:
                print(f"    [!] Error: Attribute '{attr_name}' not found on channel '{chn_name}'.")
                available = list(chn.attrs.keys())
                if available:
                    print(f"        Available attributes on this channel: {', '.join(available[:5])}{'...' if len(available) > 5 else ''}")
                errors += 1
                continue
                
        elif attr_type == 'device':
            if attr_name not in dev.attrs:
                print(f"    [!] Error: Device attribute '{attr_name}' not found on device '{dev_name}'.")
                errors += 1
                continue
                
        elif attr_type == 'debug':
            if attr_name not in dev.debug_attrs:
                print(f"    [!] Error: Debug attribute '{attr_name}' not found on device '{dev_name}'.")
                errors += 1
                continue
                
        print("    [OK] Valid.")

    print(f"Context validation complete with {errors} missing constraints.")
    return errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate a VITA-49.2 iiod mapping configuration file.")
    parser.add_argument("--config", required=True, help="Path to the vrt_mapping.conf file to validate")
    parser.add_argument("--uri", help="Optional IIO context URI (e.g., 'local:', 'ip:192.168.2.1') to actively validate mappings against hardware.")
    
    args = parser.parse_args()

    mappings, syntax_failures = validate_mapping_syntax(args.config)
    
    if syntax_failures > 0 or not mappings:
        print("\nValidation failed due to syntax errors. Fix them to proceed with hardware validation.")
        sys.exit(1)

    if args.uri:
        ctx_failures = validate_against_context(mappings, args.uri)
        if ctx_failures > 0:
            print("\nValidation failed against hardware context.")
            sys.exit(1)
        else:
            print("\nSuccess: All syntax and hardware validation checks passed!")
            sys.exit(0)
    else:
        print("\nSuccess: Syntax validation checks passed! (Use --uri to perform active hardware validation)")
        sys.exit(0)
