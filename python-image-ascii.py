# python-image-ascii v2
# Convert images to ASCII art with optional color, block characters, and HTML output.

import sys
import shutil
import argparse
from io import BytesIO

import numpy as np
import requests
from PIL import Image

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


def main():
    parser = argparse.ArgumentParser(description="Convert images to ASCII art.")
    parser.add_argument("--file", dest="img_file", required=True,
                        help="Input image path or URL")
    parser.add_argument("--out", dest="out_file",
                        help="Write plain ASCII to a text file")
    parser.add_argument("--html", dest="html_file",
                        help="Write colored ASCII to an HTML file")
    parser.add_argument("--cols", type=int,
                        help="Column width (default: terminal width)")
    parser.add_argument("--scale", type=float, default=0.43,
                        help="Aspect ratio scale (default: 0.43)")
    parser.add_argument("--color", action="store_true",
                        help="Enable TrueColor ANSI output in terminal")
    parser.add_argument("--block", action="store_true",
                        help="Use block characters instead of ASCII")
    parser.add_argument("--morelevels", action="store_true",
                        help="Use 70-character grayscale ramp")
    parser.add_argument("--invert", action="store_true",
                        help="Invert brightness mapping")

    args = parser.parse_args()

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
    image = load_image(args.img_file)
    rows = convert_image_to_ascii(image, cols, args.scale, ramp)

    # output
    if args.html_file:
        render_html(rows, args.html_file)
    elif args.out_file:
        render_file(rows, args.out_file)
    else:
        render_terminal(rows, args.color)


if __name__ == "__main__":
    main()
