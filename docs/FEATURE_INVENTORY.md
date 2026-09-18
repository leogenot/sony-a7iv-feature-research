# Hidden and product-gated feature inventory (A7 IV 6.02)

This inventory ranks implementation evidence in the shared ILCE-7M4 6.02
`appFw.so` against what the retail camera exposes. It uses the product-class
result in [Product class](PRODUCT_CLASS.md): **the A7 IV is
`PRODUCT_MODEL_LS`**.

## Grades

| Grade | Meaning |
| --- | --- |
| **A. Confirmed reachable** | Behaviour observed on a physical A7 IV |
| **B. Strong A7 IV candidate** | Backup property → model → executable consumer traced, and no product gate found on the path |
| **C. Shared implementation, A7 IV route unknown** | Code and storage exist and are not excluded for `LS`, but the menu, recorder or hardware route is unproven |
| **D. Shared code for another product** | A generated rule or feature-manager row names other product classes, and not `LS`, or the feature needs hardware the A7 IV lacks |
| **E. String/resource only** | Names or UI text only |

## How gating works in this build

The following layers were resolved in the executable. They explain why a
retained backup byte can leave a feature invisible.

1. **Product class.** `PRODUCT_MODEL_*` becomes a feature index. Its 43
   registered feature-manager parameters are listed in
   [`evidence/feature-manager-a7iv-602.json`](../evidence/feature-manager-a7iv-602.json).
2. **Per-product menu catalogue.** `PRM_FEATURE_MANAGER_menu_item` is an
   identity table (`LS=0`, `LAX=1`, `ALCIN_UUD=2`, …) with 131 direct call
   sites. This is the likely reason whole pages are absent even when the
   setting code exists.
3. **Generated HAITA rules.** These are availability/inhibit rules. A few name
   product classes directly (`TYPE_CAMERA_PARAMETERS_*`, `TYPE_MENU_ITEM_*` or
   `TYPE_<class>`). All of them are listed below.
4. **Backup properties.** The backup layout is shared. All 7,296 resolved
   `BKID_APP_*` properties exist in the live A7 IV backup, including storage
   for features the A7 IV cannot use. A property's existence is therefore not
   evidence of support.
5. **Region profiles.** Across all 32 A7 IV profiles, only
   `BKID_APP_CURRENT_AREA`, `SETTING_LANGUAGE`, `SETTING_DATE_FORMAT` and
   `SETTING_VOLUME_SETTINGS` differ. No regional or service-only feature
   switch exists among the app settings.

### Every HAITA rule that names a product class

| Rule stem | Products named | `LS`? |
| --- | --- | --- |
| `FEATURE_MANAGER_model_diff_setting_log_shooting` (Off / Flexible ISO in Movie) | `ALCIN_UUD`, `ATOM`, `DOC`, `DZ`, `HC`, `LAX`, `MT`, `NE`, `OT_UUD`, `PP`, `RS`, `SA`, `SL`, `SP` | **no** |
| `…model_diff_setting_log_shooting_setting_picture_profile` | the same 14 classes | **no** |
| `…model_diff_setting_still_log_shooting` | `DOC` | no |
| `FEATURE_MANAGER_menu_item_setting_base_sensitivity_general_shooting_mode` | `LAX`, `ALCIN_UUD`, `DOC` | no |
| `setting_raw_output_connect_with_raw_compatible_device_exposure_mode` | `LAX`, `ALCIN_UUD`, `GL`, `OS` | no |
| `…model_diff_cinematic_mode_look_…` | `NE` | no |
| `setting_ntsc_pal_selector_camera_parameters` | `MT` | no |
| `raw_output_framerate_restriction`, `(network_)streaming_framerate_restriction` | `DOC` | no |
| `FEATURE_MANAGER_menu_item_ccpf_is_registerd` | `MT` | no |

No generated rule names `LS` positively.

## Ranked findings

### 1. Anamorphic De-Squeeze Display: grade B

