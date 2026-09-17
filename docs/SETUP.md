# Python and repository setup

## Requirements

- Sony ILCE-7M4 running firmware 6.02
- A data-capable USB cable
- Python 3; Python 3.9.6 is the version used for the verified macOS session
- Git
- `libusb` and permission to access the USB device
- The official Sony `BODYDATA.DAT` update file for offline extraction

## Clone this research repository

SSH:

```bash
git clone git@github.com:leogenot/sony-a7iv-feature-research.git
```

HTTPS:

```bash
git clone https://github.com/leogenot/sony-a7iv-feature-research.git
```

Because the repository is private, GitHub authentication is required.

## Clone Sony-PMCA-RE

```bash
cd ~/Documents
git clone https://github.com/ma1co/Sony-PMCA-RE.git
cd Sony-PMCA-RE
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS, install `libusb` if it is missing:

```bash
brew install libusb
```

The verified invocation on macOS was:

```bash
sudo ./venv/bin/python ./pmca-console.py serviceshell
```

## Clone the A7 IV fwtool branch

```bash
cd ~/Documents
git clone --branch a7iv https://github.com/DavidBuchanan314/fwtool.py.git
cd fwtool.py
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Keep `Sony-PMCA-RE`, `fwtool.py`, and this repository as separate directories.
Do not commit the update file, unpacked firmware or a camera backup.

## Camera preparation

1. Charge the battery sufficiently for a service session.
2. In the camera USB settings, select **Mass Storage**.
3. Connect the camera directly to the computer.
4. Close Photos and other applications that may claim the camera USB device.
5. Start `serviceshell`. The expected transition is:

```text
Sony DSC is a camera in mass storage mode
Switching to service mode
Found a camera in service mode
Authenticating
```

If the first attempt times out while the USB mode is changing, run the command
again after the service-mode device appears.

