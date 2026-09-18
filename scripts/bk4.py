#!/usr/bin/env python3
"""Read-only parser for Sony BK4 settings backups and regional profiles.

Layout follows Sony-PMCA-RE's pmca/backup parser. Regional update profiles
(0110_backup/SYSIPSX-DSLR/*/*.bin) contain two BK4 banks, the second at
0xF3000; a live service backup contains one. Checksums are always verified.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

PROFILE_BANK_OFFSETS = (0, 0xF3000)


@dataclass
class Prop:
    attr: int
    data: bytes
    reset: bytes
    capacity: int


class BK4:
    def __init__(self, blob: bytes, base: int = 0, label: str = ""):
        b = blob[base:]
        if b[12:16] != b"BK4\0":
            raise ValueError("%s: no BK4 header at 0x%x" % (label, base))
        ns, np_, data_off, data_size = struct.unpack_from("<IIII", b, 16)
        end = data_off + data_size
        if sum(b[:32]) + sum(b[36:end]) != struct.unpack_from("<I", b, 32)[0]:
            raise ValueError("%s: checksum mismatch" % label)
        self.label = label
        self.region = b[192:224].split(b"\0")[0].decode("latin1")
        self.version = b[64:96].split(b"\0")[0].decode("latin1")
        self.props: dict[int, Prop] = {}
        table = 256 + ns * 6
        for s in range(ns):
            count, first = struct.unpack_from("<HI", b, 256 + s * 6)
            for j in range(count):
                attr, ptr = struct.unpack_from("<HI", b, table + 6 * (first + j))
                if ptr == 0xFFFFFFFF:
                    continue
                size, off = ptr >> 24, ptr & 0xFFFFFF
                cap = size
                if size == 0xFF:
                    size = cap = struct.unpack_from("<H", b, off)[0]
                    off += 2
                elif size == 0:
                    size, cap = struct.unpack_from("<HH", b, off)
                    off += 4
                reset = b[off + cap : off + cap + size] if attr & 0x74 else b""
                self.props[s << 16 | j] = Prop(attr, b[off : off + size], reset, cap)

    def get(self, pid: int) -> Prop | None:
        return self.props.get(pid)


def load_backup(path: Path) -> list[BK4]:
    """Return all BK4 banks in a file (1 for live backups, 2 for profiles)."""
    blob = path.read_bytes()
    banks = []
    for base in PROFILE_BANK_OFFSETS:
        if base + 16 <= len(blob) and blob[base + 12 : base + 16] == b"BK4\0":
            banks.append(BK4(blob, base, "%s@0x%x" % (path.name, base)))
    if not banks:
        raise ValueError("%s: not a BK4 backup" % path)
    return banks


def profile_paths(update_root: Path) -> list[Path]:
    return sorted((update_root / "0110_backup").rglob("*.bin"))
