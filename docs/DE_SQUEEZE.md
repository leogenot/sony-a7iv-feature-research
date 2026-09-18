# Anamorphic De-Squeeze Display

## Status

**Strong A7 IV candidate. The backup-to-display code path is confirmed, but
nothing has been tested on a camera.**

The retail A7 IV has no **De-Squeeze Display** menu. Sony's A7 IV menu
inventory lists none; FX3 and other Cinema Line bodies expose 1.3x and 2.0x.
The A7 IV 6.02 application nevertheless has:

- a persisted setting, `BKID_APP_SETTING_DE_SQUEEZE_DISP`
- a model extern that republishes the setting
- a model sequence that sends the de-squeeze scale to both the imaging and
  display (`BB`) blocks

None of these steps checks the product class. The only generated availability
conditions are shooting mode (Movie) and movie-recording state. Unlike Log
Shooting, the de-squeeze rules contain no `TYPE_CAMERA_PARAMETERS_*` or
`TYPE_MENU_ITEM_*` term.

This makes De-Squeeze the only candidate found so far where one documented
backup byte plausibly drives a **display-only** feature. It does not change
the encoder or the recorded file.

## Properties

| Property | Name | Size | Attr | Default (all 32 profiles and live backup) |
| --- | --- | ---: | ---: | --- |
| `0x02cf1bf2` | `BKID_APP_SETTING_DE_SQUEEZE_DISP` | 1 | `0x40` | `00` |
| `0x02cf161c` | `BKID_APP_EXTERN_DE_SQUEEZE_DISP` | 1 | `0x40` | `00` |
| `0x02cf1bf5` | `BKID_APP_EXTERN_DE_SQUEEZE_LCD_MONITOR` | 4 | `0x40` | `01000000` |

Attribute `0x40` has neither the read-only (`0x01`) nor the protected (`0x02`)
bit set.

### Enum

Generated names, in enum order:

| Value | `VAL_setting_de_squeeze_disp_*` | Extern value |
| ---: | --- | --- |
| `00` | `DE_SQUEEZE_DISP_OFF_1_0X` | `EXTERN_VAL_DE_SQUEEZE_DISP_OFF_1_0X` |
| `01` | `DE_SQUEEZE_DISP_1_3X` | `EXTERN_VAL_DE_SQUEEZE_DISP_1_3X` |
| `02` | `DE_SQUEEZE_DISP_2_0X` | `EXTERN_VAL_DE_SQUEEZE_DISP_2_0X` |

The executable extern mapper accepts exactly 0, 1 and 2 and asserts on any
other value (see below). That independently confirms the value range. The
order of 1.3x and 2.0x rests on the generated name order, which has been
reliable for every complete enum checked in this build. English resource text
for both ratios is present: "Set when an anamorphic lens with 2.0x Squeeze is
attached" and the 1.3x equivalent.

`EXTERN_DE_SQUEEZE_LCD_MONITOR` has the generated values `..._OFF` and
`..._ON`. The shipped value `1` therefore most likely means the LCD de-squeeze
output is allowed. This property is not proposed for any change.

## Executable path

```text
Application_System_Init
  0x2fd53d0  mov/movk w0, #0x02cf1bf2 ; property exists?
  0x2fd53e8  bind to model storage getter 0x28facdc
             (model base 0x7fcdd20 + 0x23c08)

model::model_extern::extern_BKID_APP_EXTERN_DE_SQUEEZE_DISP  (0x2e8a3e4)
  0x2e8a410  bl 0x28facdc          ; same storage as the backup binding
  value 0     -> publish model value 0
  value 1, 2  -> publish model value 1 / 2
  otherwise   -> assert 0x364badc (line 0x2ae5)

sequence_set_anamo_desqueeze_scale
  typeinfo 0x59d1458, vtable address point 0x59d1480, GOT slot 0x5a15bc0
  constructor 0x3240bb0 snapshots model state; the de-squeeze setting
  (getter 0x28facdc) is stored at +0x20
  run() 0x350dc80
     -> 0x35a548c  IMAGING request (trace id 0x199, forwards to 0x35e7dd0)
                   fields +0x1c, +0x14, +0x20, +0x24
     -> 0x359ce9c  BB display request
                   fields +0x14, +0x18, +0x20, +0x28, +0x24, +0x34
     on failure: log "Failure PID_SET_ANAMO_DESQUEEZE_SCALE" only (no assert)
```

