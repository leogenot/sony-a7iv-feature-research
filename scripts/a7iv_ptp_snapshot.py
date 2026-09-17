#!/usr/bin/env python3
"""Save a read-only snapshot of every Sony PC Remote PTP property descriptor."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from a7iv_ptp_log_probe import (
    SONY_SDIO_CONNECT,
    SONY_SDIO_GET_EXT_DEVICE_INFO,
    SONY_GET_DEVICE_PROP_DESC,
    find_sony_ptp_device,
    parse_descriptor,
    parse_extended_device_info,
    read_command,
)


def json_descriptor(data):
    result = parse_descriptor(data)
    result["raw"] = data.hex()
    result["trailing"] = result["trailing"].hex()
    if "range" in result:
        result["range"] = list(result["range"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pmca-root",
        type=Path,
        default=Path.home() / "Documents/Sony-PMCA-RE",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("a7iv-ptp-snapshot.json"),
    )
    args = parser.parse_args()
    sys.path.insert(0, str(args.pmca_root.resolve()))

    from pmca.commands.usb import importDriver
    from pmca.usb import MtpDevice
    from pmca.usb.driver import USB_CLASS_PTP
    from pmca.usb.driver.generic import GenericUsbException

    snapshot = {
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "descriptors": [],
        "descriptor_errors": [],
    }

    try:
        with importDriver() as drivers:
            device, info = find_sony_ptp_device(drivers, MtpDevice, USB_CLASS_PTP)
            snapshot["camera"] = {
                "manufacturer": info.manufacturer,
                "model": info.model,
                "vendor_extension": info.vendorExtension,
            }
            required = {SONY_SDIO_CONNECT, SONY_SDIO_GET_EXT_DEVICE_INFO}
            if not required.issubset(info.operationsSupported):
                raise SystemExit(
                    "The camera is not exposing Sony PC Remote commands. Set USB "
                    "Connection Mode to PC Remote, reconnect it, and close any "
                    "camera-control application."
                )

            read_command(device, SONY_SDIO_CONNECT, [1, 0, 0])
            read_command(device, SONY_SDIO_CONNECT, [2, 0, 0])
            ext_data = read_command(device, SONY_SDIO_GET_EXT_DEVICE_INFO, [0xC8])
            version, properties, controls, trailing = parse_extended_device_info(ext_data)
            read_command(device, SONY_SDIO_CONNECT, [3, 0, 0])

            snapshot["sony_protocol_version"] = version
            snapshot["advertised_codes"] = ["0x%04x" % value for value in properties]
            snapshot["control_codes"] = ["0x%04x" % value for value in controls]
            snapshot["extended_info_raw"] = ext_data.hex()
            snapshot["extended_info_trailing"] = trailing.hex()

            print("Camera: %s %s" % (info.manufacturer, info.model))
            print("Advertised codes: %d" % len(properties))
            print("Control codes: %d" % len(controls))

            for index, property_code in enumerate(properties, 1):
                try:
                    raw = read_command(
                        device, SONY_GET_DEVICE_PROP_DESC, [property_code]
                    )
                    descriptor = json_descriptor(raw)
                    snapshot["descriptors"].append(descriptor)
                    print(
                        "[%d/%d] 0x%04x %s current=%s writable=%s"
                        % (
                            index,
                            len(properties),
                            property_code,
                            descriptor["datatype_name"],
                            descriptor["current"],
                            "yes" if descriptor["writable"] else "no",
                        )
                    )
                except GenericUsbException:
                    raise
                except Exception as exc:
                    snapshot["descriptor_errors"].append(
                        {"property_code": "0x%04x" % property_code, "error": str(exc)}
                    )
                    print(
                        "[%d/%d] 0x%04x unavailable: %s"
                        % (index, len(properties), property_code, exc)
                    )

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(snapshot, indent=2) + "\n")
        print("Saved: %s" % args.output.resolve())
        print("No property was changed.")
    except GenericUsbException:
        raise SystemExit(
            "A USB endpoint stalled. Reconnect the camera in PC Remote mode, "
            "close any camera-control application, and run the snapshot again."
        )


if __name__ == "__main__":
    main()
