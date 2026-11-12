"""Builds data/flags.json: every flag as SVG text, plus names, capitals, regions,
difficulty tiers and a list of look-alike flags for each.

Inputs:  data/countries.txt, data/territories.txt, data/italian.txt, vendor/flag-icons
Needs:   numpy, playwright (with a Chromium/Chrome browser) to rasterise the SVGs
         so their colours and layouts can be compared.
"""
import asyncio, json, re
from pathlib import Path
import numpy as np
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
import os
LAUNCH = {'executable_path': os.environ['CHROME']} if os.environ.get('CHROME') else {}
DATA, SVG_DIR = ROOT / 'data', ROOT / 'vendor/flag-icons/flags/4x3'

def rows(name):
    # Each line: CODE|Name|Capital|Region|tier   (tier 1 = very well known ... 5 = obscure)
    return [l.rstrip('\n').split('|') for l in open(DATA / name, encoding='utf-8') if l.strip()]

italian = {r[0]: (r[1], r[2]) for r in rows('italian.txt')}
flags = []
for is_territory, fname in [(0, 'countries.txt'), (1, 'territories.txt')]:
    for code, name, capital, region, tier in rows(fname):
        svg = (SVG_DIR / f'{code.lower()}.svg').read_text(encoding='utf-8')
        svg = re.sub(r'<\?xml.*?\?>|<!--.*?-->', '', svg, flags=re.S)       # strip XML header and comments
        svg = re.sub(r'<script.*?</script>', '', svg, flags=re.S | re.I)   # never ship scripts
        svg = re.sub(r'\s+', ' ', svg).replace('> <', '><').strip()      # light minification
        entry = dict(c=code, n=name, cap=capital, r=region, t=int(tier),
                     ni=italian[code][0], capi=italian[code][1], svg=svg)
        if is_territory:
            entry['x'] = 1
        flags.append(entry)

async def rasterise(svgs):
    """Draw each SVG at 32x24 px in a headless browser and return the pixels."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(**LAUNCH)
        page = await browser.new_page()
        await page.set_content('<canvas id=c width=32 height=24></canvas>')
        pixels = await page.evaluate('''async (svgs) => {
          const c = document.getElementById('c').getContext('2d'), out = [];
          for (const s of svgs) {
            const img = new Image();
            img.src = URL.createObjectURL(new Blob([s], {type: 'image/svg+xml'}));
            await img.decode().catch(() => {});
            c.fillStyle = '#fff'; c.fillRect(0, 0, 32, 24); c.drawImage(img, 0, 0, 32, 24);
            out.push(Array.from(c.getImageData(0, 0, 32, 24).data));
          }
          return out;
        }''', svgs)
        await browser.close()
        return pixels

pixels = asyncio.run(rasterise([f['svg'] for f in flags]))

# Two features per flag: the small image itself, and a 64-bin colour histogram.
features = {}
for f, px in zip(flags, pixels):
    rgb = np.array(px, float).reshape(24, 32, 4)[..., :3]
    q = (rgb // 64).astype(int)
    hist = np.bincount((q[..., 0] * 16 + q[..., 1] * 4 + q[..., 2]).ravel(), minlength=64) / q[..., 0].size
    features[f['c']] = (rgb / 255, hist)

# Look-alikes: smallest combined colour + layout difference (mirror images count as similar too).
for f in flags:
    img1, h1 = features[f['c']]
    scores = []
    for g in flags:
        if g is f:
            continue
        img2, h2 = features[g['c']]
        layout = min(np.abs(img1 - img2).mean(), np.abs(img1 - img2[:, ::-1]).mean())
        scores.append((np.abs(h1 - h2).sum() * 0.5 + layout * 2, g['c']))
    f['sim'] = [c for _, c in sorted(scores)[:14]]

json.dump(flags, open(DATA / 'flags.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(f'{len(flags)} flags written to data/flags.json')
