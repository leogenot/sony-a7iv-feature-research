#!/usr/bin/env python3
"""Read-only probe for Sony's PTP Log Shooting Mode property."""

import argparse
import struct
import sys
from pathlib import Path


PTP_OC_GET_DEVICE_PROP_DESC = 0x1014
PTP_OC_GET_DEVICE_PROP_VALUE = 0x1015
PTP_DPC_SONY_LOG_SHOOTING_MODE = 0xE0E3

SCALAR_TYPES = {
    0x0001: ("INT8", "b"),
    0x0002: ("UINT8", "B"),
    0x0003: ("INT16", "h"),
    0x0004: ("UINT16", "H"),
    0x0005: ("INT32", "i"),
    0x0006: ("UINT32", "I"),
    0x0007: ("INT64", "q"),
    0x0008: ("UINT64", "Q"),
}


def unpack_value(data, offset, datatype):
    try:
        name, fmt = SCALAR_TYPES[datatype]
    except KeyError:
        raise ValueError("Unsupported PTP datatype 0x%04x" % datatype)
    size = struct.calcsize("<" + fmt)
    if offset + size > len(data):
        raise ValueError("Truncated %s value" % name)
    return struct.unpack_from("<" + fmt, data, offset)[0], offset + size


def parse_descriptor(data):
    if len(data) < 5:
        raise ValueError("Descriptor is too short: %s" % data.hex())
    property_code, datatype, get_set = struct.unpack_from("<HHB", data, 0)
    offset = 5
    factory, offset = unpack_value(data, offset, datatype)
    current, offset = unpack_value(data, offset, datatype)
    if offset >= len(data):
        raise ValueError("Descriptor has no form flag")
    form = data[offset]
    offset += 1
    result = {
        "property_code": property_code,
        "datatype": datatype,
        "datatype_name": SCALAR_TYPES.get(datatype, ("UNKNOWN",))[0],
        "writable": get_set == 1,
        "factory": factory,
        "current": current,
        "form": form,
    }
    if form == 1:
        minimum, offset = unpack_value(data, offset, datatype)
        maximum, offset = unpack_value(data, offset, datatype)
        step, offset = unpack_value(data, offset, datatype)
        result["range"] = (minimum, maximum, step)
    elif form == 2:
        if offset + 2 > len(data):
            raise ValueError("Truncated enumeration count")
        count = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        values = []
        for _ in range(count):
            value, offset = unpack_value(data, offset, datatype)
            values.append(value)
        result["enum"] = values
    result["trailing"] = data[offset:]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pmca-root",
        type=Path,
        default=Path.home() / "Documents/Sony-PMCA-RE",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(args.pmca_root.resolve()))

    from pmca.commands.usb import getDevice, importDriver
    from pmca.usb.sony import SonyMtpExtCmdDevice

    with importDriver() as drivers:
        device = getDevice(drivers)
        if device is None:
            raise SystemExit(1)
        if not isinstance(device, SonyMtpExtCmdDevice):
            raise SystemExit(
                "Camera must be connected in MTP mode; no writes were attempted."
            )

        response, descriptor_data = device.driver.sendReadCommand(
            PTP_OC_GET_DEVICE_PROP_DESC,
            [PTP_DPC_SONY_LOG_SHOOTING_MODE],
        )
        device._checkResponse(response)
        descriptor = parse_descriptor(descriptor_data)

        response, value_data = device.driver.sendReadCommand(
            PTP_OC_GET_DEVICE_PROP_VALUE,
            [PTP_DPC_SONY_LOG_SHOOTING_MODE],
        )
        device._checkResponse(response)
        value, consumed = unpack_value(value_data, 0, descriptor["datatype"])

        print("Property: 0x%04x" % descriptor["property_code"])
        print(
            "Datatype: %s (0x%04x)"
            % (descriptor["datatype_name"], descriptor["datatype"])
        )
        print("Writable: %s" % ("yes" if descriptor["writable"] else "no"))
        print("Factory value: %s" % descriptor["factory"])
        print("Descriptor current value: %s" % descriptor["current"])
        print("Live value: %s" % value)
        if "enum" in descriptor:
            print("Allowed values: %s" % descriptor["enum"])
        if "range" in descriptor:
            print("Range (min, max, step): %s" % (descriptor["range"],))
        if descriptor["trailing"] or value_data[consumed:]:
            print("Descriptor raw: %s" % descriptor_data.hex())
            print("Value raw: %s" % value_data.hex())
        print("Read-only probe complete; no property was changed.")


if __name__ == "__main__":
    main()
