# Sony A7 IV firmware and feature research

Use this at your own risk, I am not responsible for any damages.

Reproducible notes and tools for studying Sony ILCE-7M4 firmware 6.02 through
official update files and Sony's USB service mode.

The shutter-angle mode switch has been verified on a physical A7 IV running
6.02. The camera displayed the shutter-angle icon after changing one persisted
setting and cold-booting. The custom-LUT implementation is present in the
firmware, but the A7 IV's product class (`PRODUCT_MODEL_LS`) is excluded from
the Log Shooting availability rule. The retained backup setting therefore
exposed no menu.

This repository intentionally contains no Sony firmware, decrypted binaries,
camera backups, serial numbers, decryption keys, or extracted proprietary
files. Obtain the official update yourself and keep generated data local.

## Research status

| Feature | Status | Finding |
| --- | --- | --- |
| Service mode | Verified | PMCA switches the A7 IV from Mass Storage to service mode and authenticates. |
| Settings backup | Verified | A complete checksum-valid backup can be saved locally before experiments. |
| Decrypted filesystem read | Verified, read-only | Jiritsu `GET_FILE2` accepts a traversal path and returns files from the running camera. 1,064 update-backed files were independently hash-matched. |
| Shutter angle | Display verified; adjustment still gated | `0x02cf1702`: `00` speed, `01` angle. Existing `0x02cf1704=10` displays 180°, but A7 IV 6.02 still routes touch/dial control away from the angle setter. |
| Custom LUT | Implementation verified; runtime gate unresolved | `0x02cf1443=01` is accepted, survives sync and cold boot, but does not expose Flexible ISO. User1–User16 storage, CUBE parsing, selection and display paths exist; a separate runtime/UI condition remains. |
| Open Gate | Generic imager path found; recording path unproven | Shared firmware names a 5016x3344 3:2 scan mode, but no matching encoder profile, live PTP resolution, or verified A7 IV product route has been found. |
| Product class | Resolved offline | The A7 IV runs the shared application as `PRODUCT_MODEL_LS`, not `LAX`. Each product class selects its own menu catalogue. See [Product class](docs/PRODUCT_CLASS.md). |
| Log Shooting / Flexible ISO | Product-excluded | The generated Log Shooting model-difference rule names 14 product classes and omits `LS`. |
| De-Squeeze Display | Strong candidate, untested | `0x02cf1bf2` (`00` Off, `01` 1.3x, `02` 2.0x) reaches the display-scale sequence with no product check. See [De-Squeeze](docs/DE_SQUEEZE.md). |
| XAVC S-I DCI 4K | Shared implementation, route unknown | Not product-excluded by HAITA, but no A7 IV menu or verified encoder path. No experiment proposed. |

## Start here

1. Follow [Python and repository setup](docs/SETUP.md).
2. Save a [read-only settings backup](docs/SERVICE_MODE.md#save-a-backup-first).
3. Review and apply the [shutter-angle procedure](docs/SHUTTER_ANGLE.md).
4. After verifying shutter behavior, perform the isolated
   [LUT experiment](docs/LUT.md).
5. For firmware extraction and static analysis, see
   [Firmware extraction](docs/FIRMWARE_EXTRACTION.md) and
   [Research evidence](docs/RESEARCH_EVIDENCE.md).
6. See [Open Gate research](docs/OPEN_GATE.md) for the full-height 5K 3:2
   scan-mode evidence and its current limitations.
7. See the [ranked feature inventory](docs/FEATURE_INVENTORY.md) and the
   [product-class analysis](docs/PRODUCT_CLASS.md) before proposing any new
   backup-property experiment.

## Enter service mode

Set the camera's USB connection mode to **Mass Storage**, connect it by USB,
then run:

```bash
cd ~/Documents/Sony-PMCA-RE
sudo ./venv/bin/python ./pmca-console.py serviceshell
```

PMCA switches the camera into service mode and authenticates. If the first
attempt times out while the USB device is changing modes, run the same command
again after the camera reconnects.

## Quick shutter-angle commands

Inside PMCA `serviceshell`:

```text
bk r 0x02cf1702
bk r 0x02cf1704
bk w 0x02cf1702 01
bk s
exit
```

Power off, disconnect USB, remove the battery for ten seconds, and reboot in
Movie mode. Restore shutter-speed mode with:

```text
bk w 0x02cf1702 00
bk s
exit
```

## Upstream projects

- [ma1co/Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE): USB service-mode transport and backup shell.
- [DavidBuchanan314/fwtool.py, `a7iv` branch](https://github.com/DavidBuchanan314/fwtool.py/tree/a7iv): A7 IV update decryption and unpacking.
- [ma1co/fwtool.py PR #52](https://github.com/ma1co/fwtool.py/pull/52): upstream A7 IV extraction work.
- [DavidBuchanan314/ILCE-7M4-RE](https://github.com/DavidBuchanan314/ILCE-7M4-RE): A7 IV boot, UART and platform research.

## Repository layout

```text
docs/       Setup, extraction, service-mode and feature procedures
scripts/    Read-only backup/dump and offline property-analysis tools
            (appfw_elf.py, bk4.py, bkid_inventory.py, feature_manager_matrix.py)
evidence/   Sanitized property mappings and verification record
```

All camera changes documented here operate on persisted backup properties,
not a repacked firmware update. Test one property at a time and keep the
original backup and hashes outside this repository.
