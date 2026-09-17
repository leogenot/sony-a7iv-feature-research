# Read-only live filesystem collection

## Finding

In service mode, Jiritsu command `SET_FILE_PATH` accepts a path containing
parent-directory components. `GET_FILE2` then returns the referenced file.
The service constructs a path beneath `/tmp/jiritsu`; prefixing an absolute
target with `../../` resolves back to the Linux root.

The verified command constants are:

```text
category:      0x1001
SET_FILE_PATH: 0x400f
GET_FILE2:     0x4011
```

The included tools issue only path-selection and read commands. They do not
write or delete camera files.

## Fixed probe

Copy the probe into Sony-PMCA-RE:

```bash
cp ~/Documents/sony-a7iv-feature-research/scripts/a7iv_jiritsu_readonly_probe.py \
  ~/Documents/Sony-PMCA-RE/
cd ~/Documents/Sony-PMCA-RE
sudo ./venv/bin/python ./a7iv_jiritsu_readonly_probe.py
```

It reads only:

```text
/usr/share/pmbp/DeviceInfo.xml
```

For firmware 6.02 the file is 517 bytes and its SHA-256 is:

```text
e44713178fad970870ead845c93abdfcf150c418de11b306da91f2d09d67c1b7
```

## Update-backed collection

The collector builds its remote manifest from the extracted official update,
downloads only regular files represented there and checks every returned file
against the update's size and SHA-256.

```bash
cp ~/Documents/sony-a7iv-feature-research/scripts/a7iv_jiritsu_dump.py \
  ~/Documents/Sony-PMCA-RE/
cd ~/Documents/Sony-PMCA-RE
sudo ./venv/bin/python ./a7iv_jiritsu_dump.py \
  --fwtool-root ~/Documents/fwtool.py
```

Use `--all` for all update-backed regular files:

```bash
sudo ./venv/bin/python ./a7iv_jiritsu_dump.py \
  --fwtool-root ~/Documents/fwtool.py \
  --all
```

The verified full manifest contained 1,064 files and 391,692,413 reference
bytes. All 1,064 live files matched their independently extracted update bytes.

The output is resumable through `dump-index.jsonl`. Do not commit or upload the
resulting Sony files.

