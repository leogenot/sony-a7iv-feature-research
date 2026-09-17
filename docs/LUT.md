# Custom LUT research and first activation experiment

## Status

The A7 IV 6.02 firmware contains the full software-side LUT implementation:

- Log Shooting states
- S709, R709 and S-Log3 built-in LUT selection
- User1–User16 slots
- 17/33-point CUBE parsing
- import, edit, delete and reset sequences
- memory-card LUT folder mounting
- LUT display/application paths
- embedded-LUT metadata handling

The software implementation is present, but the first direct activation test
did not expose Flexible ISO on the physical A7 IV. Readback proved that the
camera accepts `0x02cf1443=01`, saves it, and retains it across a cold boot.
Therefore a separate runtime or UI-support condition blocks the feature. Keep
this experiment separate from the shutter-angle change.

## Main properties

| Property | Setting | Values | Verified default |
| --- | --- | --- | --- |
| `0x02cf1443` | Log Shooting | `00` Off, `01` Flexible ISO, `02` Cine EI Quick, `03` Cine EI | `00` |
| `0x02cf1447` | Embed LUT File | `00` On, `01` Off | `01` |
| `0x02cf1453` | Select LUT | `00` S709, `01` R709, `02` S-Log3, `03`–`12` User1–User16 | `01` |
| `0x02cf1456` | Apply/Display LUT | `00` On, `01` Off | `01` |
| `0x02cf1c9b` | Still Log Shooting | `00` Off | `00` |

The User LUT upper bound is hexadecimal `12`, which is decimal 18: the first
three values are built-ins and values 3 through 18 select User1 through User16.

## Product-family correction

The earlier working note identified the A7 IV as product class `LAX`. That was
an unsupported inference and has been withdrawn. The 6.02 update contains the
A7 IV backup profile under `SYSIPSX-DSLR/LS`, and the live CEC backup identifies
itself as `CH89101_CEC`. In `feature_manager::update_product_model()`,
`PRODUCT_MODEL_LS` maps to `TYPE_CAMERA_PARAMETERS_LS`.

The generated model-difference values for Log Shooting include combinations
for `TYPE_LAX`, `TYPE_ALCIN_UUD`, and several other camera families, including:

```text
LOG_SHOOTING_OFF + MOVIE_MODE + TYPE_LAX
LOG_SHOOTING_FLEXIBLE_ISO + MOVIE_MODE + TYPE_LAX
```

There is no corresponding `TYPE_LS` combination. These are generated
HAITA/model-difference values, so their presence alone does not prove that a
mode is enabled; the lack of an LS combination is evidence that the direct LAX
analogy was wrong. No LUT-specific product-model gate was found for Select LUT,
while Apply LUT is conditioned on Log Shooting and Movie mode. The direct
property mapping remains valid, but support on LS-class hardware remains
unproven. There is also no positive A7 IV evidence for Cine EI values `02` or
`03`.

## Readback diagnostic

Physical-camera result on firmware 6.02:

```text
initial read:       00
immediate read:     01
read after bk s:    01
read after reboot:  01
visible menu:       absent
```

This classifies the result as a retained property with a separate runtime/UI
gate. The sequence below is preserved for reproducibility.

Run this sequence in one service-shell session and record every result:

```text
bk r 0x02cf1443
bk w 0x02cf1443 01
bk r 0x02cf1443
bk s
bk r 0x02cf1443
exit
```

Cold-boot the camera with the mode dial set to Movie, re-enter service mode,
and read it once more:

```text
bk r 0x02cf1443
```

Interpretation:

| Observation | Meaning |
| --- | --- |
| Immediate readback is `00` | The write was rejected or immediately normalized. |
| Immediate and post-sync reads are `01`, post-boot read is `00` | Startup/model validation reset the setting. |
| Post-boot read remains `01`, no menu appears | **Observed:** the persisted state was accepted, but a separate runtime or UI support gate hides/disables the feature. |

Do not change the camera product-model value to bypass the gate. Product model
selects many hardware and UI parameter tables at once and is not a narrow LUT
switch.

## Read-only PTP setter-path probe

Firmware 6.02 contains a remote-event conversion path named
`to_remote_event_select_log_shooting`. Sony's PTP remote surface uses device
property `0xE0E3` for Log Shooting Mode. Querying its descriptor is a safer way
to determine whether the A7 IV exposes the official setter path than guessing
more backup-property dependencies.

Exit service mode, set **USB Connection Mode** to **MTP**, reconnect the camera,
and run from this research repository:

```bash
sudo ./../Sony-PMCA-RE/venv/bin/python scripts/a7iv_ptp_log_probe.py
```

The probe requests only `GetDevicePropDesc` and `GetDevicePropValue`. It does
not implement or issue `SetDevicePropValue`. Record the complete output. A
successful writable descriptor with values including `1` would justify a
separate, reviewable experiment through Sony's setter path. An unsupported or
read-only response would confirm that the A7 IV's remote surface also gates the
feature.

## Original isolated experiment

Read and record the current settings:

```text
bk r 0x02cf1443
bk r 0x02cf1447
bk r 0x02cf1453
bk r 0x02cf1456
```

Expected:

```text
00
01
01
01
```

Change only Log Shooting, as used in the first physical-camera test:

```text
bk w 0x02cf1443 01
bk s
exit
```

The first test retained `01` but did not expose Flexible ISO. Inspecting Movie
mode produced no visible Log Shooting setting.

- Log Shooting Setting
- Select LUT
- Display/Apply LUT
- Manage User LUTs
- changes in ISO behavior or picture-profile availability

Record both visible menus and behavior. A hidden menu with changed shooting
behavior is a different result from the property being rejected/reset.

## Import path if the menu appears

The exact A7 IV application string is:

```text
/Private/Sony/PRO/LUT
```

Place a valid 17-point or 33-point `.cube` file there on an SD card, then use
**Manage User LUTs → Import/Edit** if that menu becomes available.

Do not set Select LUT to User1 while all User LUT existence flags are zero.
An existence byte is only metadata; setting it does not create the parsed LUT
payload or file identifier.

## User1–User16 persisted state

| Range | Purpose |
| --- | --- |
| `0x02cf14a4`–`0x02cf14b3` | User1–User16 existence flags |
| `0x02cf14d6`–`0x02cf14e5` | 64-byte LUT file IDs |
| `0x02cf1508`–`0x02cf1517` | Per-slot input gamut |
| `0x02cf1472`–`0x02cf1481` | Per-slot AE-level offset |

On the unmodified backup, all existence flags and file IDs are zero.

## Rollback

```text
bk w 0x02cf1443 00
bk s
exit
```

Cold-boot again. Leave the other LUT properties at their original values until
the Flexible ISO result is understood.
