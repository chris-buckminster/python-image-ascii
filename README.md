# python-image-ascii

Command-line tool to generate ASCII art from any image. Supports color output, block characters, HTML export, image export, and URL input.

## Installation

```bash
git clone https://github.com/chris-buckminster/python-image-ascii.git
cd python-image-ascii
pip install .
```

This installs the `img2ascii` command globally.

For development, use `pip install -e .` to install in editable mode.

## Usage

```bash
# basic terminal output with color (auto-sizes to terminal width)
img2ascii photo.jpg

# block characters
img2ascii photo.jpg -b

# use a preset
img2ascii photo.jpg -p hd
img2ascii photo.jpg -p retro
img2ascii photo.jpg -p minimal

# from a URL
img2ascii https://example.com/image.png

# save to plain text file
img2ascii photo.jpg -o art.txt

# export as image (PNG or JPEG)
img2ascii photo.jpg --image art.png

# override default HTML output path
img2ascii photo.jpg --html custom.html

# disable color or HTML output
img2ascii photo.jpg --no-color
img2ascii photo.jpg --no-html
```

## Presets

| Preset | Description |
|--------|-------------|
| `hd` | 300 columns, block characters, color |
| `retro` | 80 columns, 70-character grayscale ramp, no color |
| `minimal` | 60 columns, 10-character ramp, no color |

## Options

| Flag | Short | Description |
|------|-------|-------------|
| (positional) | | Input image path or URL |
| `--cols N` | `-c` | Column width (default: terminal width) |
| `--block` | `-b` | Use block characters (░▒▓█) instead of ASCII |
| `--invert` | `-i` | Invert brightness (for light-background terminals) |
| `--scale N` | `-s` | Aspect ratio scale (default: 0.43) |
| `--preset` | `-p` | Use a preset (hd, retro, minimal) |
| `--out FILE` | `-o` | Write plain ASCII to a text file |
| `--image FILE` | | Render ASCII art to a PNG or JPEG file |
| `--html FILE` | | Override default HTML output path |
| `--no-color` | | Disable TrueColor ANSI output (on by default) |
| `--no-html` | | Suppress default HTML output |
| `--morelevels` | | Use 70-character grayscale ramp instead of 10 |

## License

GPLv3
