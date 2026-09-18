#!/usr/bin/env python3
"""Map every BKID_APP_* name record in appFw.so to its 0x02cfXXXX backup
property and, optionally, to values in a live backup and the 32 regional
profiles.

Name records are generated as (u32 id, u32 nul-inclusive length, ptr name)
and are resolved through R_AARCH64_RELATIVE relocations, never by numeric
coincidence. Constructor evidence (MOVZ/MOVK building the full property ID)
is reported with --constructors because it scans the whole .text section.

Examples:
    python3 scripts/bkid_inventory.py APPFW --grep 'LOG_SHOOTING|LUT'
    python3 scripts/bkid_inventory.py APPFW --grep ANAMORPH \
        --backup ~/Documents/Sony-PMCA-RE/a7iv-backup-602.bin \
        --update-root ~/Documents/fwtool.py/unpacked/firmware.tar_unpacked
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from appfw_elf import AppElf  # noqa: E402
from bk4 import load_backup, profile_paths  # noqa: E402

APP_SUBSYSTEM = 0x02CF0000


def bkid_names(e: AppElf, pattern: re.Pattern | None) -> list[tuple[str, int, int]]:
    result = []
    blob = e.data
    for m in re.finditer(rb"(?<=\0)(BKID_APP_[A-Z0-9_]+)(?=\0)", blob):
        name = m.group(1).decode()
        if pattern and not pattern.search(name):
            continue
        for r in e.name_records(name):
            if r.get("layout") == "id,len,ptr":
                result.append((name, r["id"], r["record"]))
    return sorted(set(result), key=lambda x: x[1])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("appfw", type=Path)
    ap.add_argument("--grep", help="regular expression applied to BKID names")
    ap.add_argument("--backup", type=Path, help="private live service backup")
    ap.add_argument("--update-root", type=Path, help="fwtool firmware.tar_unpacked directory")
    ap.add_argument("--constructors", action="store_true")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()

    e = AppElf(a.appfw)
    pattern = re.compile(a.grep) if a.grep else None
    live = load_backup(a.backup)[0] if a.backup else None
    profiles = []
    if a.update_root:
        for p in profile_paths(a.update_root):
            profiles.append((p.parent.name + "/" + p.stem, load_backup(p)[0]))

    rows = []
    for name, ident, record in bkid_names(e, pattern):
        pid = APP_SUBSYSTEM | ident
        row = {"name": name, "internal_id": "0x%04x" % ident, "property_id": "0x%08x" % pid, "name_record": "0x%x" % record}
        if a.constructors:
            row["constructors"] = ["0x%x" % x for x in e.movz_movk(pid)]
        if live is not None:
            p = live.get(pid)
            row["live"] = None if p is None else {"hex": p.data.hex(), "size": len(p.data), "attr": "0x%02x" % p.attr}
        if profiles:
            values = {}
            for label, bank in profiles:
                p = bank.get(pid)
                values.setdefault(p.data.hex() if p else None, []).append(label)
            row["profiles"] = {str(k): len(v) if len(values) == 1 else v for k, v in values.items()}
        rows.append(row)
        extra = ""
        if "live" in row:
            extra += " live=%s" % (row["live"] and "%s(sz%d,attr%s)" % (row["live"]["hex"][:32], row["live"]["size"], row["live"]["attr"]))
        if "profiles" in row:
            extra += " profiles=%s" % ("uniform" if len(row["profiles"]) == 1 else "VARIES:" + ",".join(k[:16] for k in row["profiles"]))
        if "constructors" in row:
            extra += " ctor=%s" % ",".join(row["constructors"])
        print("%s %-70s%s" % (row["property_id"], name, extra))
    if a.json:
        a.json.write_text(json.dumps(rows, indent=1) + "\n")


if __name__ == "__main__":
    main()
