VITA 49.2 Native Python Bindings
==================================

The `libiio` package exposes native C interfaces to the Python domain via standard `ctypes` bindings. 
This grants Python scripts real-time, low-overhead parsing logic of raw incoming VITA 49 packets over the network, effectively extending edge translation functionality into Python.

Parsing High-Level VITA 49.2 Contexts
-------------------------------------
Network UDP datagram representations of packets can be cast instantly into strongly-typed parameters using `iio.VRTPacket()`.

.. code-block:: python

   import socket
   import iio

   # Listen for UDP VRT contexts broadcast on Port 1234
   sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   sock.bind(("0.0.0.0", 1234))

   data, addr = sock.recvfrom(2048)

   # Abstract native memory parsing cleanly
   pkt = iio.VRTPacket(data)

   print(f"Packet type: {pkt.packet_type}")
   if pkt.has_stream_id:
       print(f"Discovered Stream ID: 0x{pkt.stream_id:08X}")

Extracting CIF0 (Context Indicator Field) Contexts
--------------------------------------------------
The `libiio` bindings support native standard bitwise sequential parsing implementations for nested properties like `Bandwidth` or `Sample Rate`.

The `cif_fields()` method decodes Context packets directly into a validated wrapper.

.. code-block:: python

   import iio
   
   # Data has been received as pkt_bytes
   pkt = iio.VRTPacket(pkt_bytes)

   if pkt.packet_type == 4:  # VRT_PKT_TYPE_IF_CONTEXT
       cif = pkt.cif_fields()
       if cif:
           print(f"CIF0 Configuration Flags: 0x{cif.cif0:08X}")
           
           if cif.has_bandwidth:
               print(f"Bandwidth: 0x{cif.bandwidth} Hz")
               
           if cif.has_sample_rate:
               print(f"Sample Rate: 0x{cif.sample_rate} Hz")

Low-Level Payload Interfacing
-----------------------------
If interacting with custom payloads or packet models, developers can utilize the internal native endian-translation getters provided on `VRTPacket`. 
These will automatically convert values dynamically from Network to Host Byte Order without error-prone struct manipulation.

.. code-block:: python

   # Extracts standard 32-bit Integer at Word offset 0
   my_custom_word = pkt.get_payload_word(0)

   # Extracts standard 64-bit IEEE 754 Float at Word offset 2
   my_custom_value = pkt.get_payload_double(2)
