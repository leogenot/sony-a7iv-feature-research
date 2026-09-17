#!/usr/bin/env python3
"""Decode aggregate Sony protocol-3 property data from a snapshot JSON."""

import argparse
import json
import struct
from pathlib import Path


SCALAR_TYPES = {
    0x0001: ("INT8", "b"),
    0x0002: ("UINT8", "B"),
    0x0003: ("INT16", "h"),
    0x0004: ("UINT16", "H"),
    0x0005: ("INT32", "i"),
    0x0006: ("UINT32", "I"),
    0x0007: ("INT64", "q"),
    0x0008: ("UINT64", "Q"),
}
ARRAY_MASK = 0x4000
STRING_TYPE = 0xFFFF


def unpack_value(data, offset, datatype):
    if datatype == STRING_TYPE:
        length = data[offset]
        offset += 1
        end = offset + length * 2
        if end > len(data):
            raise ValueError("Truncated PTP string")
        value = data[offset:end].decode("utf-16le", "replace").rstrip("\0")
        return value, end

    if datatype & ARRAY_MASK:
        base_type = datatype & ~ARRAY_MASK
        if offset + 4 > len(data):
            raise ValueError("Truncated PTP array count")
        count = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if count > 10000:
            raise ValueError("Unreasonable PTP array count: %d" % count)
        values = []
        for _ in range(count):
            value, offset = unpack_value(data, offset, base_type)
            values.append(value)
        return values, offset

    try:
        _name, value_format = SCALAR_TYPES[datatype]
    except KeyError:
        raise ValueError("Unsupported PTP datatype 0x%04x" % datatype)
    size = struct.calcsize("<" + value_format)
    if offset + size > len(data):
        raise ValueError("Truncated scalar value")
    return struct.unpack_from("<" + value_format, data, offset)[0], offset + size


def unpack_descriptor(data, offset, index):
    start = offset
    if offset + 6 > len(data):
        raise ValueError("Truncated Sony descriptor header")
    code, datatype = struct.unpack_from("<HH", data, offset)
    get_set = data[offset + 4]
    enabled = data[offset + 5]
    offset += 6
    default, offset = unpack_value(data, offset, datatype)
    current, offset = unpack_value(data, offset, datatype)
    if offset >= len(data):
        raise ValueError("Missing descriptor form")
    form = data[offset]
    offset += 1
    base_type = datatype & ~ARRAY_MASK
    datatype_name = "STRING" if datatype == STRING_TYPE else SCALAR_TYPES.get(
        base_type, ("UNKNOWN",)
    )[0]
    descriptor = {
        "index": index,
        "offset": start,
        "property_code": code,
        "datatype": datatype,
        "datatype_name": datatype_name,
        "array": bool(datatype & ARRAY_MASK),
        "get_set": get_set,
        "enabled": enabled,
        "default": default,
        "current": current,
        "form": form,
    }

    if form == 1:
        values = []
        for _ in range(3):
            value, offset = unpack_value(data, offset, datatype)
            values.append(value)
        descriptor["range"] = values
    elif form == 2:
        if offset + 2 > len(data):
            raise ValueError("Truncated enumeration count")
        count = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        values = []
        for _ in range(count):
            value, offset = unpack_value(data, offset, datatype)
            values.append(value)
        descriptor["enum"] = values
    elif form != 0:
        raise ValueError("Unknown descriptor form %d" % form)

    # Recent Sony descriptors can append a replacement settable-value list.
    # A following property code is at least 0x5000, so a value below 0x0200 is
    # an additional count rather than the next descriptor.
    if form == 2 and offset + 2 <= len(data):
        secondary_count = struct.unpack_from("<H", data, offset)[0]
        if secondary_count < 0x0200:
            offset += 2
            values = []
            for _ in range(secondary_count):
                value, offset = unpack_value(data, offset, datatype)
                values.append(value)
            descriptor["enum_secondary"] = values

    descriptor["size"] = offset - start
    return descriptor, offset


def contains_value(descriptor, target):
    for key in ("default", "current", "range", "enum", "enum_secondary"):
        value = descriptor.get(key)
        if value == target or isinstance(value, list) and target in value:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--find", type=int, default=180000)
    args = parser.parse_args()

    snapshot = json.loads(args.snapshot.read_text())
    raw = snapshot.get("all_property_info_raw")
    if not raw:
        raise SystemExit("Snapshot has no aggregate protocol-3 property data")
    data = bytes.fromhex(raw)
    if len(data) < 8:
        raise SystemExit("Aggregate property data is too short")
    count, reserved = struct.unpack_from("<II", data, 0)
    offset = 8
    descriptors = []
    for index in range(count):
        descriptor, offset = unpack_descriptor(data, offset, index)
        descriptors.append(descriptor)
    if offset != len(data):
        raise SystemExit(
            "Decoded %d of %d bytes; %d remain"
            % (offset, len(data), len(data) - offset)
        )

    matches = [item for item in descriptors if contains_value(item, args.find)]
    print("Header descriptors: %d" % count)
    print("Reserved header word: %d" % reserved)
    print("Decoded descriptors: %d" % len(descriptors))
    print("Decoded bytes: %d/%d" % (offset, len(data)))
    print("Descriptors containing %d: %d" % (args.find, len(matches)))
    for item in matches:
        print(
            "  0x%04x offset=0x%x enabled=%d current=%s"
            % (
                item["property_code"],
                item["offset"],
                item["enabled"],
                item["current"],
            )
        )

    if args.output:
        args.output.write_text(json.dumps(descriptors, indent=2) + "\n")
        print("Saved decoded descriptors: %s" % args.output.resolve())


if __name__ == "__main__":
    main()
