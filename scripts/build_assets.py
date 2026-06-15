#!/usr/bin/env python3
"""
Build the Atelier case-study image set from the source export.

The source ("Atelier Cursor + n8n .pdf") is a single 1440 x 14918 page —
the full landing design exported from Figma. The real assets are the
*embedded* raster images (app screenshots, photoreal renders, n8n
workflow shots). This script:

  1. extracts the curated embedded images (by PDF xref),
  2. crops the hero / interlude / OG visuals,
  3. downscales + encodes each as WebP (primary) + JPG (fallback),
  4. writes a manifest.json.

Usage:
    python3 scripts/build_assets.py
    [--pdf "Atelier Cursor + n8n .pdf"] [--max-width 2000]
    [--webp-quality 82] [--jpg-quality 86]

Requires: PyMuPDF (fitz) + Pillow  ->  pip3 install --user PyMuPDF Pillow
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
    from PIL import Image
except ImportError as e:  # pragma: no cover
    sys.stderr.write(
        f"missing dependency: {e}\n"
        "install with:  pip3 install --user PyMuPDF Pillow\n"
    )
    sys.exit(1)


# ── curation ─────────────────────────────────────────────────────────────
# Full embedded screenshots (no crop). name -> xref
SHOTS = {
    "ap-landing":    679,   # "Your room, reimagined in 90 seconds" — brand landing
    "ap-foursteps":  459,   # "Four steps. No designer required."
    "ap-cards":      427,   # three shoppable room directions
    "ap-upload":     603,   # design my room — upload + vibe + budget
    "ap-processing": 449,   # "Designing your room" — pipeline at work
    "ap-redesign":   453,   # one photo -> one designer-grade redesign
    "ap-faq":        423,   # the honest FAQ
    "rn-scandi":     441,   # Minimalist, Scandinavian, Serene + shopping list
    "rn-serene":     599,   # warm render + matched products
    "wf-canvas":     645,   # n8n orchestration canvas (webhook -> fan-out)
    "wf-prep":       705,   # node: prep input + json
    "wf-brief":      655,   # node: Gemini analyze + brief
    "wf-products":   611,   # node: match real products (SerpAPI)
}

# Cropped visuals. name -> (xref, (x0,y0,x1,y1) as ratios, target_width)
CROPS = {
    "interlude-before":  (603, (0.482, 0.286, 0.805, 0.750), 1400),  # empty room
    "interlude-after":   (599, (0.286, 0.075, 0.612, 0.598), 1500),  # finished render (tightened)
}

# The hero + OG image are produced from a generated, brand-matched interior
# render (assets/hero-source.png) rather than a crop of the source PDF, so the
# full-bleed hero is high-resolution. name -> (target_width, is_3x2_og)
HERO_SOURCE = "assets/hero-source.png"

# Stills lifted from the working-app screen recording (public/atelier-demo.mp4) —
# real moments the static design can't show: the live product match and the
# full styled result. name -> (timestamp_seconds, target_width, bottom_trim)
VIDEO = "public/atelier-demo.mp4"
VIDEO_STILLS = {
    "rn-cozy": (138, 1440, 0.035),  # "Retro, Elegant, Cozy" — full styled result
    "wf-serp": (152, 1440, 0.035),  # live Google Shopping product match (SerpAPI proof)
}


def encode(img: Image.Image, stem: Path, max_w: int, wq: int, jq: int,
           jpg_only: bool = False) -> None:
    if max(img.size) > max_w:
        s = max_w / max(img.size)
        img = img.resize((int(img.size[0] * s), int(img.size[1] * s)), Image.LANCZOS)
    elif img.size[0] < max_w:  # gentle upscale for the full-bleed hero crops
        s = max_w / img.size[0]
        img = img.resize((int(img.size[0] * s), int(img.size[1] * s)), Image.LANCZOS)
    img = img.convert("RGB")
    img.save(stem.with_suffix(".jpg"), "JPEG", quality=jq, optimize=True, progressive=True)
    if not jpg_only:
        img.save(stem.with_suffix(".webp"), "WEBP", quality=wq, method=6)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pdf", default="Atelier Cursor + n8n .pdf")
    p.add_argument("--out", default="public")
    p.add_argument("--max-width", type=int, default=2000)
    p.add_argument("--webp-quality", type=int, default=82)
    p.add_argument("--jpg-quality", type=int, default=86)
    args = p.parse_args()

    pdf = Path(args.pdf).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    root = Path(".").resolve()
    if not pdf.exists():
        sys.stderr.write(f"error: PDF not found at {pdf}\n")
        sys.exit(1)
    out.mkdir(parents=True, exist_ok=True)

    print(f"→ opening {pdf.name}")
    doc = fitz.open(pdf)
    page = doc[0]
    cache: dict[int, Image.Image] = {}

    def load(xref: int) -> Image.Image:
        if xref not in cache:
            info = doc.extract_image(xref)
            cache[xref] = Image.open(__import__("io").BytesIO(info["image"]))
        return cache[xref]

    manifest_shots = []
    for name, xref in SHOTS.items():
        im = load(xref)
        encode(im, out / name, args.max_width, args.webp_quality, args.jpg_quality)
        manifest_shots.append(name)
        print(f"   shot  {name:<14} ← x{xref}  {im.size[0]}x{im.size[1]}")

    for name, (xref, (rx0, ry0, rx1, ry1), tw) in CROPS.items():
        im = load(xref)
        W, H = im.size
        box = (int(rx0 * W), int(ry0 * H), int(rx1 * W), int(ry1 * H))
        crop = im.crop(box)
        encode(crop, out / name, tw, args.webp_quality, args.jpg_quality)
        print(f"   crop  {name:<14} ← x{xref}  {crop.size[0]}x{crop.size[1]} → {tw}px")

    doc.close()

    # hero + OG from the generated brand render
    hero_src = Path(HERO_SOURCE)
    if hero_src.exists():
        h = Image.open(hero_src).convert("RGB")
        encode(h, root / "hero", 2400, args.webp_quality, 90, jpg_only=True)
        # OG: center-crop to 3:2
        W, H = h.size
        target = W / 1.5
        if H > target:
            off = int((H - target) / 2)
            og = h.crop((0, off, W, off + int(target)))
        else:
            og = h
        encode(og, root / "og-cover", 1536, args.webp_quality, 88, jpg_only=True)
        print(f"   hero  ← {HERO_SOURCE}  {h.size[0]}x{h.size[1]} → 2400px (+ og 3:2)")
    else:
        sys.stderr.write(f"note: {HERO_SOURCE} missing — hero.jpg / og-cover.jpg not rebuilt\n")

    # stills pulled from the demo recording (needs any ffmpeg; imageio-ffmpeg bundles one)
    stills_done = []
    video = Path(VIDEO)
    if video.exists():
        ff = None
        try:
            import imageio_ffmpeg
            ff = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            sys.stderr.write("note: imageio-ffmpeg missing — video stills not rebuilt "
                             "(pip3 install --user imageio-ffmpeg)\n")
        if ff:
            import subprocess, tempfile
            for name, (t, tw, trim) in VIDEO_STILLS.items():
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
                subprocess.run([ff, "-y", "-ss", str(t), "-i", str(video),
                                "-frames:v", "1", tmp],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                fr = Image.open(tmp).convert("RGB")
                W, H = fr.size
                fr = fr.crop((0, 0, W, int(H * (1 - trim))))
                encode(fr, out / name, tw, args.webp_quality, args.jpg_quality)
                Path(tmp).unlink(missing_ok=True)
                stills_done.append(name)
                print(f"   still {name:<14} ← {video.name} @ {t}s  → {tw}px")
    else:
        sys.stderr.write(f"note: {VIDEO} missing — video stills not rebuilt\n")

    manifest = {
        "source": pdf.name,
        "title": "Atelier — AI Interior Design",
        "shots": manifest_shots,
        "crops": list(CROPS.keys()),
        "video_stills": stills_done,
        "max_width": args.max_width,
        "webp_quality": args.webp_quality,
        "jpg_quality": args.jpg_quality,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"✓ done — {len(manifest_shots)} shots + {len(CROPS)} crops "
          f"+ {len(stills_done)} video stills → {out}")


if __name__ == "__main__":
    main()
