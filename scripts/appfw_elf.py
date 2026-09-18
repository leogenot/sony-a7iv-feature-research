#!/usr/bin/env python3
"""Small offline helpers for Sony AArch64 appFw.so analysis.

The module only reads a locally extracted binary. It never writes to it.

Features:
- section/segment address translation
- R_AARCH64_RELATIVE relocation index (target -> addend and addend -> targets)
- generated name-record resolution ("NAME" -> id records that point at it)
- MOVZ/MOVK immediate search and ADRP+ADD/LDR address-reference search

Command-line use:

    python3 scripts/appfw_elf.py APPFW names PRODUCT_MODEL_LAX PRODUCT_MODEL_LS
    python3 scripts/appfw_elf.py APPFW refs 0x4f95b8c
    python3 scripts/appfw_elf.py APPFW imm 0x02cf1702
    python3 scripts/appfw_elf.py APPFW ptrs 0x37b7910 8
"""

from __future__ import annotations

import argparse
import bisect
import struct
import sys
from functools import cached_property
from pathlib import Path

R_AARCH64_RELATIVE = 1027


class AppElf:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        if self.data[:4] != b"\x7fELF" or self.data[4] != 2:
            raise ValueError("expected a 64-bit ELF file")
        shoff = struct.unpack_from("<Q", self.data, 40)[0]
        entsize, count, shstrndx = struct.unpack_from("<HHH", self.data, 58)
        raw = [
            struct.unpack_from("<IIQQQQIIQQ", self.data, shoff + i * entsize)
            for i in range(count)
        ]
        names_off = raw[shstrndx][4]
        self.sections = []
        for s in raw:
            end = self.data.index(b"\0", names_off + s[0])
            name = self.data[names_off + s[0] : end].decode()
            self.sections.append(
                dict(name=name, type=s[1], flags=s[2], addr=s[3], offset=s[4], size=s[5], entsize=s[9])
            )
        self.by_name = {s["name"]: s for s in self.sections}

    # -- address translation ------------------------------------------------
    def offset(self, va: int) -> int:
        for s in self.sections:
            if s["type"] != 8 and s["addr"] and s["addr"] <= va < s["addr"] + s["size"]:
                return s["offset"] + va - s["addr"]
        raise ValueError("VA 0x%x is not file-backed" % va)

    def va(self, off: int) -> int:
        for s in self.sections:
            if s["type"] != 8 and s["addr"] and s["offset"] <= off < s["offset"] + s["size"]:
                return s["addr"] + off - s["offset"]
        raise ValueError("offset 0x%x is not mapped" % off)

    def section_of(self, va: int) -> str | None:
        for s in self.sections:
            if s["addr"] and s["addr"] <= va < s["addr"] + s["size"]:
                return s["name"]
        return None

    def u8(self, va): return self.data[self.offset(va)]
    def u16(self, va): return struct.unpack_from("<H", self.data, self.offset(va))[0]
    def u32(self, va): return struct.unpack_from("<I", self.data, self.offset(va))[0]
    def i32(self, va): return struct.unpack_from("<i", self.data, self.offset(va))[0]
    def u64(self, va): return struct.unpack_from("<Q", self.data, self.offset(va))[0]

    def cstr(self, va: int, limit: int = 512) -> str:
        off = self.offset(va)
        end = self.data.find(b"\0", off, off + limit)
        return self.data[off : end if end >= 0 else off + limit].decode("latin1")

    # -- relocations ----------------------------------------------------------
    @cached_property
    def reloc_target_to_addend(self) -> dict[int, int]:
        result = {}
        for s in self.sections:
            if s["type"] != 4:
                continue
            for off in range(s["offset"], s["offset"] + s["size"], s["entsize"] or 24):
                target, info, addend = struct.unpack_from("<QQq", self.data, off)
                if info & 0xFFFFFFFF == R_AARCH64_RELATIVE:
                    result[target] = addend
        return result

    @cached_property
    def reloc_addend_to_targets(self) -> dict[int, list[int]]:
        result: dict[int, list[int]] = {}
        for target, addend in self.reloc_target_to_addend.items():
            result.setdefault(addend, []).append(target)
        for v in result.values():
            v.sort()
        return result

    def ptr(self, va: int) -> int:
        """Pointer stored at VA, honouring RELATIVE relocations."""
        return self.reloc_target_to_addend.get(va, self.u64(va))

    # -- strings ---------------------------------------------------------------
    def find_cstr(self, text: str) -> list[int]:
        needle = b"\0" + text.encode() + b"\0"
        result, start = [], 0
        while True:
            i = self.data.find(needle, start)
            if i < 0:
                return result
            result.append(self.va(i + 1))
            start = i + 1

    # -- code ------------------------------------------------------------------
    @cached_property
    def text(self) -> tuple[int, bytes]:
        s = self.by_name[".text"]
        return s["addr"], self.data[s["offset"] : s["offset"] + s["size"]]

    @cached_property
    def text_words(self):
        import array

        base, blob = self.text
        a = array.array("I")
        a.frombytes(blob[: len(blob) // 4 * 4])
        return base, a

    def movz_movk(self, value: int, reg_any: bool = True) -> list[int]:
        """Find MOVZ Wn/Xn,#lo ; MOVK same,#hi,LSL#16 constructing value."""
        base, words = self.text_words
        lo, hi = value & 0xFFFF, (value >> 16) & 0xFFFF
        result = []
        for i in range(len(words) - 1):
            a = words[i]
            if a & 0x7F800000 != 0x52800000 or (a >> 21) & 3:
                continue
            if (a >> 5) & 0xFFFF != lo:
                continue
            rd = a & 31
            for j in range(i + 1, min(i + 4, len(words))):
                b = words[j]
                if b & 0x7F800000 == 0x72800000 and (b >> 21) & 3 == 1 and b & 31 == rd and (b >> 5) & 0xFFFF == hi:
                    result.append(base + 4 * i)
                    break
        return result

    def adrp_refs(self, target: int) -> list[int]:
        """Find ADRP+ADD / ADRP+LDR pairs that materialise target (exact)."""
        base, words = self.text_words
        page = target & ~0xFFF
        result = []
        for i in range(len(words)):
            w = words[i]
            if w & 0x9F000000 != 0x90000000:
                continue
            pc = base + 4 * i
            imm = ((w >> 29) & 3) | (((w >> 5) & 0x7FFFF) << 2)
            if imm & (1 << 20):
                imm -= 1 << 21
            if (pc & ~0xFFF) + (imm << 12) != page:
                continue
            rd = w & 31
            for j in range(i + 1, min(i + 8, len(words))):
                x = words[j]
                if x & 0xFF800000 == 0x91000000 and (x >> 5) & 31 == rd:  # ADD imm
                    sh = (x >> 22) & 1
                    off = ((x >> 10) & 0xFFF) << (12 * sh)
                    if page + off == target:
                        result.append(pc)
                    break
                if x & 0x3B000000 == 0x39000000 and (x >> 5) & 31 == rd:  # LDR/STR unsigned imm
                    size = x >> 30
                    if (x >> 26) & 1:  # SIMD
                        size = size | (((x >> 23) & 1) << 2)
                    off = ((x >> 10) & 0xFFF) << size
                    if page + off == target:
                        result.append(pc)
                    break
        return result

    @cached_property
    def call_index(self) -> dict[int, list[int]]:
        base, words = self.text_words
        idx: dict[int, list[int]] = {}
        for i, w in enumerate(words):
            if w & 0xFC000000 == 0x94000000:  # BL
                imm = w & 0x3FFFFFF
                if imm & (1 << 25):
                    imm -= 1 << 26
                pc = base + 4 * i
                idx.setdefault(pc + imm * 4, []).append(pc)
        return idx

    def callers(self, fn: int) -> list[int]:
        return self.call_index.get(fn, [])

    def function_start(self, va: int, max_back: int = 0x4000) -> int:
        """Heuristic: walk back to a preceding RET/B and a STP x29,x30 or PACIASP."""
        base, words = self.text_words
        i = (va - base) // 4
        for k in range(i, max(i - max_back // 4, 0), -1):
            w = words[k]
            if w == 0xD503233F:  # paciasp
                return base + 4 * k
            if w & 0xFFC07FFF == 0xA9807BFD or w & 0xFFC07FFF == 0xA9007BFD:  # stp x29,x30,[sp,#..]!
                # accept only if preceded by ret/b/brk or a sub sp
                prev = words[k - 1]
                if prev & 0xFF8003FF == 0xD10003FF:  # sub sp,sp,#
                    return base + 4 * (k - 1)
                return base + 4 * k
            if w == 0xD65F03C0 and k != i:  # ret
                return base + 4 * (k + 1)
        return va

    # -- generated name records --------------------------------------------------
    def name_records(self, name: str) -> list[dict]:
        """Return records whose relocated pointer points at NAME.

        Two layouts are common in appFw.so:
          A: u32 id, u32 len, ptr name   (BKID, PRM tables)
          B: ptr name, u32 id, u32 len   (UIBIZ tables)
        """
        out = []
        for sva in self.find_cstr(name):
            for p in self.reloc_addend_to_targets.get(sva, []):
                rec = {"string": sva, "pointer_at": p}
                try:
                    i0, l0 = struct.unpack_from("<II", self.data, self.offset(p - 8))
                    i1, l1 = struct.unpack_from("<II", self.data, self.offset(p + 8))
                except ValueError:
                    i0 = l0 = i1 = l1 = None
                if l0 == len(name) + 1 or l0 == len(name):
                    rec.update(layout="id,len,ptr", id=i0, record=p - 8)
                elif l1 == len(name) + 1 or l1 == len(name):
                    rec.update(layout="ptr,id,len", id=i1, record=p)
                out.append(rec)
        return out


def _int(x: str) -> int:
    return int(x, 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("appfw", type=Path)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("names"); p.add_argument("names", nargs="+")
    p = sub.add_parser("refs"); p.add_argument("va", type=_int)
    p = sub.add_parser("imm"); p.add_argument("value", type=_int)
    p = sub.add_parser("ptrs"); p.add_argument("va", type=_int); p.add_argument("count", type=_int)
    p = sub.add_parser("callers"); p.add_argument("va", type=_int)
    a = ap.parse_args()
    elf = AppElf(a.appfw)
    if a.cmd == "names":
        for n in a.names:
            for r in elf.name_records(n) or [{"string": None}]:
                print(n, {k: (hex(v) if isinstance(v, int) else v) for k, v in r.items()})
    elif a.cmd == "refs":
        print("relocated pointers:", [hex(x) for x in elf.reloc_addend_to_targets.get(a.va, [])])
        print("adrp refs:", [hex(x) for x in elf.adrp_refs(a.va)])
    elif a.cmd == "imm":
        print([hex(x) for x in elf.movz_movk(a.value)])
    elif a.cmd == "ptrs":
        for i in range(a.count):
            va = a.va + 8 * i
            v = elf.ptr(va)
            s = ""
            try:
                if elf.section_of(v) == ".rodata":
                    s = elf.cstr(v, 80)
            except ValueError:
                pass
            print(hex(va), hex(v), elf.section_of(v), s)
    elif a.cmd == "callers":
        print([hex(x) for x in elf.callers(a.va)])


if __name__ == "__main__":
    sys.exit(main())
