# python-image-ascii v2
# Convert images to ASCII art with optional color, block characters, and HTML output.

import sys
import shutil
import argparse
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

# grayscale ramps from http://paulbourke.net/dataformats/asciiart/
GSCALE_70 = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
GSCALE_10 = "@%#*+=-:. "
GSCALE_BLOCK = " ░▒▓█"


def load_image(source):
    """Load image from a local path or URL."""
    if source.startswith("http://") or source.startswith("https://"):
        try:
            resp = requests.get(source, timeout=15, headers={"User-Agent": "python-image-ascii"})
            resp.raise_for_status()
            return Image.open(BytesIO(resp.content))
        except Exception as e:
            print(f"Error fetching URL: {e}")
            sys.exit(1)
    return Image.open(source)


def get_average_l(image):
    """Return average grayscale value for a PIL Image tile."""
    im = np.array(image)
    return np.average(im.reshape(im.shape[0] * im.shape[1]))


def get_average_color(image):
    """Return average RGB color for a PIL Image tile."""
    im = np.array(image)
    pixels = im.reshape(-1, im.shape[-1]) if im.ndim == 3 else None
    if pixels is None:
        avg = int(np.average(im))
        return (avg, avg, avg)
    return tuple(int(x) for x in np.mean(pixels, axis=0)[:3])


def convert_image_to_ascii(image, cols, scale, ramp):
    """Convert a PIL Image to a list of (char, rgb) tuples per row."""
    gray = image.convert("L")
    color = image.convert("RGB")
    W, H = image.size
    w = W / cols
    h = w / scale
    rows = int(H / h)

    if cols > W or rows > H:
        print("Image too small for specified cols!")
        sys.exit(1)

    ramp_len = len(ramp) - 1
    result = []

    for j in range(rows):
        y1 = int(j * h)
        y2 = H if j == rows - 1 else int((j + 1) * h)
        row = []
        for i in range(cols):
            x1 = int(i * w)
            x2 = W if i == cols - 1 else int((i + 1) * w)

            gray_tile = gray.crop((x1, y1, x2, y2))
            color_tile = color.crop((x1, y1, x2, y2))

            avg = int(get_average_l(gray_tile))
            rgb = get_average_color(color_tile)
            char = ramp[int((avg * ramp_len) / 255)]
            row.append((char, rgb))
        result.append(row)

    return result


def render_terminal(rows, use_color):
    """Print ASCII art to terminal, optionally with TrueColor ANSI."""
    lines = []
    for row in rows:
        if use_color:
            line = "".join(f"\033[38;2;{r};{g};{b}m{ch}\033[0m" for ch, (r, g, b) in row)
        else:
            line = "".join(ch for ch, _ in row)
        lines.append(line)
    print("\n".join(lines))


def render_file(rows, out_path):
    """Write plain ASCII art to a text file."""
    with open(out_path, "w") as f:
        for row in rows:
            f.write("".join(ch for ch, _ in row) + "\n")
    print(f"Art written to {out_path}")


def render_html(rows, html_path):
    """Write colored ASCII art to an HTML file."""
    chars = []
    for row in rows:
        for ch, (r, g, b) in row:
            escaped = ch.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            chars.append(f'<span style="color:rgb({r},{g},{b})">{escaped}</span>')
        chars.append("\n")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ASCII Art</title>