- **Evidence:** `0x02cf1bf2` `BKID_APP_SETTING_DE_SQUEEZE_DISP` is registered
  at `0x2fd53d0`. Extern mapper `0x2e8a3e4` accepts 0/1/2.
  `sequence_set_anamo_desqueeze_scale` (constructor `0x3240bb0`, `run()`
  `0x350dc80`) sends the setting to IMAGING and BB. HAITA depends only on
  Movie mode and recording state.
- **A7 IV reachability:** no menu; the software path is not product-gated.
- **Missing:** confirmation that the A7 IV display/imaging layers honour it.
- **Confidence:** high for the path, medium for the visible effect.
- **Experiment:** justified. One byte, display-only, full procedure and
  rollback in [De-Squeeze](DE_SQUEEZE.md).

### 2. Shutter angle: grade A (display), with adjustment blocked

- **Evidence and procedure:** [Shutter angle](SHUTTER_ANGLE.md) and
  [Shutter menu gate](SHUTTER_MENU_GATE.md).
- **Product result:** no HAITA rule names a product for `setting_mode_shutter`.
  The missing page fits the per-product `menu_item` catalogue. The dial
  remains blocked by the generated guard `0x293d634`.
- **Missing:** input binding and menu node for `LS`.
- **Confidence:** high.
- **Experiment:** already performed. Rollback: `bk w 0x02cf1702 00`.

### 3. XAVC S-I DCI 4K (4096x2160 All-Intra): grade C

- **Evidence:** file-format enum `FILE_FOMRAT_XAVC_SI_DCI_4K`. Per-slot
  frame-rate and record-setting properties `0x02cf1a3e`–`0x02cf1a6b`, plus
  `0x02cf1623` `BKID_APP_EXTERN_DCI_4K_REC_FRAME_RATE`. UI strings "XAVC S-I
  DCI 4K" and "DCI 4K / 24.00p". The HAITA rules allow it for
  `TYPE_SYSTEM_ARCHITECTURE_IPSX`, which the A7 IV is (`system_architecture`
  is `IPSX` for `LS`). There is no product-class exclusion rule.
- **A7 IV reachability:** absent from Sony's A7 IV movie tables and menu.
  The gate is most likely the `LS` menu catalogue.
- **Missing:** proof that the A7 IV imager readout and encoder support a
  4096-wide recording. Selection is stored in the per-slot
  `BKID_APP_MR_SETTING_FILE_FORMAT` (`0x02cf019c`, 10 bytes). Its numeric
  enum is not safely decoded, because the generated label array may skip
  values.
- **Confidence:** medium that the code is generic, low for recording support.
- **Experiment:** not justified. It would change the recorder configuration,
  and the enum and encoder path are unverified.

### 4. Log Shooting, Flexible ISO, Cine EI and User LUT: grade D (explicitly not `LS`)

- **Evidence:** full LUT/CUBE/User1–16 implementation ([LUT](LUT.md)).
  `PRM_HAITA_FEATURE_MANAGER_model_diff_setting_log_shooting` lists 14
  product classes and omits `LS`. Related storage: `0x02cf144a`
  `BKID_APP_MR_SETTING_BASE_ISO`, `0x02cf158a` `SETTING_EXPOSURE_INDEX`,
  and `0x02cf144c`–`0x02cf1452` exposure-index values.
- **A7 IV reachability:** `0x02cf1443=01` was retained across reboot with no
  visible feature. The generated model-difference rule has no Flexible-ISO
  combination for the A7 IV's class, which explains this.
- **Missing:** a positive `LS` availability rule and the `LS` menu nodes.
- **Confidence:** high.
- **Experiment:** none. Rollback for the earlier test: `bk w 0x02cf1443 00`.

### 5. Base ISO Low/High switch (dual base ISO): grade D

- **Evidence:** `FEATURE_MANAGER_menu_item_setting_base_sensitivity_general_shooting_mode`
  permits Low/High in Movie only for `LAX`, `ALCIN_UUD` and `DOC`. Storage:
  `0x02cf158d` `BKID_APP_MR_SETTING_BASE_SENSITIVITY` and `0x02cf153a`
  `SETTING_BASE_ISO_HIGH`.
