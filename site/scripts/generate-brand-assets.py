#!/usr/bin/env python3
"""Regenerate the brand raster assets from the name in src/data/site.ts.

The wordmark, page titles, canonical URLs, robots.txt and sitemap.xml all follow
`site.name` / `site.origin` automatically. These three files cannot — the name is
baked into pixels — so they are generated here instead of being hand-made once
and then quietly going stale after a rename.

Outputs: public/og.png (1200x630 share card), public/favicon.ico (16/32/48),
public/apple-touch-icon.png (180). favicon.svg is hand-maintained; update the
letter there too if the name's first letter changes.

Needs Pillow. On this Mac it is in the system interpreter, not the project venv:
    python3 site/scripts/generate-brand-assets.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - environment guidance, not logic
    sys.exit("Pillow is required: python3 -m pip install --user Pillow")

SITE = Path(__file__).resolve().parents[1]
PUBLIC = SITE / "public"
INK, BLUE, MUTED, LINE = (23, 33, 59), (20, 59, 209), (98, 109, 131), (224, 229, 238)
FONTS = {
    True: "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    False: "/System/Library/Fonts/Supplemental/Arial.ttf",
}


def font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype(FONTS[bold], size)
    except OSError:
        return ImageFont.load_default(size)


def read_site_config() -> dict[str, str]:
    """Pull name/stage out of site.ts. Fails loudly rather than guessing."""
    source = (SITE / "src/data/site.ts").read_text(encoding="utf-8")
    found = {}
    for key in ("name", "stage"):
        match = re.search(rf"^\s*{key}:\s*'([^']+)'", source, re.MULTILINE)
        if not match:
            sys.exit(f"Could not read `{key}` from src/data/site.ts — update this script.")
        found[key] = match.group(1)
    return found


def mark(px: int, letter: str) -> Image.Image:
    """The rounded blue square with the name's initial, as in favicon.svg."""
    s = px * 8  # supersample, then downscale, so small sizes stay clean
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 9 / 40), fill=BLUE + (255,))
    d.text((s / 2, s * 0.52), letter, font=font(int(s * 0.66), True),
           fill=(255, 255, 255, 255), anchor="mm")
    return img.resize((px, px), Image.LANCZOS)


def share_card(name: str, stage: str, stats: list[tuple[str, str]]) -> Image.Image:
    img = Image.new("RGB", (1200, 630), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 10, 630], fill=BLUE)
    img.paste(mark(64, name[0]), (72, 64), mark(64, name[0]))
    d.text((152, 96), name, font=font(40, True), fill=INK, anchor="lm")

    badge_x = 152 + d.textlength(name, font=font(40, True)) + 20
    label = stage.upper()
    badge_w = int(d.textlength(label, font=font(17, True))) + 36
    d.rounded_rectangle([badge_x, 82, badge_x + badge_w, 112], 8, fill=(234, 240, 255))
    d.text((badge_x + badge_w / 2, 97), label, font=font(17, True), fill=BLUE, anchor="mm")

    d.text((72, 218), "EEG models,", font=font(78, True), fill=INK, anchor="lt")
    d.text((72, 306), "measured in context.", font=font(78, True), fill=INK, anchor="lt")
    d.text((72, 418), "Every score reported with its protocol, cohort, electrode",
           font=font(30), fill=MUTED, anchor="lt")
    d.text((72, 460), "count, training budget and chance level.",
           font=font(30), fill=MUTED, anchor="lt")

    d.line([72, 528, 1128, 528], fill=LINE, width=2)
    number_font, label_font, x = font(38, True), font(24), 72
    for value, caption in stats:
        d.text((x, 556), value, font=number_font, fill=BLUE, anchor="lt")
        x += d.textlength(value, font=number_font) + 10
        d.text((x, 572), caption, font=label_font, fill=MUTED, anchor="lt")
        x += d.textlength(caption, font=label_font) + 46
    return img


def main() -> None:
    config = read_site_config()
    name, letter = config["name"], config["name"][0]
    stats = [("8", "protocols"), ("7", "datasets"), ("39", "comparisons"), ("9", "methods")]

    share_card(name, config["stage"], stats).save(PUBLIC / "og.png", "PNG", optimize=True)
    mark(256, letter).save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    mark(180, letter).save(PUBLIC / "apple-touch-icon.png", "PNG", optimize=True)
    print(f"Regenerated og.png, favicon.ico and apple-touch-icon.png for {name!r}.")
    print("favicon.svg is hand-maintained — check its letter if the name changed.")


if __name__ == "__main__":
    main()
