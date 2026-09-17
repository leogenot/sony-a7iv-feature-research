#!/usr/bin/env python3
"""Read Sony's Log Shooting PTP descriptor without changing the camera."""

import argparse
import struct
import sys
from pathlib import Path


SONY_VENDOR_ID = 0x054C
SONY_SDIO_CONNECT = 0x9201
SONY_SDIO_GET_EXT_DEVICE_INFO = 0x9202
SONY_GET_DEVICE_PROP_DESC = 0x9203
SONY_LOG_SHOOTING_MODE = 0xE0E3

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
    # Sony's 0x9203 descriptor has an extra status byte after GetSet.
    if len(data) < 6:
        raise ValueError("Descriptor is too short: %s" % data.hex())
    property_code, datatype, get_set, status = struct.unpack_from("<HHBB", data, 0)
    offset = 6
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
        "status": status,
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


def unpack_u16_array(data, offset):
    if offset + 4 > len(data):
        raise ValueError("Truncated Sony property-code array count")
    count = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    end = offset + count * 2
    if end > len(data):
        raise ValueError("Truncated Sony property-code array")
    values = list(struct.unpack_from("<%dH" % count, data, offset)) if count else []
    return values, end


def parse_extended_device_info(data):
    if len(data) < 2:
        raise ValueError("Sony extended-device-info response is too short")
    version = struct.unpack_from("<H", data, 0)[0]
    properties, offset = unpack_u16_array(data, 2)
    controls, offset = unpack_u16_array(data, offset)
    return version, properties, controls, data[offset:]


def read_command(device, operation, params):
    response, data = device.driver.sendReadCommand(operation, params)
    device._checkResponse(response)
    return data


def find_sony_ptp_device(drivers, mtp_device_class, ptp_class):
    cameras = []
    for _handle, interface_class, driver in drivers.listDevices(SONY_VENDOR_ID):
        if interface_class != ptp_class:
            continue
        device = mtp_device_class(driver)
        info = device.getDeviceInfo()
        if "sony" in info.manufacturer.lower():
            cameras.append((device, info))

    if not cameras:
        raise SystemExit(
            "No Sony PTP camera found. Set USB Connection Mode to PC Remote, "
            "reconnect the cable, and close Imaging Edge/Photos."
        )
    if len(cameras) != 1:
        raise SystemExit("More than one Sony PTP camera was found.")
    return cameras[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pmca-root",
        type=Path,
        default=Path.home() / "Documents/Sony-PMCA-RE",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(args.pmca_root.resolve()))

    from pmca.commands.usb import importDriver
    from pmca.usb import MtpDevice
    from pmca.usb.driver import USB_CLASS_PTP
    from pmca.usb.driver.generic import GenericUsbException

    try:
        with importDriver() as drivers:
            device, info = find_sony_ptp_device(drivers, MtpDevice, USB_CLASS_PTP)
            print("Camera: %s %s" % (info.manufacturer, info.model))
            print("PTP vendor extension: %s" % info.vendorExtension)

            required = {SONY_SDIO_CONNECT, SONY_SDIO_GET_EXT_DEVICE_INFO}
            if not required.issubset(info.operationsSupported):
                raise SystemExit(
                    "The camera is in file-transfer MTP mode, not PC Remote mode. "
                    "No Sony remote command was sent. Change USB Connection Mode "
                    "to PC Remote, reconnect, and run the probe again."
                )

            print("Sony SDIO handshake: phase 1")
            read_command(device, SONY_SDIO_CONNECT, [1, 0, 0])
            print("Sony SDIO handshake: phase 2")
            read_command(device, SONY_SDIO_CONNECT, [2, 0, 0])
            ext_data = read_command(device, SONY_SDIO_GET_EXT_DEVICE_INFO, [0xC8])
            version, properties, controls, trailing = parse_extended_device_info(ext_data)
            print("Sony protocol version: 0x%04x" % version)
            print("Advertised properties: %d" % len(properties))
            print("Advertised controls: %d" % len(controls))
            if trailing:
                print("Extended-info trailing bytes: %s" % trailing.hex())
            print("Sony SDIO handshake: phase 3")
            read_command(device, SONY_SDIO_CONNECT, [3, 0, 0])

            advertised = SONY_LOG_SHOOTING_MODE in properties
            controlled = SONY_LOG_SHOOTING_MODE in controls
            print(
                "Log Shooting 0x%04x advertised: %s"
                % (SONY_LOG_SHOOTING_MODE, "yes" if advertised else "no")
            )
            print(
                "Log Shooting 0x%04x controllable: %s"
                % (SONY_LOG_SHOOTING_MODE, "yes" if controlled else "no")
            )
            if not advertised:
                print(
                    "The official Sony PC Remote surface does not publish the "
                    "Log Shooting property on this camera/mode."
                )
                print("Read-only probe complete; no property was changed.")
                return

            descriptor_data = read_command(
                device, SONY_GET_DEVICE_PROP_DESC, [SONY_LOG_SHOOTING_MODE]
            )
            descriptor = parse_descriptor(descriptor_data)

            print("Property: 0x%04x" % descriptor["property_code"])
            print(
                "Datatype: %s (0x%04x)"
                % (descriptor["datatype_name"], descriptor["datatype"])
            )
            print("Writable: %s" % ("yes" if descriptor["writable"] else "no"))
            print("Sony status byte: 0x%02x" % descriptor["status"])
            print("Factory value: %s" % descriptor["factory"])
            print("Current value: %s" % descriptor["current"])
            if "enum" in descriptor:
                print("Allowed values: %s" % descriptor["enum"])
            if "range" in descriptor:
                print("Range (min, max, step): %s" % (descriptor["range"],))
            if descriptor["trailing"]:
                print("Descriptor raw: %s" % descriptor_data.hex())
            print("Read-only probe complete; no property was changed.")
    except GenericUsbException:
        raise SystemExit(
            "A USB endpoint stalled. Confirm PC Remote mode, reconnect the "
            "camera, close any camera-control app, and run the probe again."
        )


if __name__ == "__main__":
    main()
