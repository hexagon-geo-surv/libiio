VITA 49.2 Architecture
======================

The `libiio` VITA 49.2 Backend enables robust, native integration with modern standard IF context devices. These devices typically emit I/Q data and contexts directly using VITA 49.2 VRT (VITA Radio Transport) structures over standard sockets (e.g., UDP broadcast, multicast, or TCP).

By interpreting `struct vrt_packet` natively, libiio maps dynamic VITA Stream IDs and payloads directly into its internal device map without requiring a rigid vendor-specific plugin.

Features
--------

- **Automatic Discovery**: Automatically discovers remote VITA 49.2 endpoints transmitting UDP datagrams.
- **Parsing/Generation Engine**: High-performance, low-level engine conforming strictly to the VRT standard packing rules for Type 0-7 packets.
- **TDD Validated**: The underlying `vita49_packet.h` interface has been constructed using extensive test-driven unit validation inside `tests/api/test_vita49.c`.
- **Endianness Safety**: Built-in getters/setters abstract standard network-byte order structures, decoupling protocol conversion from IIO hardware translations.
- **Dynamic Context**: Includes deep support for Context Indicator Field (CIF0) flags (like Bandwidth, Sample Rate, and Frequency Offset).

VITA 49.2 C Structures
----------------------

The internal libiio backend implements standard mappings using the VITA 49.2 structures in the C domain.
The C API supports decomposing standard VRT datagrams dynamically.

.. c:struct:: vrt_header
   
   Represents the VITA 49.2 packet header layout. Encapsulates fixed data such as `packet_type` and `packet_size_words`.

.. c:struct:: vrt_trailer
   
   Represents the VITA 49.2 packet trailer layout, including state and event indicators.

.. c:struct:: vrt_packet

   The complete parsed representation of a VITA 49.2 packet including fields for Stream ID, Class ID, Timestamp, payload pointer, sizes, and parsed header/trailer data. 

.. c:struct:: vrt_cif_fields

   A structure encapsulating Context Indicator Field 0 (CIF0) decoded payload fields. This struct enables intuitive property access over varying payload formats without requiring bit-level indexing. Common decoded properties include ``bandwidth``, ``sample_rate``, and ``rf_reference_frequency``.

.. c:function:: int vrt_parse_packet(const uint32_t *buf, size_t words, struct vrt_packet *pkt)

   Parses a raw 32-bit word UDP data stream into a validated `struct vrt_packet`.

.. c:function:: int vrt_parse_cif_payload(const struct vrt_packet *pkt, struct vrt_cif_fields *cif)

   Evaluates the Context Indicator fields inside a `VRT_PKT_TYPE_IF_CONTEXT` payload and deserializes them into strongly typed struct fields.