Constructor `0x3240bb0` is called from six generic sequence-dispatch sites:
`0x326ea80`, `0x32b3cc4`, `0x335c30c`, `0x335c3d4`, `0x33bd40c` and
`0x34109ac`. None is preceded by a product-model or `menu_item` test. The
request wrappers only emit trace records and forward their arguments.

Other symbols on this path:

```text
EVENT_REMOTE_DE_SQUEEZE_RATIO         remote/PC event
de_squeeze_disp_hdmi_onoff            HDMI on/off companion state
user_menu_de_squeeze, user_menu_anamo_de_squeeze   My Menu identifiers
PRM_HAITA_setting_de_squeeze_disp_general_shooting_mode
PRM_HAITA_setting_de_squeeze_disp_general_shooting_mode_movie_recording_state
```

The generated HAITA values allow 1.3x and 2.0x in
`GENERAL_SHOOTING_MODE_MOVIE`, in both standby and recording.

## What is not established

- **Lower-layer support.** The A7 IV imaging/BB firmware must accept the
  scale. The IPC path exists and failure is non-fatal, but the A7 IV has never
  been observed de-squeezing.
- **Boot-time refresh.** The sequence is dispatched on generic events. It is
  not yet shown that a cold boot into Movie mode runs it with the stored value.
  A mode change after boot is the most likely trigger.
- **Menu.** The `LS` menu catalogue appears to omit the page, so the value can
  be changed only through the backup property. There will be no in-camera
  control to turn it off. Rollback must use the same service-mode procedure.

## Controlled experiment

Only this one property is changed. Complete it and roll it back before any
other test.

1. Save a fresh backup ([Service mode](SERVICE_MODE.md#save-a-backup-first)).
2. In `serviceshell`, read the current values:

   ```text
   bk r 0x02cf1bf2
   bk r 0x02cf161c
   bk r 0x02cf1bf5
   ```

   Expected: `00`, `00`, `01 00 00 00`. Stop if any value differs.
3. Set 2.0x, the most visually obvious ratio:

   ```text
   bk w 0x02cf1bf2 02
   bk r 0x02cf1bf2
   bk s
   exit
   ```

4. Power off, disconnect USB, remove the battery for ten seconds, and boot in
   **Movie** mode with an ordinary (non-anamorphic) lens.
5. Record:
   - whether the live view is squeezed or stretched horizontally, and by how
     much (a circle should look horizontally stretched about 2x, or appear
     letterboxed)
   - the result after switching Still → Movie once with the mode lever
   - whether a test clip plays back normally and has the expected 3840x2160
     dimensions for the selected format on a computer (it should: the feature is display-only)
   - whether an HDMI monitor, if available, changes
6. Re-enter service mode and read `0x02cf1bf2` and `0x02cf161c`. The extern
   value tells you whether the model republished the setting.

### Interpreting the result

| Observation | Meaning |
| --- | --- |
| `0x02cf1bf2` reads `00` after boot | The value was normalised at startup; there is a product-level validation step |
| Setting retained, extern `02`, display unchanged | The model accepts it; the display or IPC layer ignores or rejects it |
| Setting retained, display de-squeezed | Reachable A7 IV feature via backup property |

### Rollback

```text
bk w 0x02cf1bf2 00
bk s
exit
```

Cold-boot again and confirm that the live view is normal. If `0x02cf161c` did
not return to `00` after this reboot, report it before writing to it: it is a
derived extern value, and it should follow the setting.

## Reproduction

```bash
A7=~/Documents/fwtool.py/unpacked/firmware.tar_unpacked/0700_part_image/dev/nflasha15_unpacked/lib/appFw.so
python3 scripts/bkid_inventory.py "$A7" --grep SQUEEZE --constructors
objdump -d --start-address=0x2e8a3e4 --stop-address=0x2e8a4e4 "$A7"
objdump -d --start-address=0x3240bb0 --stop-address=0x3240c5c "$A7"
objdump -d --start-address=0x350dc80 --stop-address=0x350dd60 "$A7"
strings -a -t x "$A7" | rg -i 'squeeze'
```
