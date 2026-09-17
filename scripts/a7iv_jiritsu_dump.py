#!/usr/bin/env python3
"""Resumable read-only collector for update-backed A7 IV 6.02 files."""

import argparse
import hashlib
import json
import os
import stat
import struct
import sys
from collections import Counter
from pathlib import Path, PurePosixPath

from pmca.commands.usb import senserShellCommand


JIRITSU_CATEGORY = 0x1001
JIRITSU_SET_FILE_PATH = 0x400F
JIRITSU_GET_FILE2 = 0x4011

SAMPLE_PATHS = {
    "/version.txt",
    "/sbin/initrc/fstab",
    "/system/vmlinux.bin",
    "/cp/tomco.txt",
    "/usr/share/pmbp/DeviceInfo.xml",
}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_stream(stream):
    digest = hashlib.sha256()
    size = 0
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        size += len(chunk)
        digest.update(chunk)
    return size, digest.hexdigest()


def load_readers(fwtool_root):
    sys.path.insert(0, str(fwtool_root))
    from fwtool.archive.ext2 import readExt2
    from fwtool.archive.fat import readFat

    update_root = (
        fwtool_root
        / "unpacked/firmware.tar_unpacked/0700_part_image/dev"
    )
    return (
        ("/", update_root / "nflasha7", readExt2),
        ("/usr", update_root / "nflasha15", readExt2),
        ("/system", update_root / "nflasha3", readFat),
        ("/cp", update_root / "nflasha8", readFat),
    )


def build_manifest(sources, include_all):
    manifest = []
    for mount, image_path, reader in sources:
        if not image_path.is_file():
            raise RuntimeError("Missing update filesystem image: %s" % image_path)
        with image_path.open("rb") as image:
            for entry in reader(image):
                if not stat.S_ISREG(entry.mode):
                    continue
                remote = str(PurePosixPath(mount) / entry.path.lstrip("/"))
                if not remote.startswith("/"):
                    remote = "/" + remote
                if not include_all and remote not in SAMPLE_PATHS:
                    continue
                size, digest = sha256_stream(entry.contents)
                manifest.append(
                    {"remote": remote, "size": size, "sha256": digest}
                )

    folded_counts = Counter(entry["remote"].casefold() for entry in manifest)
    for entry in manifest:
        if folded_counts[entry["remote"].casefold()] > 1:
            entry["output_relative"] = (
                "__case_collisions__/"
                + entry["remote"].encode("utf-8").hex()
                + ".bin"
            )
        else:
            entry["output_relative"] = entry["remote"].lstrip("/")
    return manifest


def parse_status(response, command_name):
    if len(response) < 4:
        raise RuntimeError(
            "%s response is shorter than its 4-byte status: %r"
            % (command_name, response)
        )
    return struct.unpack_from("<I", response)[0], response[4:]


def read_remote_file(camera, remote):
    traversal = ("../../" + remote.lstrip("/")).encode("utf-8")
    set_response = camera._sendAdjustControlPacket(
        JIRITSU_CATEGORY,
        JIRITSU_SET_FILE_PATH,
        b"\x00" + traversal,
    )
    set_status, set_extra = parse_status(set_response, "SET_FILE_PATH")
    if set_status != 0 or set_extra:
        raise RuntimeError(
            "SET_FILE_PATH status 0x%08x, extra=%s"
            % (set_status, set_extra.hex())
        )

    get_response = camera._sendAdjustControlPacket(
        JIRITSU_CATEGORY,
        JIRITSU_GET_FILE2,
        b"\x00\xff\x00",
    )
    get_status, payload = parse_status(get_response, "GET_FILE2")
    if get_status != 0:
        raise RuntimeError("GET_FILE2 status 0x%08x" % get_status)
    return payload


def load_completed(index_path, output_root, manifest):
    completed = set()
    if not index_path.exists():
        return completed
    latest = {}
    for line in index_path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            latest[record["remote"]] = record
        except (KeyError, ValueError):
            continue
    expected_outputs = {
        entry["remote"]: entry["output_relative"] for entry in manifest
    }
    for remote, record in latest.items():
        try:
            expected_relative = expected_outputs[remote]
            recorded_relative = record.get("output_relative", remote.lstrip("/"))
            output = output_root / recorded_relative
            if (
                record.get("result") == "ok"
                and recorded_relative == expected_relative
                and output.is_file()
                and sha256_file(output) == record.get("live_sha256")
            ):
                completed.add(remote)
        except (KeyError, OSError, ValueError):
            continue
    return completed


def collect(camera, manifest, output_root):
    output_root.mkdir(parents=True, exist_ok=True)
    index_path = output_root / "dump-index.jsonl"
    completed = load_completed(index_path, output_root, manifest)
    pending = [entry for entry in manifest if entry["remote"] not in completed]

    print("Manifest files: %d" % len(manifest))
    print("Already verified locally: %d" % (len(manifest) - len(pending)))
    print("Pending reference bytes: %d" % sum(e["size"] for e in pending))

    camera.readHasp()
    with index_path.open("a", encoding="utf-8") as index:
        for number, entry in enumerate(pending, 1):
            remote = entry["remote"]
            print("[%d/%d] %s" % (number, len(pending), remote), flush=True)
            try:
                payload = read_remote_file(camera, remote)
                live_hash = sha256_bytes(payload)
                output = output_root / entry["output_relative"]
                output.parent.mkdir(parents=True, exist_ok=True)
                temporary = output.with_name(output.name + ".part")
                temporary.write_bytes(payload)
                os.replace(str(temporary), str(output))
                record = {
                    "remote": remote,
                    "output_relative": entry["output_relative"],
                    "result": "ok",
                    "bytes": len(payload),
                    "live_sha256": live_hash,
                    "reference_bytes": entry["size"],
                    "reference_sha256": entry["sha256"],
                    "matches_reference": (
                        len(payload) == entry["size"]
                        and live_hash == entry["sha256"]
                    ),
                }
                print(
                    "  %d bytes, update match: %s"
                    % (len(payload), "yes" if record["matches_reference"] else "no")
                )
            except Exception as error:
                record = {
                    "remote": remote,
                    "result": "error",
                    "error": str(error),
                    "reference_bytes": entry["size"],
                    "reference_sha256": entry["sha256"],
                }
                print("  ERROR: %s" % error)
            index.write(json.dumps(record, sort_keys=True) + "\n")
            index.flush()

    print("Local output: %s" % output_root)
    print("Index: %s" % index_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fwtool-root", type=Path, required=True)
    parser.add_argument(
        "--all",
        action="store_true",
        help="collect every regular file represented in the extracted update",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("a7iv-live-dump-602"),
    )
    args = parser.parse_args()

    sources = load_readers(args.fwtool_root.expanduser().resolve())
    manifest = build_manifest(sources, args.all)
    mode = "full" if args.all else "sample"
    print(
        "Prepared %s manifest: %d files, %d reference bytes"
        % (mode, len(manifest), sum(entry["size"] for entry in manifest))
    )

    completed = False

    def run(camera):
        nonlocal completed
        collect(camera, manifest, args.output.expanduser().resolve())
        completed = True

    senserShellCommand(complete=run)
    if not completed:
        raise SystemExit("Collector did not run; rerun after camera reconnection")


if __name__ == "__main__":
    main()

