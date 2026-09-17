# Service mode and backup workflow

## Enter service mode

```bash
cd ~/Documents/Sony-PMCA-RE
sudo ./venv/bin/python ./pmca-console.py serviceshell
```

Useful shell commands include:

```text
info
bk r <ID>
bk w <ID> <HEX_DATA>
bk s
exit
```

`bk r` reads a persisted backup property. `bk w` changes its in-memory value.
`bk s` synchronizes changes to persistent storage.

## Save a backup first

Copy the supplied helper into the PMCA repository or invoke it with that
repository on `PYTHONPATH`:

```bash
cp ~/Documents/sony-a7iv-feature-research/scripts/a7iv_read_backup.py \
  ~/Documents/Sony-PMCA-RE/
cd ~/Documents/Sony-PMCA-RE
sudo ./venv/bin/python ./a7iv_read_backup.py ./a7iv-backup-602.bin
```

The script refuses to overwrite an existing output. Keep the resulting file
private. It can contain per-camera state and identifiers.

Record a second external hash if desired:

```bash
shasum -a 256 ./a7iv-backup-602.bin
```

The verified research backup was 2,369,436 bytes and parsed with a valid Sony
BK4 checksum. Its hash is intentionally omitted because camera backups should
not be published as reusable artifacts.

## Apply one change at a time

For each experiment:

1. Read and record the original property.
2. Write one documented value.
3. Run `bk s`.
4. Exit the shell.
5. Turn the camera off and disconnect USB.
6. Remove the battery for ten seconds.
7. Reinsert it and test the behavior.
8. Restore the original value before testing an unrelated property.

This produces an interpretable result and a direct rollback path.