<style>
body {{ background: #1a1a1a; margin: 0; padding: 20px; }}
pre {{ font-family: "Courier New", monospace; font-size: 8px; line-height: 8px; letter-spacing: 1px; }}
</style>
</head>
<body>
<pre>{"".join(chars)}</pre>
</body>
</html>"""

    with open(html_path, "w") as f:
        f.write(html)
    print(f"HTML written to {html_path}")


def render_image(rows, image_path):
    """Render colored ASCII art to a PNG or JPEG file using Pillow."""
    font = ImageFont.load_default()
    bbox = font.getbbox("A")
    char_w = bbox[2] - bbox[0]
    char_h = bbox[3] - bbox[1]

    cols = len(rows[0]) if rows else 0
    num_rows = len(rows)
    img_w = cols * char_w
    img_h = num_rows * char_h

    img = Image.new("RGB", (img_w, img_h), color=(26, 26, 26))
    draw = ImageDraw.Draw(img)

    for j, row in enumerate(rows):
        for i, (ch, (r, g, b)) in enumerate(row):
            draw.text((i * char_w, j * char_h), ch, fill=(r, g, b), font=font)

    img.save(image_path)
    print(f"Image written to {image_path}")


PRESETS = {
    "hd":      {"cols": 300, "block": True,  "no_color": False, "morelevels": False},
    "retro":   {"cols": 80,  "block": False, "no_color": True,  "morelevels": True},
    "minimal": {"cols": 60,  "block": False, "no_color": True,  "morelevels": False},
}


def main():
    parser = argparse.ArgumentParser(description="Convert images to ASCII art.")
    parser.add_argument("file", nargs="?",
                        help="Input image path or URL")
    parser.add_argument("--file", dest="file_flag",
                        help=argparse.SUPPRESS)
    parser.add_argument("-o", "--out", dest="out_file",
                        help="Write plain ASCII to a text file")
    parser.add_argument("--html", dest="html_file",
                        help="Override default HTML output path")
    parser.add_argument("--no-html", dest="no_html", action="store_true",
                        help="Suppress default HTML output")
    parser.add_argument("--image", dest="image_file",
                        help="Render ASCII art to a PNG or JPEG file")
    parser.add_argument("-c", "--cols", type=int,
                        help="Column width (default: terminal width)")
    parser.add_argument("-s", "--scale", type=float, default=0.43,
                        help="Aspect ratio scale (default: 0.43)")
    parser.add_argument("--no-color", dest="no_color", action="store_true",
                        help="Disable TrueColor ANSI output")
    parser.add_argument("-b", "--block", action="store_true",
                        help="Use block characters instead of ASCII")
    parser.add_argument("--morelevels", action="store_true",
                        help="Use 70-character grayscale ramp")
    parser.add_argument("-i", "--invert", action="store_true",
                        help="Invert brightness mapping")
    parser.add_argument("-p", "--preset", choices=PRESETS.keys(),
                        help="Use a preset (hd, retro, minimal)")

    args = parser.parse_args()

    # resolve file from positional or --file flag
    img_file = args.file or args.file_flag
    if not img_file:
        parser.error("please provide an image path or URL")

    # apply preset defaults (explicit flags override)
    if args.preset:
        p = PRESETS[args.preset]
        if args.cols is None:
            args.cols = p["cols"]
        if not args.block:
            args.block = p["block"]
        if not args.no_color:
            args.no_color = p["no_color"]
        if not args.morelevels:
            args.morelevels = p["morelevels"]

    # determine column width
    if args.cols:
        cols = args.cols
    else:
        cols = shutil.get_terminal_size().columns

    # pick character ramp
    if args.block:
        ramp = GSCALE_BLOCK
    elif args.morelevels:
        ramp = GSCALE_70
    else:
        ramp = GSCALE_10

    if args.invert:
        ramp = ramp[::-1]

    # load and convert
    image = load_image(img_file)
    rows = convert_image_to_ascii(image, cols, args.scale, ramp)

    # HTML output (default unless --no-html)
    if not args.no_html:
        if args.html_file:
            html_path = args.html_file
        elif img_file.startswith("http://") or img_file.startswith("https://"):
            html_path = "output.html"
        else:
            html_path = str(Path(img_file).with_suffix(".html"))
        render_html(rows, html_path)

    # optional image export
    if args.image_file:
        render_image(rows, args.image_file)

    # terminal or text file output
    if args.out_file:
        render_file(rows, args.out_file)
    else:
        render_terminal(rows, not args.no_color)


if __name__ == "__main__":
    main()
