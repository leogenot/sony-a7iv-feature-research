# Firmware extraction

## Unpack the official update

Place Sony's A7 IV `BODYDATA.DAT` in the local `fwtool.py` directory. With the
`a7iv` branch and dependencies active:

```bash
cd ~/Documents/fwtool.py
source venv/bin/activate
python ./fwtool.py unpack -f ./BODYDATA.DAT -o ./unpacked
```

For the verified 6.02 package, fwtool identifies:

```text
model:   0x01030081
version: 6.02
crypter: CXD90057_k8
```

The main research targets are:

```text
unpacked/firmware.tar_unpacked/0700_part_image/dev/
  nflasha3_unpacked/    /system
  nflasha7_unpacked/    root filesystem
  nflasha8_unpacked/    /cp coprocessor files
  nflasha15_unpacked/   /usr application files
```

The main camera application is:

```text
nflasha15_unpacked/lib/appFw.so
```

The update contains substantial replacement filesystem images. It is not a
full backup of every live partition or device-specific setting.

## Offline property analysis

Run the analyzer against `appFw.so` and a private service backup:

```bash
cd ~/Documents/sony-a7iv-feature-research
python3 ./scripts/analyze_feature_properties.py \
  ~/Documents/fwtool.py/unpacked/firmware.tar_unpacked/0700_part_image/dev/nflasha15_unpacked/lib/appFw.so \
  --backup ~/Documents/Sony-PMCA-RE/a7iv-backup-602.bin \
  --pmca-root ~/Documents/Sony-PMCA-RE
```

The output resolves named `BKID_APP_*` records to service property IDs and
shows the AArch64 constructor addresses that build each complete
`0x02cfXXXX` identifier.

## Product matrix and full property inventory

`feature_manager_matrix.py` decodes the per-product feature-manager tables.
`bkid_inventory.py` resolves every `BKID_APP_*` name record and can join it to
a private backup and the 32 regional profiles:

```bash
A7=~/Documents/fwtool.py/unpacked/firmware.tar_unpacked/0700_part_image/dev/nflasha15_unpacked/lib/appFw.so
python3 ./scripts/feature_manager_matrix.py "$A7" --diff-only
python3 ./scripts/bkid_inventory.py "$A7" --grep SQUEEZE --constructors \
  --backup ~/Documents/Sony-PMCA-RE/a7iv-backup-602.bin \
  --update-root ~/Documents/fwtool.py/unpacked/firmware.tar_unpacked
```

`appfw_elf.py` provides the shared relocation, name-record, immediate and
`ADRP` reference helpers, and a small command-line interface. `bk4.py` is a
dependency-free BK4 reader that verifies checksums and reads both banks.

## Compare against an enabled camera

FX3 7.02 was used as a positive reference because Sony exposes shutter angle
and User1–User16 LUT import on that camera. Its extracted `libSysDef.so`
contains the same `MIRA_CETUS2` platform identifier as the A7 IV. Physical
backup property numbers are not assumed to match across models.

