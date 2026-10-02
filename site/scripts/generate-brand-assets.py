#!/usr/bin/env python3
"""Regenerate the brand raster assets from the name in src/data/site.ts.

The wordmark, page titles, canonical URLs, robots.txt and sitemap.xml all follow
`site.name` / `site.origin` automatically. These three files cannot — the name is
baked into pixels — so they are generated here instead of being hand-made once
and then quietly going stale after a rename.

Outputs: public/og.png (1200x630 share card), public/favicon.ico (16/32/48),
public/apple-touch-icon.png (180) and public/logo.png (512, for places that need
a raster, such as the Hugging Face dataset card).

The share card's figures are the core matrix's own counts, read from
src/data/mvp.json the way the home page's stat rail reads them, so the picture
cannot advertise a scope the page does not show. Every run records what it drew
in scripts/brand-assets.json — the SHA-256 of each file it wrote, and the card's
text and counts — and check-workbench.mjs compares the served og.png with that
record, because a text check cannot see inside a bitmap. That is how the card
kept a "Research preview" badge after the site dropped it on 2026-10-01.

The mark itself is public/logo.svg: a top-down head with five electrode sites,
generated in Recraft (V4.1 Vector) and cleaned by hand — metadata and background
removed, cropped to the mark. logo-dark.svg and favicon.svg are the same paths
with dark-background colours; change all three together.

Every raster here sits on a paper-coloured tile. The mark is dark ink on
transparent, which disappears on a dark tab bar, a dark search result or an iOS
home screen.

Needs Pillow (on this Mac it is in the system interpreter, not the project venv)
and the site's node_modules, for sharp:
    python3 site/scripts/generate-brand-assets.py          # all four rasters
    python3 site/scripts/generate-brand-assets.py og       # only the share card
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
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
MANIFEST = SITE / "scripts/brand-assets.json"
# Warm palette, matching src/styles/global.css. Keep the two in step: the share
# card is the only place these values are duplicated, because PNG has no
# stylesheet to read them from.
INK = (36, 28, 21)
ACCENT = (179, 69, 14)
MUTED = (119, 102, 90)
LINE = (212, 197, 176)
PAPER = (251, 247, 242)

# Serif for the name and headline, sans for labels — the same split the site
# uses. Falls back silently on a machine without these faces.
FONTS = {
    ("serif", True): "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    ("serif", False): "/System/Library/Fonts/Supplemental/Georgia.ttf",
    ("sans", True): "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ("sans", False): "/System/Library/Fonts/Supplemental/Arial.ttf",
}

HEADLINE = ("Every EEG score, with the", "protocol that produced it.")
DEK = ("Cohort, electrode count, training budget and chance",
       "level travel with every number.")


def font(size: int, bold: bool = False, family: str = "sans"):
    try:
        return ImageFont.truetype(FONTS[(family, bold)], size)
    except OSError:
        return ImageFont.load_default(size)


def read_site_config() -> dict[str, str]:
    """Pull name and origin out of site.ts. Fails loudly rather than guessing.

    There is no stage label to read any more: the "Research preview" badge came
    off the site on 2026-10-01, and the card follows the site.
    """
    source = (SITE / "src/data/site.ts").read_text(encoding="utf-8")
    found = {}
    for key in ("name", "origin"):
        match = re.search(rf"^\s*{key}:\s*'([^']+)'", source, re.MULTILINE)
        if not match:
            sys.exit(f"Could not read `{key}` from src/data/site.ts — update this script.")
        found[key] = match.group(1)
    return found


def core_counts() -> dict[str, int]:
    """The core matrix's counts, derived as the home page derives its stat rail."""
    data = json.loads((SITE / "src/data/mvp.json").read_text(encoding="utf-8"))
    return {
        "protocols": data["coverage"]["displayedProtocols"],
        "datasets": len({t["dataset"] for t in data["tracks"]}),
        "comparisons": data["coverage"]["displayedComparisons"],
        "methods": len({r["name"] for t in data["tracks"] for r in t["rows"]}),
    }


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


def share_card(name: str, host: str, stats: list[tuple[str, str]]) -> Image.Image:
    img = Image.new("RGB", (1200, 630), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 10, 630], fill=ACCENT)
    wordmark = font(38, True, "serif")
    head = logo(64)
    img.paste(head, (72, 64), head)
    d.text((152, 96), name, font=wordmark, fill=INK, anchor="lm")

    headline = font(70, True, "serif")
    d.text((72, 214), HEADLINE[0], font=headline, fill=INK, anchor="lt")
    d.text((72, 300), HEADLINE[1], font=headline, fill=INK, anchor="lt")
    d.text((72, 418), DEK[0], font=font(30), fill=MUTED, anchor="lt")
    d.text((72, 460), DEK[1], font=font(30), fill=MUTED, anchor="lt")

    d.line([72, 528, 1128, 528], fill=LINE, width=2)
    number_font, label_font, x = font(38, True), font(24), 72
    for value, caption in stats:
        d.text((x, 556), value, font=number_font, fill=ACCENT, anchor="lt")
        x += d.textlength(value, font=number_font) + 10
        d.text((x, 572), caption, font=label_font, fill=MUTED, anchor="lt")
        x += d.textlength(caption, font=label_font) + 46
    # The address, for link previews that show no domain of their own.
    d.text((1128, 572), host, font=label_font, fill=MUTED, anchor="rt")
    return img


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


TARGETS = ("og", "favicon", "touch", "logo")


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate the brand rasters.")
    parser.add_argument("targets", nargs="*", choices=TARGETS,
                        help="which rasters to write (default: all four)")
    targets = set(parser.parse_args().targets or TARGETS)

    config = read_site_config()
    name = config["name"]
    host = config["origin"].split("://", 1)[-1]
    counts = core_counts()
    stats = [(str(counts[k]), k) for k in ("protocols", "datasets", "comparisons", "methods")]

    try:
        record = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except FileNotFoundError:
        record = {}
    written = []
    if "og" in targets:
        share_card(name, host, stats).save(PUBLIC / "og.png", "PNG", optimize=True)
        record["og.png"] = {
            "sha256": sha256(PUBLIC / "og.png"), "width": 1200, "height": 630,
            "text": [name, *HEADLINE, *DEK, *(f"{v} {c}" for v, c in stats), host],
            "counts": counts,
        }
        written.append("og.png")
    # A 16 px icon needs the mark nearly edge to edge; the tile is only a backing.
    if "favicon" in targets:
        mark(256, scale=0.86).save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
        record["favicon.ico"] = {"sha256": sha256(PUBLIC / "favicon.ico")}
        written.append("favicon.ico")
    # iOS masks its own rounded corners and adds no background: full-bleed paper.
    if "touch" in targets:
        mark(180, rounded=False, scale=0.7).save(PUBLIC / "apple-touch-icon.png", "PNG", optimize=True)
        record["apple-touch-icon.png"] = {"sha256": sha256(PUBLIC / "apple-touch-icon.png")}
        written.append("apple-touch-icon.png")
    if "logo" in targets:
        mark(512, scale=0.76).save(PUBLIC / "logo.png", "PNG", optimize=True)
        record["logo.png"] = {"sha256": sha256(PUBLIC / "logo.png")}
        written.append("logo.png")
    MANIFEST.write_text(json.dumps(dict(sorted(record.items())), indent=2) + "\n", encoding="utf-8")
    print(f"Regenerated {', '.join(written)} for {name!r}; recorded in {MANIFEST.relative_to(SITE)}.")
    print("logo.svg, logo-dark.svg and favicon.svg are the vector sources — keep them in step.")


if __name__ == "__main__":
    main()
