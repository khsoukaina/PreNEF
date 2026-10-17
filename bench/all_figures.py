#!/usr/bin/env python3
"""Put every paper figure into ONE overview image (contact sheet), with a label above each figure.

  python3 bench/all_figures.py                                   # all campaigns/*/paper/*.png
  python3 bench/all_figures.py --campaigns final3,qos,sweep,ablation --cols 2 --out campaigns/all_figures.png

Also writes the same figures as a multi-page PDF (one figure per page) next to the PNG.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ["fig1", "fig2", "fig3", "fig4", "fig5", "figH", "figQ1", "figQ2", "figQ3", "figQ4", "figC", "figA", "figB",
         "figM1", "figM2", "figM3", "figM4", "figS1"]


def font(size):
    for f in ("DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rank(path):
    name = os.path.basename(path)
    for i, p in enumerate(ORDER):
        if name.startswith(p + "_") or name.startswith(p + "."):
            return (i, name)
    return (len(ORDER), name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaigns", default="", help="comma list of campaign names under campaigns/ (default: all)")
    ap.add_argument("--exclude", default="", help="comma list of name prefixes to skip, e.g. figS1,figQ4")
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--tile-width", type=int, default=1600, help="pixel width of each figure in the sheet")
    ap.add_argument("--out", default=os.path.join(ROOT, "campaigns", "all_figures.png"))
    a = ap.parse_args()
    names = [c for c in a.campaigns.split(",") if c] or sorted(
        os.path.basename(os.path.dirname(d)) for d in glob.glob(os.path.join(ROOT, "campaigns", "*", "paper")))
    figs = []
    for c in names:
        skip = tuple(x for x in a.exclude.split(",") if x)
        pngs = [p for p in glob.glob(os.path.join(ROOT, "campaigns", c, "paper", "*.png"))
                if not (skip and os.path.basename(p).startswith(skip))]
        figs += [(c, p) for p in sorted(pngs, key=rank)]
    if not figs:
        print("no figures found under campaigns/*/paper/ - generate them first")
        return 1
    W, label_h, pad = a.tile_width, 70, 40
    f_lab, f_title = font(34), font(56)
    tiles = []
    for c, p in figs:
        im = Image.open(p).convert("RGB")
        im = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
        tiles.append((f"{c} / {os.path.splitext(os.path.basename(p))[0]}", im))
    cols = max(1, a.cols)
    rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
    row_h = [label_h + max(im.height for _, im in r) + pad for r in rows]
    title_h = 110
    sheet = Image.new("RGB", (cols * W + (cols + 1) * pad, title_h + sum(row_h) + pad), "white")
    d = ImageDraw.Draw(sheet)
    d.text((pad, 30), f"PReNEF - all figures ({len(tiles)})", fill=(26, 26, 26), font=f_title)
    y = title_h
    for r, h in zip(rows, row_h):
        for k, (lab, im) in enumerate(r):
            x = pad + k * (W + pad)
            d.text((x, y + 15), lab, fill=(85, 85, 85), font=f_lab)
            sheet.paste(im, (x, y + label_h))
            d.rectangle([x - 1, y + label_h - 1, x + im.width, y + label_h + im.height], outline=(228, 228, 228), width=2)
        y += h
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    max_px = 30000
    if sheet.height > max_px:
        s = max_px / sheet.height
        sheet = sheet.resize((int(sheet.width * s), max_px), Image.LANCZOS)
    sheet.save(a.out, optimize=True)
    pdf = os.path.splitext(a.out)[0] + ".pdf"
    pages = [im for _, im in tiles]
    pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=200)
    print(f"{len(tiles)} figures from {', '.join(names)}")
    for lab, _ in tiles:
        print("  ", lab)
    print(f"wrote {a.out} ({sheet.width}x{sheet.height}px) and {pdf} (one figure per page)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
