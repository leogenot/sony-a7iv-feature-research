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

The camera serial number and backup hash are deliberately omitted.

