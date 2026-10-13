#!/usr/bin/env python3
"""Regenerate ``app.ico`` (the Windows installer/shortcut icon) from the Android
launcher icon.

The Android launcher is the vector ``app/src/main/res/drawable/ic_launcher.xml``:
a blue (#1E88E5) square with four white 24x24 squares on a 108x108 viewport
(top-left, top-right, bottom-left, bottom-right). This script paints the same
geometry and writes a multi-resolution Windows ``.ico`` next to itself so
``MyDroidDeck.iss`` can use it as ``SetupIconFile``.

Run from anywhere with Pillow available:

    python3 setup/windows/make-icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

# Geometry copied verbatim from ic_launcher.xml (108x108 viewport).
VIEWPORT = 108
BACKGROUND = "#1E88E5"
FOREGROUND = "#FFFFFF"
SQUARES = ((26, 26), (58, 26), (26, 58), (58, 58))
SQUARE_SIZE = 24

# Windows renders icons from a range of sizes; embed all of them.
SIZES = (16, 24, 32, 48, 64, 128, 256)
# Draw the master at 256 * 8 px so the downscaled edges stay smooth.
MASTER = 256
SUPERSAMPLE = 8

OUTPUT = Path(__file__).resolve().parent / "app.ico"


def render_master() -> Image.Image:
    """Paint the icon at high resolution, keeping every edge crisp."""
    big = MASTER * SUPERSAMPLE
    scale = big / VIEWPORT
    image = Image.new("RGBA", (big, big), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for x, y in SQUARES:
        draw.rectangle(
            (
                round(x * scale),
                round(y * scale),
                round((x + SQUARE_SIZE) * scale),
                round((y + SQUARE_SIZE) * scale),
            ),
            fill=FOREGROUND,
        )
    return image.resize((MASTER, MASTER), Image.LANCZOS)


def main() -> None:
    render_master().save(OUTPUT, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"wrote {OUTPUT} ({', '.join(f'{s}x{s}' for s in SIZES)})")


if __name__ == "__main__":
    main()
