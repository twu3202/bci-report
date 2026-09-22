#!/usr/bin/env python3
"""Regenerate the brand raster assets from the name in src/data/site.ts.

The wordmark, page titles, canonical URLs, robots.txt and sitemap.xml all follow
`site.name` / `site.origin` automatically. These three files cannot — the name is
baked into pixels — so they are generated here instead of being hand-made once
and then quietly going stale after a rename.

Outputs: public/og.png (1200x630 share card), public/favicon.ico (16/32/48),
public/apple-touch-icon.png (180) and public/logo.png (512, for places that need
a raster, such as the Hugging Face dataset card).

The mark itself is public/logo.svg: a top-down head with five electrode sites,
generated in Recraft (V4.1 Vector) and cleaned by hand — metadata and background
removed, cropped to the mark. logo-dark.svg and favicon.svg are the same paths
with dark-background colours; change all three together.

Every raster here sits on a paper-coloured tile. The mark is dark ink on
transparent, which disappears on a dark tab bar, a dark search result or an iOS
home screen.

Needs Pillow (on this Mac it is in the system interpreter, not the project venv)
and the site's node_modules, for sharp:
    python3 site/scripts/generate-brand-assets.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - environment guidance, not logic
    sys.exit("Pillow is required: python3 -m pip install --user Pillow")

SITE = Path(__file__).resolve().parents[1]
PUBLIC = SITE / "public"
# Warm palette, matching src/styles/global.css. Keep the two in step: the share
# card is the only place these values are duplicated, because PNG has no
# stylesheet to read them from.
INK = (36, 28, 21)
ACCENT = (179, 69, 14)
MUTED = (119, 102, 90)
LINE = (212, 197, 176)
PAPER = (251, 247, 242)
WASH = (251, 234, 219)

# Serif for the name and headline, sans for labels — the same split the site
# uses. Falls back silently on a machine without these faces.
FONTS = {
    ("serif", True): "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    ("serif", False): "/System/Library/Fonts/Supplemental/Georgia.ttf",
    ("sans", True): "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ("sans", False): "/System/Library/Fonts/Supplemental/Arial.ttf",
}


def font(size: int, bold: bool = False, family: str = "sans"):
    try:
        return ImageFont.truetype(FONTS[(family, bold)], size)
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


_LOGO: Image.Image | None = None


def logo(px: int) -> Image.Image:
    """public/logo.svg on transparent, rendered once at 1024 by sharp, then downscaled."""
    global _LOGO
    if _LOGO is None:
        png = subprocess.run(["node", str(SITE / "scripts/render-logo.mjs"), "1024"],
                             check=True, capture_output=True, cwd=SITE).stdout
        _LOGO = Image.open(io.BytesIO(png)).convert("RGBA")
    return _LOGO.resize((px, px), Image.LANCZOS)


def mark(px: int, rounded: bool = True, scale: float = 0.8) -> Image.Image:
    """The logo centred on a paper tile, so it survives a dark background."""
    s = px * 8  # supersample, then downscale, so small sizes stay clean
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.2), fill=PAPER + (255,))
    else:
        d.rectangle([0, 0, s - 1, s - 1], fill=PAPER + (255,))
    inner = int(s * scale)
    img.alpha_composite(logo(inner), ((s - inner) // 2, (s - inner) // 2))
    return img.resize((px, px), Image.LANCZOS)


def share_card(name: str, stage: str, stats: list[tuple[str, str]]) -> Image.Image:
    img = Image.new("RGB", (1200, 630), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 10, 630], fill=ACCENT)
    wordmark = font(38, True, "serif")
    head = logo(64)
    img.paste(head, (72, 64), head)
    d.text((152, 96), name, font=wordmark, fill=INK, anchor="lm")

    badge_x = 152 + d.textlength(name, font=wordmark) + 20
    label = stage.upper()
    badge_w = int(d.textlength(label, font=font(17, True))) + 36
    d.rounded_rectangle([badge_x, 82, badge_x + badge_w, 112], 2, fill=WASH)
    d.text((badge_x + badge_w / 2, 97), label, font=font(17, True), fill=ACCENT, anchor="mm")

    headline = font(70, True, "serif")
    d.text((72, 214), "Every EEG score, with the", font=headline, fill=INK, anchor="lt")
    d.text((72, 300), "protocol that produced it.", font=headline, fill=INK, anchor="lt")
    d.text((72, 418), "Cohort, electrode count, training budget and chance",
           font=font(30), fill=MUTED, anchor="lt")
    d.text((72, 460), "level travel with every number.",
           font=font(30), fill=MUTED, anchor="lt")

    d.line([72, 528, 1128, 528], fill=LINE, width=2)
    number_font, label_font, x = font(38, True), font(24), 72
    for value, caption in stats:
        d.text((x, 556), value, font=number_font, fill=ACCENT, anchor="lt")
        x += d.textlength(value, font=number_font) + 10
        d.text((x, 572), caption, font=label_font, fill=MUTED, anchor="lt")
        x += d.textlength(caption, font=label_font) + 46
    return img


def main() -> None:
    config = read_site_config()
    name = config["name"]
    stats = [("8", "protocols"), ("7", "datasets"), ("39", "comparisons"), ("9", "methods")]

    share_card(name, config["stage"], stats).save(PUBLIC / "og.png", "PNG", optimize=True)
    # A 16 px icon needs the mark nearly edge to edge; the tile is only a backing.
    mark(256, scale=0.86).save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    # iOS masks its own rounded corners and adds no background: full-bleed paper.
    mark(180, rounded=False, scale=0.7).save(PUBLIC / "apple-touch-icon.png", "PNG", optimize=True)
    mark(512, scale=0.76).save(PUBLIC / "logo.png", "PNG", optimize=True)
    print(f"Regenerated og.png, favicon.ico, apple-touch-icon.png and logo.png for {name!r}.")
    print("logo.svg, logo-dark.svg and favicon.svg are the vector sources — keep them in step.")


if __name__ == "__main__":
    main()
