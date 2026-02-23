iiod VITA-49.2 Integration Workflow
===================================

The traditional `iiod` networking architecture has been augmented to support functioning as an edge VITA 49.2 translator. 
`iiod` can be configured to start a dynamic VRT UDP thread, which intercepts and maps VITA 49 Context and Command packets natively to underlying `libiio` backends (such as configuring local system DSP variables on an `ad9361-phy`).

Configuration Mapping Files
---------------------------
To define which `libiio` attributes should be modified when a particular VITA-49.2 packet arrives, you can provide `iiod` with a translation mapping file:

.. code-block:: bash

   iiod --vrt-mapping /etc/libiio/vrt_mapping.conf

The file maps specific VITA Stream IDs and CIF0 (Context Indicator Field 0) evaluation bits directly to a target destination `[device]/[channel]/[attribute]`.

**Format Specification:**
The CSV-style mapping config file utilizes the following structure:

``stream_id, cif0_bit, device_name, attr_type, channel_name, is_output, attr_name``

- **stream_id**: The targeted 32-bit hexadecimal identifier (e.g. `0x1234ABCD`)
- **cif0_bit**:  The physical bit evaluating to present in CIF0 (e.g., `21` for Sample Rate, `29` for Bandwidth).
- **device_name**: The strict hardware `libiio` device name.
- **attr_type**: The type of attribute to target (`channel`, `device`, or `debug`).
- **channel_name**: The hardware channel designation. (Use `none` if targeting `device` or `debug` attributes).
- **is_output**: `true` or `false` to set the channel direction target. (Use `none` if targeting `device` or `debug` attributes).
- **attr_name**: The specific device attribute string to mutate (e.g. `rf_bandwidth`).

**Example: `vrt_mapping.conf`**

.. code-block:: text

   # Map IF Context Stream 0x12345678, CIF0 Bit 21 to ad9361-phy channel sample rate
   0x12345678,21,ad9361-phy,channel,voltage0,true,sampling_frequency
   
   # Map IF Context Stream 0x12345678, CIF0 Bit 29 to ad9361-phy device attribute
   0x12345678,29,ad9361-phy,device,none,none,global_device_attr
   
   # Map IF Context Stream 0x12345678, CIF0 Bit 18 to ad9361-phy debug attribute
   0x12345678,18,ad9361-phy,debug,none,none,temperature_test

Offline Validation Workflows
----------------------------
It can be dangerous to deploy mapping files out of cycle without confirming they won't syntax error or target invalid system topology attributes.

A CLI validation tool is provided within the Python bindings tree. 
You can use the tool to dry-run validate a configuration layout entirely offline.

.. code-block:: bash
   
   cd bindings/python/examples
   python3 vrt_mapping_validate.py --config /path/to/vrt_mapping.conf

Active Hardware Validation Workflow
-----------------------------------
This tool can also actively connect to a live hardware context (running `iiod`) to verify that the channels and attributes defined in the mapping actually exist on physical devices.

.. code-block:: bash
   
   python3 vrt_mapping_validate.py --config config.conf --uri "ip:192.168.1.10"
