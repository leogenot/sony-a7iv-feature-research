# A7 IV product class: `PRODUCT_MODEL_LS`

## Conclusion

The ILCE-7M4 runs the shared 6.02 application as **`PRODUCT_MODEL_LS`**, not
`PRODUCT_MODEL_LAX`. `LAX` and `ALCIN_UUD` are both Cinema Line classes.
Several earlier notes in this repository assumed that the A7 IV was `LAX`. They
also read feature-manager tables at the wrong indices. Those statements are
corrected below and in the affected documents.

Every product-gate conclusion in this repository now uses the `LS` column.

## How the product model selects features

`feature_manager::update_product_model()` (`0x183ecc0`) reads the product
model enum and stores an internal *feature index* in `.bss` at `0x5a59788`.
Each `PRM_FEATURE_MANAGER_*` parameter has a getter shaped like this:

```asm
adrp  x0, 0x5a59000
ldrsw x1, [x0, #0x788]      ; feature index
adrp  x0, TABLE
add   x0, x0, #TABLE_LO
ldr   w0, [x0, x1, lsl #2]  ; per-product value
ret
```

A relocated array at `0x59be378` registers `(parameter id, getter)` pairs.
The parameter id indexes the `PRM_*` name-pointer array at `0x575dfe0`, which
gives each getter its generated name. Enum labels come from the generated
`VAL_FEATURE_MANAGER_*` string-pointer array at `0x575de40`–`0x5797f48`.

`scripts/feature_manager_matrix.py` derives all of these structures from the
binary, without hard-coded addresses, and prints the per-product matrix. The
A7 IV 6.02 output is saved in
[`evidence/feature-manager-a7iv-602.json`](../evidence/feature-manager-a7iv-602.json).

### Product enum and feature index

| Name record | Enum | Feature index |
| --- | ---: | ---: |
| `PRODUCT_MODEL_LS` | 0 | 26 |
| `PRODUCT_MODEL_YT` | 1 | 22 |
| `PRODUCT_MODEL_GL` | 2 | 23 |
| `PRODUCT_MODEL_LAX` | 3 | 25 |
| `PRODUCT_MODEL_ALCIN_UUD` | 4 | 24 |

The enum values come from the generated name records at `0x57c9528`
(`u32 id, u32 length, ptr name`). The feature index comes from the byte jump
table at `0x37b7910`. The 6.02 build defines 27 product classes.

## Evidence that the A7 IV is `LS`

The rows below that describe hardware select the A7 IV only in the `LS` column.

| Feature-manager parameter | `LS` | `LAX` | `ALCIN_UUD` |
| --- | --- | --- | --- |
| `imager_model` | `IMX710` | `IMX684` | `IMX510` |
| `product_concept` | `OTHER` | `CINEMA_LINE` | `CINEMA_LINE` |
| `mecha_shutter` | available | **not available** | available |
| `fastest_shutter_speed_of_mecha_shutter` | 1/8000 | none | 1/8000 |
| `shutter_curtain` | available | not available | not available |
| `shoot_mode_switch` | mode dial + mode lever | MODE button + dial guide | MODE button + dial guide |
| `support_cfexpress` | slot 1 only | slots 1 and 2 | slots 1 and 2 |
| `c2pa_movie` | supported | not supported | not supported |
| `digital_signature_still_movie` | supported | not supported | not supported |
| `menu_item` | `TYPE_MENU_ITEM_LS` | `TYPE_MENU_ITEM_LAX` | `TYPE_MENU_ITEM_ALCIN_UUD` |

The A7 IV has a 1/8000 mechanical shutter, a mode dial with a separate
Still/Movie/S&Q lever, and CFexpress Type A in slot 1 only. It is not a Cinema
Line camera. Only `LS` matches all of these facts. The update package points
the same way. Its 32 backup profiles are stored under `SYSIPSX-DSLR/LS` and
`SYSIPSX-DSLR/LS_GLEE`. The live service backup identifies itself as
`CH89101_CEC`, a profile in the `LS` directory.

