# Enable shutter angle

## Verified properties

| Property | Size | Meaning |
| --- | ---: | --- |
| `0x02cf1702` | 1 byte | `00` = shutter speed, `01` = shutter angle |
| `0x02cf1704` | 1 byte | Selected shutter-angle enum; default `10` = 180° |

Both are writable/resettable settings in the A7 IV 6.02 backup. The mapping is
confirmed by named firmware records and two executable registration passes.

## Activation

Enter PMCA `serviceshell` and read first:

```text
bk r 0x02cf1702
bk r 0x02cf1704
```

The verified defaults are:

```text
00
10
```

Enable angle mode:

```text
bk w 0x02cf1702 01
bk s
exit
```

Cold-boot the camera: power off, disconnect USB, remove the battery for ten
seconds, then restart in Movie mode.

## Verified result

On an ILCE-7M4 running 6.02, the shutter-angle icon appeared in Movie mode
after this procedure. The FX3-style **Shutter Mode** menu remained hidden.
That menu only chooses Speed versus Angle; the backup property performs the
same selection.

To adjust the angle with the camera controls:

1. Use Movie mode.
2. Select Manual Exposure or Shutter Priority.
3. With Flexible Exposure Mode, switch shutter/Tv control to Manual.
4. Turn the dial assigned to shutter speed.

## Direct angle values

Writing the angle property is a fallback when testing dial behavior. Values
are one-byte hexadecimal strings:

| Data | Angle | Data | Angle | Data | Angle |
| --- | ---: | --- | ---: | --- | ---: |
| `0A` | 360° | `11` | 172.8° | `18` | 45° |
| `0B` | 300° | `12` | 150° | `19` | 30° |
| `0C` | 270° | `13` | 144° | `1A` | 22.5° |
| `0D` | 240° | `14` | 120° | `1B` | 11.25° |
| `0E` | 216° | `15` | 90° | `1C` | 5.6° |
| `0F` | 210° | `16` | 86.4° |  |  |
| `10` | 180° | `17` | 72° |  |  |

Example: set 90° and cold-boot:

```text
bk w 0x02cf1704 15
bk s
exit
```

Restore 180°:

```text
bk w 0x02cf1704 10
bk s
exit
```

The enum also contains frame-period values `00` through `09` (`64F`, `32F`,
`16F`, `8F`, `7F`, `6F`, `5F`, `4F`, `3F`, `2F`). These have not been tested
on the A7 IV.

## Rollback to shutter speed

```text
bk w 0x02cf1702 00
bk s
exit
```

Perform the same cold reboot.