- **Missing:** a sensor with switchable conversion gain characterised for
  this mode, and the `LS` menu. Sensor-dependent.
- **Experiment:** not justified.

### 6. RAW output to an external recorder: grade D

- **Evidence:** the `raw_output_connect_with_raw_compatible_device` rule names
  only `LAX`, `ALCIN_UUD`, `GL` and `OS`. `0x02cf0440`
  `BKID_APP_SETTING_RAW_OUTPUT_FRAME_RATE` is only storage.
- **Missing:** the product route, and HDMI RAW readout on this hardware.
- **Experiment:** not justified.

### 7. Open Gate 5K 3:2 and X-OCN: grade D

See [Open Gate](OPEN_GATE.md). These are shared scan-mode and X-OCN names
with no A7 IV encoder profile, and the A7 IV is not the `LAX` class.

### 8. Auto framing and e-framing: grade C/D

- **Evidence:** `0x02cf15f8`–`0x02cf1602`
  `BKID_APP_MR_SETTING_FIXED_CAMERA_FRAMING_SETTINGS_*` and `0x02cf1d0d`/`1d0f`
  `EFRAMING_*`; strings "Auto Framing", "Auto Framing Settings". In the FX3
  7.02 build, `eframing_support_type` is `MANUAL_ONLY` for `LAX`/`ALCIN_UUD`
  and `NOT_SUPPORT` for `LS`. The A7 IV 6.02 build has no
  `eframing_support_type` parameter at all.
- **Experiment:** not justified.

### 9. Built-in variable ND filter: grade D

The `ND_FILTER` properties (`0x02cf02de`, `0x02cf1151`/`1153`,
`0x02cf1721`, `0x02cf1739`) are shared storage. The feature needs the
electronic ND hardware that only some Cinema Line bodies have.

### 10. Cinematic mode look, and the NTSC/PAL selector restriction: grade D

These rules name only `NE` and `MT`. They are not A7 IV features.

## Already retail on the A7 IV (not hidden)

Time code/user bit, Gamma Display Assist and Breathing Compensation
(`0x02cf0232` `BKID_APP_MR_SETTING_LENS_COMP_BREATHING`) are documented A7 IV
features. They were checked and excluded from the hidden-feature list.
`c2pa_movie` and `digital_signature_still_movie` are `SUPPORT` for `LS`. On the
A7 IV they are licence-dependent retail features, not hidden ones.

## Open leads

- `timelapse_movie_4k` is `SUPPORT` for every product class, and time-lapse
  (`TL_`) record settings exist, including DCI 4K. Whether the A7 IV has a
  reachable in-camera time-lapse movie mode has not been traced.
- The `menu_item` consumers (131 call sites of `0x183ee0c`) should be
  classified to find the exact catalogue nodes that omit Shutter Mode,
  De-Squeeze and DCI 4K for `LS`.

## Reproduction

```bash
A7=~/Documents/fwtool.py/unpacked/firmware.tar_unpacked/0700_part_image/dev/nflasha15_unpacked/lib/appFw.so
UPD=~/Documents/fwtool.py/unpacked/firmware.tar_unpacked
BK=~/Documents/Sony-PMCA-RE/a7iv-backup-602.bin

python3 scripts/feature_manager_matrix.py "$A7" --diff-only
python3 scripts/bkid_inventory.py "$A7" --backup "$BK" --update-root "$UPD" \
  --grep 'SQUEEZE|DCI|LOG_SHOOTING|BASE_ISO|BASE_SENSITIVITY|RAW_OUTPUT|FRAMING|ND_FILTER'
strings -a "$A7" | rg '^VAL_HAITA_.*TYPE_(CAMERA_PARAMETERS_|MENU_ITEM_)?(LS|LAX|ALCIN_UUD)'
```

The inventory run takes about 30 seconds. Its output contains live backup
values. Keep saved outputs outside the repository.
