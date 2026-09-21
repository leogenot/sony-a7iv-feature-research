# David Buchanan A7 IV repositories

Reviewed 2026-09-21 at:

- [`ILCE-7M4-RE` commit `660aa69`](https://github.com/DavidBuchanan314/ILCE-7M4-RE/commit/660aa69)
- [`Sony-ILCE-7M4-Linux` commit `fa5c6f6a`](https://github.com/DavidBuchanan314/Sony-ILCE-7M4-Linux/commit/fa5c6f6a)

The repositories were cloned into a temporary directory for inspection. No
boot ROM, eMMC image, encryption key, firmware binary or third-party source
tree was copied into this repository.

## Conclusion

The two repositories materially improve the **acquisition, boot-chain and
hardware-interface** side of this project. They do not directly identify a
new retail-disabled camera feature.

| Repository | Value to this project | Limit |
| --- | --- | --- |
| `ILCE-7M4-RE` | High: cold-boot code execution, read-only eMMC partition dumps, transparent partition decryption, AP/Cetus/Darwin memory access, and a route to the Cetus NOR | Contains no `appFw` feature analysis, HAITA rules, menu catalogue or recorder-profile proof |
| `Sony-ILCE-7M4-Linux` | Medium: names the CXD90057 registers, memory map, SDM2 partition format, kernel interfaces and SPAcc crypto engine; provides release-to-release kernel deltas | It is GPL kernel/driver source, not Sony's application, imaging pipeline, sensor or recorder source |

Neither repository changes the product-class result: the retail A7 IV runs as
`PRODUCT_MODEL_LS`, while `LAX` is a different camera class. See
[Product class](PRODUCT_CLASS.md).

## What `ILCE-7M4-RE` adds

### 1. A repeatable pre-OS execution route

The main CXD90057 AP has a ROM serial-boot receiver reachable through the
Multi/Micro USB accessory connector. The repository uses an RP2040 board to:

1. pulse the camera reset line;
2. send the serial-boot carrier and records;
3. exploit a stack-resident unlock comparison;
4. stage a bare-metal payload at `0xfe020000`; and
5. execute it at EL3.

The relevant implementation is
[`scripts/push_payload.py`](https://github.com/DavidBuchanan314/ILCE-7M4-RE/blob/main/scripts/push_payload.py),
[`tools/uart_boot/uart_boot.ino`](https://github.com/DavidBuchanan314/ILCE-7M4-RE/blob/main/tools/uart_boot/uart_boot.ino),
and the [fastboot payload](https://github.com/DavidBuchanan314/ILCE-7M4-RE/tree/main/payloads/fastboot).

This is independent of Linux, service mode and the normal Sony application.
The payload lives in eSRAM and need not modify persistent storage. It still
writes arbitrary AP RAM and takes over the boot process, so it is outside this
project's current read-only camera-interaction policy.

### 2. Complete read-only eMMC acquisition

The fastboot payload implements:

- SDM2 partition enumeration;
- raw `boot0`/`boot1` and user-area reads;
- named partition dumps;
- transparent AES-XTS decryption for normal user-area partitions; and
- bounds-checked writes and Android sparse-image handling.

The dump path is useful even though the payload also has flashing commands.
The implementation states that each 512-byte sector uses its **absolute eMMC
sector number** as the XTS tweak. The offline scripts derive the keys from the
CXD90057 boot ROM scrambling table and the decrypted eMMC loader. See
[`parse_emmc_boot0.py`](https://github.com/DavidBuchanan314/ILCE-7M4-RE/blob/main/scripts/parse_emmc_boot0.py),
[`parse_emmc_partitions.py`](https://github.com/DavidBuchanan314/ILCE-7M4-RE/blob/main/scripts/parse_emmc_partitions.py),
and [`fastboot.c`](https://github.com/DavidBuchanan314/ILCE-7M4-RE/blob/main/payloads/fastboot/src/fastboot.c).

For feature research, a full decrypted dump could reveal persistent or active
partitions not present in an update package or the current Jiritsu filesystem
dump. It would also permit exact comparison of the installed system against
the 6.02 updater. It does not by itself prove that a feature is reachable.

### 3. The most valuable new lead: Cetus and its 64 MiB NOR

The CXD90058 coprocessor (named **Cetus**) has a ROM SPI monitor with memory
write, checksum and execute operations. The fastboot payload can reset Cetus,
install a small monitor payload, read/write its memory, execute code, dump its
boot ROM and dump the 64 MiB NOR flash. See
[`payloads/fastboot/src/cetus.c`](https://github.com/DavidBuchanan314/ILCE-7M4-RE/blob/main/payloads/fastboot/src/cetus.c)
and the [Cetus payload](https://github.com/DavidBuchanan314/ILCE-7M4-RE/tree/main/payloads/fastboot/cetus).

This matters to the hidden-feature project because `appFw.so` can contain a
complete setting and IPC sequence while a lower imaging, display or recorder
processor rejects it. A Cetus NOR dump provides a way to determine whether
such lower-layer implementations exist on the retail A7 IV. The best targets
would be:

- `PID_SET_ANAMO_DESQUEEZE_SCALE`, to resolve the remaining lower-layer
  uncertainty in [De-Squeeze](DE_SQUEEZE.md);
- 4096-wide DCI 4K mode identifiers and encoder configurations;
- 5016x3344 / full-frame 5K 3:2 scan modes;
- RAW/X-OCN mode tables and product checks; and
- model-specific sensor timing and imager-mode acceptance tables.

The public repository does not include a decoded Cetus NOR or demonstrate any
of those feature paths. It supplies the acquisition mechanism, not the result.

### 4. Darwin access

The payload can read memory from the Darwin power/watchdog controller and
report its watchdog state. This is useful for platform recovery and reset
research, but currently has little direct value for recorder or UI features.

### 5. Boot-chain implications

The repository reports encrypted eMMC partitions without signature
verification and demonstrates arbitrary pre-OS payload execution. This means
that modified system images may be technically bootable. That is a major
platform result, but it is not a safe feature-enablement method. This project
continues to prohibit firmware patching, repacking, arbitrary RAM writes and
partition flashing.

## What `Sony-ILCE-7M4-Linux` adds

### 1. Platform labels and register maps

Sony's released kernel source identifies the main AP as CXD90057 and describes
four Cortex-A35 CPUs, the GPIO/UART/SPI blocks, SCU, eSRAM, PCIe, USB and other
platform addresses. The most useful references are:

- [`cxd90057.dtsi`](https://github.com/DavidBuchanan314/Sony-ILCE-7M4-Linux/blob/main/linux-kernel/arch/arm64/boot/dts/cxd/cxd90057.dtsi)
- [`platform.h`](https://github.com/DavidBuchanan314/Sony-ILCE-7M4-Linux/blob/main/linux-kernel/drivers/udif/mach-cxd900xx/include/mach/platform.h)
- [`platform.c`](https://github.com/DavidBuchanan314/Sony-ILCE-7M4-Linux/blob/main/linux-kernel/drivers/udif/mach-cxd900xx/platform.c)

These files explain and corroborate the addresses used by the bare-metal
payload. They are useful as Ghidra labels for the loader, kernel modules and
hardware-facing binaries. They do not describe the camera sensor or media
encoder blocks.

### 2. SDM2 partition-table format

[`sdm2_partition_table.h`](https://github.com/DavidBuchanan314/Sony-ILCE-7M4-Linux/blob/main/linux-kernel/block/partitions/sdm2_partition_table.h)
defines the exact on-disk table consumed by the offline and fastboot tools:

- magic `0x36343238` (`"8246"` in little-endian byte order);
- version `0x30302e32` (`"2.00"`);
- up to 30 entries;
- 512-byte sectors; and
- 16-byte entries containing start, size, type and flags.

This is strong primary-source support for parsing a future raw eMMC image.

### 3. SPAcc AES-XTS implementation

The repository includes Sony's released Elliptic/Synopsys SPAcc driver at
commit `fa5c6f6a`. It defines AES-XTS mode, context layout, register offsets,
job submission and userspace interfaces. This validates the crypto-engine
model used by the bare-metal payload and provides names for its register-level
implementation. It does not publish the camera's secret keys; those are
recovered by the other repository's boot-chain analysis.

### 4. A real v6.00 transport addition: `usbg_iap`

The source history contains camera-system releases from v1.00 through v6.00.
Between the v5.00 commit `868c0e1f` and v6.00 commit `793c15dc`, Sony added a
USB iAP gadget driver:

- `/dev/usb/iap`;
- bulk IN and OUT endpoints;
- read/write completion events; and
- `USBG_IOC_IAP_GET_DATA`.

The source is under
[`drivers/usb/gadget/specific_gadget/usbg_iap`](https://github.com/DavidBuchanan314/Sony-ILCE-7M4-Linux/tree/main/linux-kernel/drivers/usb/gadget/specific_gadget/usbg_iap).

The A7 IV 6.02 live dump contains `/usr/kmod/usbg_iap.ko`, version
`02.00.000`, and it hash-matches the update copy recorded in the dump index.
The module is therefore a **confirmed shipped A7 IV component**. No userspace
binary in the live dump contains `/dev/usb/iap`, `iap_core` or `usbg_iap`, and
the base `usb_insmod.sh` does not load it. That does not prove the module is
unreachable, because the application can select USB functions through the
common gadget framework. It does mean the GPL source alone does not establish
a hidden user-facing mode.

The most plausible role is Apple-device USB transport for a documented phone
connection or tethering workflow. It should be classified as **shared or
on-demand transport implementation, A7 IV route unknown**, not as an
unlockable recording feature. Sony's current A7 IV Help Guide already
documents USB remote shooting with Creators' App and smartphone tethering.

### 5. What the release deltas do not show

The v6.00 kernel delta is primarily USB/iAP, still-image gadget and tracing
work. It contains no new imager, video encoder, anamorphic, LUT, DCI, RAW or
X-OCN implementation. Sony's 6.02 release notes describe 6.02 as stability
and bug fixes on top of the v6.00 feature set, consistent with the absence of
a separate GPL source snapshot for 6.02.

## Effect on the candidate inventory

| Candidate | New information from these repositories | Updated grade |
| --- | --- | --- |
| De-Squeeze Display | Cetus/NOR access could resolve whether `PID_SET_ANAMO_DESQUEEZE_SCALE` exists below `appFw`; no lower-layer proof is present yet | **B: Strong A7 IV candidate**, unchanged |
| DCI 4K | Full eMMC/Cetus acquisition could find missing encoder tables; none are exposed by the Linux source | **C: shared implementation, route unknown**, unchanged |
| Open Gate 5K 3:2 | Cetus acquisition is the best new route to seek sensor/recorder support, but the repositories add no encoder profile | **D: shared code for another product**, unchanged |
| Log Shooting / LUT / Cine EI | No new `LS` route or product gate | **D**, unchanged |
| USB iAP transport | Kernel module source and matching 6.02 retail module are confirmed; userspace activation path is unresolved | **C: shared implementation, A7 IV route unknown** |

## Recommended use in this project

1. Use the Linux source immediately as a symbol/register reference for static
   analysis. This is safe and offline.
2. Add the USB iAP module to the transport inventory, but do not treat its
   presence as a hidden-feature finding.
3. If the project's camera-interaction policy is later expanded, design a
   **read-only** serial-boot payload build that omits `flash`, `poke`,
   `exec` and Cetus write operations before considering hardware use.
4. Give a Cetus NOR acquisition its own risk review and rollback/recovery plan.
   The current upstream payload necessarily writes AP and Cetus RAM and is not
   approved under the current rules.
5. Never copy the upstream boot ROM, eMMC images, derived keys or camera dumps
   into this repository.
