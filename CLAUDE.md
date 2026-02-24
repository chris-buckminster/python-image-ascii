# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CLI tool that converts images to ASCII art. Single-file Python application (`python-image-ascii.py`) with color output, block characters (░▒▓█), URL support, HTML export, and auto-sizing to terminal width. Licensed under GPLv3.

## Setup and Running

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```bash
# Basic usage
python python-image-ascii.py --file <path_or_url>

# With color / block chars / HTML export
python python-image-ascii.py --file photo.jpg --color
python python-image-ascii.py --file photo.jpg --block --color
python python-image-ascii.py --file photo.jpg --html output.html
```

There are no tests, linter, or build system configured.

## Architecture

The entire application lives in `python-image-ascii.py` using a purely functional style (no classes). The pipeline is:

1. **`load_image(source)`** — Loads from local path or HTTP URL via requests/PIL
2. **`convert_image_to_ascii(image, cols, scale, ramp)`** — Divides image into tiles, computes average brightness (`get_average_l`) and color (`get_average_color`) per tile using NumPy, maps brightness to a character from the selected ramp
3. **Rendering** — One of three output paths:
   - `render_terminal(rows, use_color)` — stdout with optional TrueColor ANSI escape codes
   - `render_file(rows, out_path)` — plain text file
   - `render_html(rows, html_path)` — HTML with inline `<span>` color styling
4. **`main()`** — argparse CLI, orchestrates the above

Three character ramps are defined as globals: `GSCALE_70` (70-char), `GSCALE_10` (10-char), `GSCALE_BLOCK` (block chars). The `--invert` flag reverses the ramp.

## Dependencies

- **Pillow** — image loading and cropping
- **NumPy** — average brightness/color calculation on pixel arrays
- **requests** — fetching images from URLs
