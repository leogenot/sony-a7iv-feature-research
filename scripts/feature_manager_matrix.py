#!/usr/bin/env python3
"""Decode the appFw.so feature-manager product matrix offline.

For every generated PRM_FEATURE_MANAGER_* parameter this prints the value the
firmware selects for each PRODUCT_MODEL_* class, with enum labels recovered
from the generated VAL_FEATURE_MANAGER_* string arrays.

The decoder locates, without hard-coded addresses:
  1. PRODUCT_MODEL_* name records (u32 id, u32 len, ptr name)
  2. feature_manager::update_product_model() via its diagnostic string, and
     its jump table from product enum to internal feature index
  3. table getters of the form
        adrp x0, STATE ; ldrsw x1, [x0, #IDX] ; adrp/add x0, TABLE ;
        ldr w0, [x0, x1, lsl #2] ; ret
  4. the relocated (parameter id, getter) registration array
  5. the PRM_* parameter-name pointer array and VAL_* label arrays

Usage:
    python3 scripts/feature_manager_matrix.py APPFW [--products LS LAX ALCIN_UUD]
        [--json OUT.json] [--diff-only]

It reads the binary only. Nothing is written except the optional JSON.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from appfw_elf import AppElf  # noqa: E402


def adrp_target(word: int, pc: int) -> int:
    imm = ((word >> 29) & 3) | (((word >> 5) & 0x7FFFF) << 2)
    if imm & (1 << 20):
        imm -= 1 << 21
    return (pc & ~0xFFF) + (imm << 12)


def product_models(e: AppElf) -> dict[int, str]:
    result = {}
    first = e.find_cstr("PRODUCT_MODEL_LS")[0]
    rec = e.reloc_addend_to_targets[first][0] - 8
    while True:
        ident, length = e.u32(rec), e.u32(rec + 4)
        name = e.cstr(e.ptr(rec + 8), 80)
        if not name.startswith("PRODUCT_MODEL_") or length != len(name) + 1:
            break
        result[ident] = name[len("PRODUCT_MODEL_") :]
        rec += 16
    return result


def decode_update_product_model(e: AppElf):
    diag = e.find_cstr("void feature_manager::update_product_model()")[0]
    ref = e.adrp_refs(diag)[0]
    base, words = e.text_words
    # The diagnostic sits in the out-of-range branch after the jump-table
    # cases, so walk back to the frame-creating "stp x29, x30, [sp, #-N]!".
    i = (ref - base) // 4
    while words[i] & 0xFFC07FFF != 0xA9807BFD:
        i -= 1
    end = (ref - base) // 4
    count = table = jbase = state_page = state_off = None
    for k in range(i, end):
        w = words[k]
        pc = base + 4 * k
        if w & 0x7F80001F == 0x7100001F and count is None:  # cmp wN, #imm
            count = ((w >> 10) & 0xFFF) + 1
        if w & 0xFFC00000 == 0x38606800 or (w & 0xFFE0FC00) == 0x38604800:  # ldrb w, [x, w, uxtw]
            pass
        if w & 0x9F000000 == 0x10000000 and jbase is None:  # adr
            imm = ((w >> 29) & 3) | (((w >> 5) & 0x7FFFF) << 2)
            if imm & (1 << 20):
                imm -= 1 << 21
            jbase = pc + imm
        if w & 0x9F00001F == 0x90000001 and table is None:  # adrp x1
            nxt = words[k + 2] if (words[k + 1] & 0x9F000000) == 0x90000000 else words[k + 1]
            table = adrp_target(w, pc) + ((nxt >> 10) & 0xFFF)
        if w & 0x9F00001F == 0x90000000 and state_page is None:  # adrp x0 (state)
            state_page = adrp_target(w, pc)
    # the case bodies: first case stores wzr, others "mov w1,#k ; b/str"
    case_value = {}
    for k in range((jbase - base) // 4, (jbase - base) // 4 + 4 * count + 8):
        w = words[k]
        pc = base + 4 * k
        if w & 0xFFC0001F == 0xB900001F and pc == jbase:  # str wzr,[x0,#off]
            state_off = ((w >> 10) & 0xFFF) * 4
            case_value[pc] = 0
        if w & 0xFFE0001F == 0x52800001:  # mov w1,#imm
            case_value[pc] = (w >> 5) & 0xFFFF
    mapping = {}
    for p in range(count):
        b = e.u8(table + p)
        if b > 127:
            b -= 256
        mapping[p] = case_value[jbase + 4 * b]
    return mapping, state_page + state_off


def find_getters(e: AppElf, state: int) -> dict[int, int]:
    base, words = e.text_words
    page, off = state & ~0xFFF, state & 0xFFF
    ldrsw = 0xB9800001 | ((off // 4) << 10)  # ldrsw x1, [x0, #off]
    result = {}
    for k in range(len(words) - 5):
        if words[k + 1] != ldrsw:
            continue
        a, b, c = words[k], words[k + 2], words[k + 3]
        pc = base + 4 * k
        if a & 0x9F00001F != 0x90000000 or adrp_target(a, pc) != page:
            continue
        if b & 0x9F00001F != 0x90000000 or c & 0xFF8003FF != 0x91000000:
            continue
        if words[k + 4] != 0xB8617800 or words[k + 5] != 0xD65F03C0:
            continue
        result[pc] = adrp_target(b, pc + 8) + ((c >> 10) & 0xFFF)
    return result


def registration_pairs(e: AppElf, getters: dict[int, int]) -> dict[int, int]:
    pairs = {}
    for g in getters:
        for slot in e.reloc_addend_to_targets.get(g, []):
            ident = e.u64(slot - 8)
            if ident < 0x10000:
                pairs[ident] = g
    return pairs


def string_pointer_array(e: AppElf, member: str, prefix: str) -> tuple[int, list[str]]:
    slot = e.reloc_addend_to_targets[e.find_cstr(member)[0]][0]
    while True:
        try:
            s = e.cstr(e.ptr(slot - 8), 400)
        except ValueError:
            break
        if not s.startswith(prefix):
            break
        slot -= 8
    start, names = slot, []
    while True:
        try:
            s = e.cstr(e.ptr(slot), 400)
        except ValueError:
            break
        if not re.match(r"^[A-Z]+_", s):
            break
        names.append(s)
        slot += 8
    return start, names


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("appfw", type=Path)
    ap.add_argument("--products", nargs="*", default=["LS", "LAX", "ALCIN_UUD"])
    ap.add_argument("--json", type=Path)
    ap.add_argument("--diff-only", action="store_true", help="only rows where selected products differ")
    a = ap.parse_args()

    e = AppElf(a.appfw)
    products = product_models(e)
    mapping, state = decode_update_product_model(e)
    getters = find_getters(e, state)
    pairs = registration_pairs(e, getters)
    _, prm_names = string_pointer_array(e, "PRM_FEATURE_MANAGER_camera_parameters", "PRM_")
    # The PRM array is indexed from its first PRM_ entry.
    _, val_names = string_pointer_array(e, "VAL_FEATURE_MANAGER_menu_item_TYPE_MENU_ITEM_LS", "VAL_")
    fm = sorted({n[len("PRM_FEATURE_MANAGER_") :] for n in prm_names if n.startswith("PRM_FEATURE_MANAGER_")}, key=len, reverse=True)
    labels: dict[str, list[str]] = {}
    for v in val_names:
        if not v.startswith("VAL_FEATURE_MANAGER_"):
            continue
        rest = v[len("VAL_FEATURE_MANAGER_") :]
        for short in fm:
            if rest.startswith(short + "_"):
                labels.setdefault(short, []).append(rest[len(short) + 1 :])
                break

    wanted = {name: pid for pid, name in products.items() if name in a.products}
    missing = set(a.products) - set(wanted)
    if missing:
        ap.error("unknown product(s): %s; available: %s" % (", ".join(sorted(missing)), ", ".join(products.values())))

    print("binary: %s" % a.appfw)
    print("product state: 0x%x   products: %d   getters: %d   registered: %d" % (state, len(products), len(getters), len(pairs)))
    for name, pid in wanted.items():
        print("  PRODUCT_MODEL_%s = %d -> feature index %d" % (name, pid, mapping[pid]))
    rows = []
    for ident, g in sorted(pairs.items()):
        pname = prm_names[ident] if ident < len(prm_names) else "?"
        short = pname.replace("PRM_FEATURE_MANAGER_", "")
        table = getters[g]
        vals = {}
        for name, pid in wanted.items():
            v = e.u32(table + 4 * mapping[pid])
            lab = labels.get(short, [])
            # Label arrays omit unused values; only trust them when complete.
            complete = len(lab) > max(e.u32(table + 4 * k) for k in range(len(mapping)))
            vals[name] = {"value": v, "label": lab[v] if v < len(lab) and (complete or v < 3) else None}
        differs = len({x["value"] for x in vals.values()}) > 1
        rows.append({"prm_id": ident, "name": pname, "getter": "0x%x" % g, "table": "0x%x" % table, "values": vals, "differs": differs})
        if a.diff_only and not differs:
            continue
        cells = "  ".join("%s=%s" % (n, "%d:%s" % (x["value"], x["label"] or "?")) for n, x in vals.items())
        print("%5d %-48s %s%s" % (ident, short[:48], cells, "  *" if differs else ""))
    if a.json:
        a.json.write_text(json.dumps({"products": products, "feature_index": mapping, "rows": rows}, indent=1) + "\n")


if __name__ == "__main__":
    main()
