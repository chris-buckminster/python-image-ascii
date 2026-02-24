# python-image-ascii

Command-line tool to generate ASCII art from any image. Supports color output, block characters, HTML export, and URL input.

## Installation

```bash
git clone https://github.com/chris-buckminster/python-image-ascii.git
cd python-image-ascii
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# basic terminal output (auto-sizes to terminal width)
python python-image-ascii.py --file photo.jpg

# colored output using TrueColor ANSI
python python-image-ascii.py --file photo.jpg --color

# block characters (with or without color)
python python-image-ascii.py --file photo.jpg --block
python python-image-ascii.py --file photo.jpg --block --color

# from a URL
python python-image-ascii.py --file https://example.com/image.png

# save to file
python python-image-ascii.py --file photo.jpg --out art.txt

# export as colored HTML
python python-image-ascii.py --file photo.jpg --html output.html
```

## Options

| Flag | Description |
|------|-------------|
| `--file` | Input image path or URL (required) |
| `--cols N` | Column width (default: terminal width) |
| `--color` | Enable TrueColor ANSI output |
| `--block` | Use block characters (░▒▓█) instead of ASCII |
| `--morelevels` | Use 70-character grayscale ramp instead of 10 |
| `--invert` | Invert brightness (for light-background terminals) |
| `--scale N` | Aspect ratio scale (default: 0.43) |
| `--out FILE` | Write plain ASCII to a text file |
| `--html FILE` | Write colored ASCII to an HTML file |

## License

GPLv3