`ALCIN_UUD` uses `IMX510`, the FX3/A7S III sensor, and is a Cinema Line
class. In the FX3 7.02 build, which defines only nine product classes, the
same `LAX` and `ALCIN_UUD` classes are also the Cinema Line/e-framing
classes. `ALCIN_UUD` is therefore the FX3 class. The retail identity of `LAX`
(Cinema Line, IMX684, no mechanical shutter) is not needed for this work and
has not been established.

`LS_GLEE` differs from `LS` only in its default volume value (`07` instead of
`08`) among all 7,296 resolved `BKID_APP_*` properties when profiles for the
same region are compared. It looks like a
hardware sub-variant rather than a feature tier.

## Per-product menu catalogue

`PRM_FEATURE_MANAGER_menu_item` (parameter id 119, getter `0x183ee0c`,
table `0x37b7be8`) is an identity table. Each product class selects its own
menu catalogue: `LS=0`, `LAX=1`, `ALCIN_UUD=2`, and so on. The getter has 131
direct call sites. This is the product mechanism that can omit whole pages
such as Shutter Mode, Log Shooting, De-Squeeze Display or DCI 4K from the
A7 IV while keeping the shared implementation in the binary.

Generated HAITA rules also name `TYPE_MENU_ITEM_*` directly. None of these
rules includes `LS`:

| Rule | Products named |
| --- | --- |
| `menu_item_setting_base_sensitivity_general_shooting_mode` (Base ISO Low/High in Movie) | `LAX`, `ALCIN_UUD`, `DOC` |
| `setting_raw_output_connect_with_raw_compatible_device_exposure_mode` | `LAX`, `ALCIN_UUD`, `GL`, `OS` |
| `menu_item_ccpf_is_registerd` | `MT` |

## Corrections to earlier notes

1. **A7 IV is not `LAX`.** [Open Gate](OPEN_GATE.md) and
   [Shutter menu gate](SHUTTER_MENU_GATE.md) previously called the A7 IV
   `PRODUCT_MODEL_LAX`. The correct class is `LS`. [LUT](LUT.md) had already
   withdrawn the `LAX` label; this document supplies the executable proof.
2. **Wrong enum values and indices.** The shutter note gave `LAX=4 → index 24`
   and `ALCIN_UUD=5 → index 21`. The generated records give `LAX=3 → 25` and
   `ALCIN_UUD=4 → 24`.
3. **Wrong getter.** `0x183f0f4` is `PRM_FEATURE_MANAGER_shooting_mode_dial`
   (id 3), not `menu_item`. The two `1` values previously quoted from
   `0x37b9548` were `shooting_mode_dial` values for `ALCIN_UUD` and `SA`.
4. **`menu_item` is not shared.** `menu_item` differs for every product.
   The earlier conclusion that it could not explain the missing Shutter Mode
   page was based on the wrong table. A per-product menu catalogue is now the
   leading explanation for missing pages. The exact catalogue nodes are still
   unresolved.

## Reproduction

```bash
A7=~/Documents/fwtool.py/unpacked/firmware.tar_unpacked/0700_part_image/dev/nflasha15_unpacked/lib/appFw.so
FX3=~/Documents/fwtool.py/comparison/FX3-7.02-unpacked/firmware.tar_unpacked/0700_part_image/dev/nflasha15_unpacked/lib/appFw.so

python3 scripts/feature_manager_matrix.py "$A7" --diff-only
python3 scripts/feature_manager_matrix.py "$FX3" --products LS YT GL LAX ALCIN_UUD SA DZ YS GS
python3 scripts/appfw_elf.py "$A7" names PRODUCT_MODEL_LS PRODUCT_MODEL_LAX PRODUCT_MODEL_ALCIN_UUD
objdump -d --start-address=0x183ecc0 --stop-address=0x183ee24 "$A7"
```

Enum labels are taken by position from the generated `VAL_` arrays. Those
arrays omit unused values. For example, `menu_item` has 27 table values but only
20 labels, because the codename classes `TAKE_BASIC` through `ALCIN2` have no
label. The script therefore prints a label only when the array covers the full
value range, or when the value is below 3, which is before the first gap for
the product-indexed enums.
