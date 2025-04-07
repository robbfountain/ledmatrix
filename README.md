# LED Matrix Clock

A simple, modular clock application for Raspberry Pi using Adafruit LED Matrix displays.

## Hardware Requirements

- Raspberry Pi 3
- 2x Adafruit 64x32 LED Matrices
- Adafruit Pi LED Matrix Bonnet

## Installation

1. Install the rpi-rgb-led-matrix library from the existing folder:
```bash
cd rpi-rgb-led-matrix-master
make
sudo make install
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install the DejaVu Sans font (if not already installed):
```bash
sudo apt-get install fonts-dejavu
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
python clock.py
```

To stop the clock, press Ctrl+C.

## Project Structure

- `src/`
  - `clock.py` - Main clock application
  - `config_manager.py` - Configuration management
  - `display_manager.py` - LED matrix display handling
- `config/`
  - `config.json` - Configuration settings 