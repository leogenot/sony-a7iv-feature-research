#!/usr/bin/env python3
"""Resolve named app backup properties and their constructor references."""

from __future__ import annotations

import argparse
import io
import json
import struct
import sys
from pathlib import Path


DEFAULT_NAMES = [
    "BKID_APP_SETTING_MODE_SHUTTER",
    "BKID_APP_SETTING_SHUTTER_ANGLE",
    "BKID_APP_SETTING_LOG_SHOOTING",
    "BKID_APP_SETTING_EMBED_LUT_FILE",
    "BKID_APP_SETTING_SELECT_LUT",
    "BKID_APP_SETTING_APPLY_LUT",
    "BKID_APP_SETTING_STILL_LOG_SHOOTING",
    "BKID_APP_CUBE_FILE_OPERATION_DESTINATION",
]


class Elf:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        shoff = struct.unpack_from("<Q", self.data, 40)[0]
        entsize, count, _ = struct.unpack_from("<HHH", self.data, 58)
        self.sections = [
            struct.unpack_from("<IIQQQQIIQQ", self.data, shoff + i * entsize)
            for i in range(count)
        ]

    def va(self, file_offset: int) -> int:
        section = next(
            s
            for s in self.sections
            if s[1] != 8 and s[4] <= file_offset < s[4] + s[5]
        )
        return section[3] + file_offset - section[4]

    def offset(self, address: int) -> int:
        section = next(
            s
            for s in self.sections
            if s[1] != 8 and s[3] <= address < s[3] + s[5]
        )
        return section[4] + address - section[3]

    def relative_relocations(self) -> dict[int, list[int]]:
        result: dict[int, list[int]] = {}
        for section in self.sections:
            if section[1] != 4:
                continue
            for offset in range(section[4], section[4] + section[5], section[9]):
                target, info, addend = struct.unpack_from("<QQq", self.data, offset)
                if info & 0xFFFFFFFF == 1027:
                    result.setdefault(addend, []).append(target)
        return result

    def text(self) -> tuple[int, bytes]:
        executable = [s for s in self.sections if s[1] == 1 and s[2] & 4]
        section = max(executable, key=lambda s: s[5])
        return section[3], self.data[section[4] : section[4] + section[5]]


def named_id(elf: Elf, relocations: dict[int, list[int]], name: str):
    string_offset = elf.data.index(name.encode() + b"\0")
    string_va = elf.va(string_offset)
    for pointer_va in relocations.get(string_va, []):
        record_offset = elf.offset(pointer_va) - 8
        identifier, length = struct.unpack_from("<II", elf.data, record_offset)
        if length == len(name) + 1:
            return identifier, pointer_va - 8
    raise ValueError("No name record found for %s" % name)


def constructed_at(elf: Elf, value: int):
    """Find MOVZ W0,#lo followed by MOVK W0,#hi,LSL#16."""
    base, text = elf.text()
    result = []
    for offset in range(0, len(text) - 8, 4):
        first, second = struct.unpack_from("<II", text, offset)
        if first & 0xFF80001F != 0x52800000:
            continue
        if second & 0xFF80001F != 0x72800000:
            continue
        immediate = ((first >> 5) & 0xFFFF) | (((second >> 5) & 0xFFFF) << 16)
        if immediate == value:
            result.append(base + offset)
    return result


def load_backup(path, pmca_root):
    if path is None:
        return None
    if pmca_root is None:
        raise ValueError("--pmca-root is required with --backup")
    sys.path.insert(0, str(pmca_root))
    from pmca.backup import BackupFile

    return BackupFile(io.BytesIO(path.read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("appfw", type=Path)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--pmca-root", type=Path)
    parser.add_argument("--name", action="append", dest="names")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    elf = Elf(args.appfw)
    relocations = elf.relative_relocations()
    backup = load_backup(args.backup, args.pmca_root)
    rows = []
    for name in args.names or DEFAULT_NAMES:
        identifier, record_va = named_id(elf, relocations, name)
        property_id = 0x02CF0000 | identifier
        row = {
            "name": name,
            "internal_id": "0x%04x" % identifier,
            "name_record_va": "0x%x" % record_va,
            "property_id": "0x%08x" % property_id,
            "constructor_references": [
                "0x%x" % address for address in constructed_at(elf, property_id)
            ],
        }
        if backup is not None:
            try:
                prop = backup.getProperty(property_id)
                row["backup"] = {
                    "size": len(prop.data),
                    "value_hex": prop.data.hex(),
                    "attributes": "0x%02x" % prop.attr,
                }
            except Exception:
                row["backup"] = None
        rows.append(row)

    rendered = json.dumps(rows, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()

