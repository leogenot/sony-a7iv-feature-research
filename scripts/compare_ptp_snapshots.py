#!/usr/bin/env python3
"""Compare Sony protocol-3 aggregate property descriptors in two snapshots."""

import argparse
import json
import struct
from pathlib import Path

from analyze_ptp_snapshot import unpack_descriptor


FIELDS = (
    "datatype",
    "get_set",
    "enabled",
    "default",
    "current",
    "form",
    "range",
    "enum",
    "enum_secondary",
)


def decode(path):
    snapshot = json.loads(path.read_text())
    raw = snapshot.get("all_property_info_raw")
    if not raw:
        raise ValueError("%s has no aggregate protocol-3 property data" % path)
    data = bytes.fromhex(raw)
    if len(data) < 8:
        raise ValueError("%s has truncated aggregate property data" % path)
    count, _reserved = struct.unpack_from("<II", data, 0)
    offset = 8
    result = {}
    for index in range(count):
        descriptor, offset = unpack_descriptor(data, offset, index)
        result[descriptor["property_code"]] = descriptor
    if offset != len(data):
        raise ValueError(
            "%s: decoded %d of %d bytes" % (path, offset, len(data))
        )
    return snapshot, result


def changed_fields(before, after):
    return [field for field in FIELDS if before.get(field) != after.get(field)]


def short(value):
    if isinstance(value, list):
        if len(value) > 8:
            return "%s ... (%d values)" % (value[:8], len(value))
        return repr(value)
    return repr(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument(
        "--enablement-only",
        action="store_true",
        help="show only additions, removals, and enable/get-set changes",
    )
    args = parser.parse_args()

    before_snapshot, before = decode(args.before)
    after_snapshot, after = decode(args.after)
    print("Before: %s" % args.before.resolve())
    print("After:  %s" % args.after.resolve())
    print(
        "Protocol: %s -> %s"
        % (
            before_snapshot.get("sony_protocol_version"),
            after_snapshot.get("sony_protocol_version"),
        )
    )

    changed = 0
    for code in sorted(before.keys() | after.keys()):
        left = before.get(code)
        right = after.get(code)
        if left is None:
            changed += 1
            print("0x%04x added" % code)
            continue
        if right is None:
            changed += 1
            print("0x%04x removed" % code)
            continue
        fields = changed_fields(left, right)
        if not fields:
            continue
        if args.enablement_only and not {"enabled", "get_set"}.intersection(fields):
            continue
        changed += 1
        print("0x%04x: %s" % (code, ", ".join(fields)))
        for field in fields:
            print("  %-14s %s -> %s" % (field, short(left.get(field)), short(right.get(field))))

    print("Changed descriptors shown: %d" % changed)


if __name__ == "__main__":
    main()
