#!/usr/bin/env python3
"""Save a read-only copy of the camera's settings backup through PMCA."""

import argparse
import hashlib
from pathlib import Path


def read_backup(camera, destination):
    camera.readHasp()
    print("Reading backup settings from memory...")
    data = camera.getBackupPresetData(True)
    if not data:
        raise RuntimeError("Camera returned an empty backup; nothing saved")
    with destination.open("xb") as output:
        output.write(data)
    print("Saved: %s" % destination.resolve())
    print("Bytes: %d" % len(data))
    print("SHA256: %s" % hashlib.sha256(data).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new filename")
    if not args.output.parent.is_dir():
        parser.error("Output parent directory does not exist")

    from pmca.commands.usb import senserShellCommand

    completed = False

    def collect(camera):
        nonlocal completed
        read_backup(camera, args.output)
        completed = True

    senserShellCommand(complete=collect)
    if not completed:
        raise SystemExit(
            "No backup saved. If switching timed out, rerun after reconnection."
        )


if __name__ == "__main__":
    main()

