# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CLI tool that converts images to ASCII art. Core logic in `img2ascii.py`, interactive TUI in `tui.py` + `tui.tcss`. Supports color output (on by default), block characters, URL support, HTML/image export, and auto-sizing to terminal width.

## Setup and Running

```bash
pip install .           # installs `img2ascii` (CLI) and `img2ascii-tui` (TUI)
pip install -e .        # editable/dev mode
```

```bash
# Basic usage (color on by default, auto-sizes to terminal width)
img2ascii photo.jpg

# Block characters, presets, image export
img2ascii photo.jpg -b
img2ascii photo.jpg -p hd
img2ascii photo.jpg --image art.png

# Disable color or HTML output
img2ascii photo.jpg --no-color
img2ascii photo.jpg --no-html
```

The file argument is positional, but `--file` still works for backwards compatibility.

There are no tests, linter, or build system configured.

## Architecture

The entire application lives in `img2ascii.py` using a purely functional style (no classes). The pipeline is:

1. **`load_image(source)`** — Loads from local path or HTTP URL via requests/PIL
2. **`convert_image_to_ascii(image, cols, scale, ramp)`** — Divides image into tiles, computes average brightness (`get_average_l`) and color (`get_average_color`) per tile using NumPy, maps brightness to a character from the selected ramp
3. **Rendering** — Multiple outputs run in sequence (not mutually exclusive):
   - `render_html(rows, html_path)` — HTML with inline `<span>` color styling (on by default, `--no-html` to suppress)
   - `render_image(rows, image_path)` — PNG/JPEG via Pillow's ImageDraw (when `--image` is specified)
   - `render_terminal(rows, use_color)` — stdout with TrueColor ANSI (default) or `render_file(rows, out_path)` for plain text
4. **`main()`** — argparse CLI with presets (`PRESETS` dict), orchestrates the above

Three character ramps are defined as globals: `GSCALE_70` (70-char), `GSCALE_10` (10-char), `GSCALE_BLOCK` (block chars). The `--invert` flag reverses the ramp.

Presets (`-p`): `hd` (300 cols, block, color), `retro` (80 cols, morelevels, no color), `minimal` (60 cols, no color). Preset values are defaults that explicit flags can override.

## TUI (`tui.py` + `tui.tcss`)

Interactive terminal UI built with Textual (`img2ascii-tui`). Vaporwave-themed.

- **`ImageDirectoryTree`** — `DirectoryTree` subclass filtered to image files, plain text icons (no emojis)
- **`AsciiArtApp`** — Main app with sidebar (file tree + settings panel) and preview area
- Settings panel has `Select` (presets), `Input` (cols/scale), `Switch` (color/block/morelevels/invert), and export `Button`s
- Selecting a preset updates all controls; changing any control sets preset to "custom"
- Preview renders via `RichLog` with `rich.text.Text` objects for per-character color styling
- Image conversion runs in a worker thread (`@work(thread=True)`) to keep UI responsive
- Imports `load_image`, `convert_image_to_ascii`, `render_html`, `render_image` from `img2ascii.py`
- Styling lives in `tui.tcss` — all colors are hardcoded vaporwave palette, not Textual theme variables

## Dependencies

Defined in `pyproject.toml` (no separate requirements.txt):

- **Pillow** — image loading, cropping, and image export rendering
- **NumPy** — average brightness/color calculation on pixel arrays
- **requests** — fetching images from URLs
- **Textual** — TUI framework (used by `tui.py`)
