# Property-mapping evidence

## Executable mapping method

`appFw.so` contains records shaped as:

```c
uint32_t id;
uint32_t nul_inclusive_name_length;
const char *name;
```

The pointer is represented by an `R_AARCH64_RELATIVE` relocation. For the
settings below, `Application_System_Init` constructs a service property as
`0x02cf0000 | id`, checks that it exists and registers its model accessor.

| Name | Internal ID | Physical property | Constructor VA |
| --- | ---: | ---: | ---: |
| `BKID_APP_SETTING_MODE_SHUTTER` | `0x1702` | `0x02cf1702` | `0x2fceda0` |
| `BKID_APP_SETTING_SHUTTER_ANGLE` | `0x1704` | `0x02cf1704` | `0x2fcee50` |
| `BKID_APP_SETTING_LOG_SHOOTING` | `0x1443` | `0x02cf1443` | `0x2fcb5f0` |
| `BKID_APP_SETTING_EMBED_LUT_FILE` | `0x1447` | `0x02cf1447` | `0x2fcb6a0` |
| `BKID_APP_SETTING_SELECT_LUT` | `0x1453` | `0x02cf1453` | `0x2fcfe78` |
| `BKID_APP_SETTING_APPLY_LUT` | `0x1456` | `0x02cf1456` | `0x2fd5378` |
| `BKID_APP_SETTING_STILL_LOG_SHOOTING` | `0x1c9b` | `0x02cf1c9b` | `0x2fcb6f8` |

Example AArch64 sequence:

```text
0x2fceda0  mov  w0, #0x1702
0x2fceda4  movk w0, #0x2cf, lsl #16
0x2fceda8  bl   property_exists_or_register
```

This is stronger than matching numerical IDs from unrelated tables. Earlier
candidate mappings based on such numeric collisions were withdrawn and are not
included here.

## Sanitized live values

| Property | Bytes | Size | Attribute |
| --- | --- | ---: | ---: |
| `0x02cf1702` | `00`, then verified working as `01` | 1 | `0x60` |
| `0x02cf1704` | `10` | 1 | `0x60` |
| `0x02cf1443` | `00` | 1 | `0x60` |
| `0x02cf1447` | `01` | 1 | `0x60` |
| `0x02cf1453` | `01` | 1 | `0x60` |
| `0x02cf1456` | `01` | 1 | `0x40` |
| `0x02cf1c9b` | `00` | 1 | `0x60` |

In Sony-PMCA-RE's backup parser, neither `0x60` nor `0x40` has the read-only
bit (`0x01`) or protected bit (`0x02`) set.

## Live verification record

Environment:

```text
Camera:   ILCE-7M4
Firmware: 6.02
Region:   CEC backup profile family
```

Result:

```text
0x02cf1702: 00 -> 01
Cold reboot performed
Shutter-angle icon visible in Movie mode
FX3-style Shutter Mode menu remains hidden
```

The first Custom LUT activation test produced:

```text
0x02cf1443 initial:       00
0x02cf1443 immediate:     01
0x02cf1443 after bk s:    01
0x02cf1443 after reboot:  01
Flexible ISO menu:        absent
```

This rules out backup-write rejection and boot-time normalization. A separate
runtime or menu-support condition blocks the visible feature.

Static analysis also explains why a retained backup byte may be insufficient.
The application's `model::model_api::detail::set_log_shooting()` path (around
VA `0x270b990`) first updates the Log Shooting model property, then branches on
all four Log Shooting values and dispatches additional model/sequence changes.
Writing `0x02cf1443` through `bk w` changes the persisted property directly and
does not execute that coordinated setter path. The remaining work is therefore
to identify the narrow dependent state or a callable event that invokes the
official setter; changing the global product-model value is not an equivalent
substitute.

The same binary contains `to_remote_event_select_log_shooting`, indicating a
PTP/remote-event route into the model layer. `scripts/a7iv_ptp_log_probe.py`
performs Sony's read-only PC Remote handshake and checks whether the camera
advertises the Log Shooting Mode property `0xE0E3`; it intentionally contains
no setter operation. An initial test in file-transfer MTP mode reached the
camera but stalled on standard PTP `GetDevicePropDesc` (`0x1014`). Sony remote
control instead requires PC Remote mode and the vendor operations `0x9201`,
`0x9202`, and `0x9203`.

## Log Shooting model-family evidence

The A7 IV 6.02 update stores its matching backup profiles under
`SYSIPSX-DSLR/LS`, including `CH89101_CEC.bin`; the live backup family is also
`CH89101_CEC`. The application's feature manager maps `PRODUCT_MODEL_LS` to
`TYPE_CAMERA_PARAMETERS_LS`.

Generated `PRM_HAITA_FEATURE_MANAGER_model_diff_setting_log_shooting` values
contain model-specific Off/Flexible-ISO combinations for `TYPE_LAX`,
`TYPE_ALCIN_UUD`, and multiple other families, but none for `TYPE_LS`. This
withdraws the earlier LAX classification and means those LAX values cannot be
used as positive evidence for A7 IV support.

The camera serial number and backup hash are deliberately omitted.
