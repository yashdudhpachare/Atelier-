# Atelier — AI Interior Design

A standalone case-study page for **Atelier**, a solo-built validation MVP that
turns a phone photo of any room into a magazine-grade redesign *and* a shoppable
list of real products — orchestrated end-to-end with **n8n**, **Next.js**,
**GPT-4o** and **Imagen 3**.

Single-file static site — vanilla HTML, CSS and JS (no build step), matching the
rest of the portfolio (see `Farmly`, `WC 1`, etc.).

## Run locally

```bash
cd "Atelier (Reimagined you room) n8n + cursor"
python3 -m http.server 5173
# open http://localhost:5173
```

## Structure

```
.
├── index.html                  single-file case study
├── hero.jpg                    full-bleed hero (generated brand render, 2400px)
├── og-cover.jpg                social-share image (3:2 from the hero)
├── assets/hero-source.png      generated 1536×1024 hero source
├── public/
│   ├── ap-*.jpg / .webp        the live app screens (landing, four steps, …)
│   ├── rn-*.jpg / .webp        photoreal room renders + shopping lists
│   │                           (rn-cozy is lifted from the demo recording)
│   ├── wf-*.jpg / .webp        the n8n workflow canvas + node detail shots
│   │                           (wf-serp is the live product match from the demo)
│   ├── interlude-*.jpg/.webp   before / after full-bleed photo breaks
│   ├── atelier-demo.mp4        web-compressed app demo (1440×826, ~4.7 MB) — embedded inline
│   ├── demo-poster.jpg         poster frame for the inline player
│   └── manifest.json
├── scripts/build_assets.py     rebuilds every image from the sources
├── Atelier Cursor + n8n .pdf   source (a single 1440×14918 Figma export)
└── App working video.mov       original 1.4 GB screen recording (kept as master)
```

## Source assets

The page's visuals come from the **`Atelier Cursor + n8n .pdf`**, which is the
full landing design exported from Figma as one tall page. The real assets are the
*embedded* raster images (app screenshots, photoreal renders, n8n workflow
shots); the diagrams (pipeline, engine, architecture) are rebuilt natively in
HTML/CSS rather than pasted as images.

Original Figma file:
[Room Designer — Atelier Landing](https://www.figma.com/design/PsOlyv5aP3XMTi30ZDoPbv/Room-Designer-%E2%80%94-Atelier-Landing).

## Re-extracting / tuning images

If the source PDF is updated, or you want different crops / quality:

```bash
python3 scripts/build_assets.py \
  --pdf "Atelier Cursor + n8n .pdf" \
  --out public \
  --max-width 2000 --webp-quality 82 --jpg-quality 86
```

(Requires `PyMuPDF` and `Pillow` — `pip3 install --user PyMuPDF Pillow`.)
Curated image xrefs and crop boxes live at the top of `scripts/build_assets.py`.
The hero is produced from `assets/hero-source.png` (a generated, brand-matched
interior render), not a PDF crop, so the full-bleed hero stays high-resolution.

## Re-compressing the demo video

The page embeds a web-friendly `public/atelier-demo.mp4` compressed from the
1.4 GB master `App working video.mov` (3456×1982 · 60 fps · ~38 Mbps → 1440×826 ·
30 fps · ~4.7 MB). To regenerate it (any ffmpeg works; `imageio-ffmpeg` bundles one):

```bash
pip3 install --user imageio-ffmpeg
FF=$(python3 -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())")
"$FF" -y -i "App working video.mov" \
  -vf "scale=1440:-2,fps=30" -c:v libx264 -crf 30 -preset veryfast \
  -pix_fmt yuv420p -movflags +faststart -an "public/atelier-demo.mp4"
# poster frame:
"$FF" -y -ss 3 -i "public/atelier-demo.mp4" -frames:v 1 -vf "scale=1280:-2" -q:v 4 "public/demo-poster.jpg"
```

## Page anatomy

Fixed section rail + scroll progress · full-bleed hero · *Why* · *How it works*
(four-step flow) · *Pipeline* (3 AI stages with live I/O JSON) · *Engine* (the
8-node n8n workflow) · *Stack & architecture* · *Results* gallery · closing.
Galleries compose into static, scroll-driven and swipe segments and open into a
full-screen lightbox + slide drawer.
