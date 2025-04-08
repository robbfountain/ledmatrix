# LED Matrix Clock

A simple, modular clock application for Raspberry Pi using Adafruit LED Matrix displays.

## Hardware Requirements

- Raspberry Pi 3
- 2x Adafruit 64x32 LED Matrices
- Adafruit Pi LED Matrix Bonnet

## Installation

1. Install required system packages:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev python3-setuptools
sudo apt-get install -y build-essential git
sudo apt-get install -y python3-pil python3-pil.imagetk
sudo apt-get install -y cython3
```

2. Install the rpi-rgb-led-matrix library and Python bindings:
```bash
# Make sure you're in the main project directory
cd ~/LEDSportsMatrix/rpi-rgb-led-matrix-master

# Build the C++ library first
make

# Build and install Python bindings
cd bindings/python
sudo python3 setup.py install
cd ../..

# Install the library files
sudo cp -r lib/* /usr/local/lib/
sudo cp -r include/* /usr/local/include/
sudo ldconfig
cd ..
```

3. Install additional Python packages:
```bash
sudo python3 -m pip install pytz
```

4. Install the DejaVu Sans font:
```bash
sudo apt-get install -y fonts-dejavu
```

## Performance Optimization

To reduce flickering and improve display quality:

1. Edit `/boot/firmware/cmdline.txt`:
```bash
sudo nano /boot/firmware/cmdline.txt
```

2. Add `isolcpus=3` at the end of the line

3. Save and reboot:
```bash
sudo reboot
```

## Configuration

Edit the `config/config.json` file to customize:
- Timezone
- Display settings (brightness, dimensions)
- Clock format and update interval

For sensitive settings like API keys:
1. Copy the template: `cp config/config_secrets.template.json config/config_secrets.json`
2. Edit `config/config_secrets.json` with your API keys

## Running the Clock

The program must be run with root privileges to access the LED matrix hardware:

```bash
cd src
sudo python3 display_controller.py
```

To stop the clock, press Ctrl+C.

## Project Structure

- `src/`
  - `clock.py` - Main clock application
  - `config_manager.py` - Configuration management
  - `display_manager.py` - LED matrix display handling
- `config/`
  - `config.json` - Configuration settings
  - `config_secrets.json` - Private settings (not in git) 