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
```

2. Install the rpi-rgb-led-matrix library:
```bash
cd rpi-rgb-led-matrix-master
make
sudo make install
cd ..
```

3. Install Python dependencies:
```bash
python3 -m pip install -r requirements.txt
```

4. Install the DejaVu Sans font:
```bash
sudo apt-get install -y fonts-dejavu
```

## Configuration

Edit the `config/config.json` file to customize:
- Timezone
- Display settings (brightness, dimensions)
- Clock format and update interval

## Running the Clock

To start the clock:
```bash
cd src
python3 clock.py
```

To stop the clock, press Ctrl+C.

## Project Structure

- `src/`
  - `clock.py` - Main clock application
  - `config_manager.py` - Configuration management
  - `display_manager.py` - LED matrix display handling
- `config/`
  - `config.json` - Configuration settings 