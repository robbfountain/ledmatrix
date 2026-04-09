# LEDMatrix Emulator Setup Guide

Run and test the LED matrix display on your local machine without physical hardware, using [RGBMatrixEmulator](https://github.com/ty-porter/RGBMatrixEmulator) (pygame-based).

## Prerequisites

- Python 3.10 or higher
- macOS, Linux, or Windows
- A working virtual environment (the repo includes one at `venv/`)

## Setup

### 1. Activate the virtual environment

From the `LEDMatrix/` directory:

```bash
source venv/bin/activate
```

If your shell says `command not found`, you are either not in the right directory or using a shell that requires a different activate script:

```bash
# fish shell
source venv/bin/activate.fish

# csh/tcsh
source venv/bin/activate.csh
```

### 2. Install emulator dependency

The emulator requirement is kept separate from `requirements.txt` so it does not get installed on the Pi.

```bash
pip install -r requirements-emulator.txt
```

If you have not yet installed the main dependencies:

```bash
pip install -r requirements.txt
```

## Running the emulator

Pass the `-e` (or `--emulator`) flag to `run.py`:

```bash
python3 run.py -e
```

Add `-d` for verbose debug output:

```bash
python3 run.py -e -d
```

When emulator mode is active you will see a pygame window rendering the matrix and a startup banner in the terminal:

```
============================================================
LEDMatrix Emulator Mode Enabled
============================================================
Using pygame/RGBMatrixEmulator for display
Press ESC to exit
```

## Controls

| Key | Action |
|-----|--------|
| `ESC` | Exit |

## Emulator configuration

`RGBMatrixEmulator` reads an optional `emulator_config.json` file placed in the project root. Create it if you want to adjust rendering:

```json
{
    "pixel_size": 16,
    "pixel_style": "square",
    "pixel_outline": 0,
    "pixel_glow": 6,
    "display_adapter": "pygame"
}
```

| Key | Description | Default |
|-----|-------------|---------|
| `pixel_size` | Size of each emulated pixel in screen pixels | `16` |
| `pixel_style` | Shape of each pixel (`"square"` or `"circle"`) | `"square"` |
| `pixel_outline` | Border thickness around each pixel (0 to disable) | `0` |
| `pixel_glow` | Glow bloom intensity (0 to disable) | `6` |
| `display_adapter` | Rendering backend (`"pygame"` or `"browser"`) | `"pygame"` |

### Browser adapter

If you cannot run a graphical window (headless environment, remote session), use the browser adapter. It starts a local web server and renders the matrix as a video stream.

```json
{
    "display_adapter": "browser",
    "browser": {
        "port": 8888,
        "target_fps": 24,
        "quality": 70
    }
}
```

Then open `http://localhost:8888` in a browser after starting `run.py -e`.

## Troubleshooting

**`ModuleNotFoundError: No module named 'RGBMatrixEmulator'`**
Run `pip install -r requirements-emulator.txt` inside the active venv.

**Pygame window does not open on macOS**
Ensure you are running inside a terminal that has display access (not a headless SSH session). If using an SSH session, switch to the browser adapter.

**Port 8888 already in use (browser adapter)**
Change `port` in `emulator_config.json` to an available port.
