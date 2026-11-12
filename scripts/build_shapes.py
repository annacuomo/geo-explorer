"""Builds data/shapes.json: one SVG path per country for the Shapes game (in a 100x100 box),
plus a list of similar-looking outlines for each.

Inputs: data/flags.json, vendor/countries (mledoze/countries, ODbL)
Needs:  numpy, Pillow
"""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from geo_utils import simplify, area, clip_north_of, polygons

ROOT = Path(__file__).resolve().parent.parent
DATA, SRC = ROOT / 'data', ROOT / 'vendor/countries'

cca3 = {c['cca2']: c['cca3'].lower() for c in json.load(open(SRC / 'countries.json', encoding='utf-8'))}
flags = json.load(open(DATA / 'flags.json', encoding='utf-8'))
region = {f['c']: f['r'] for f in flags}

# Places whose outline is a dot or a scatter of tiny islands are left out of this game.
TOO_SMALL = set('VA MC SM LI AD NR TV MH FM KI PW MV SC ST TO KN AG DM LC VC GD BB BH SG'.split())
codes = [f['c'] for f in flags if (not f.get('x') and f['c'] not in TOO_SMALL) or f['c'] in ('GL', 'PR')]

def equal_area(lon, lat, lon0, lat0):
    """Lambert azimuthal equal-area projection centred on the country, so it isn't stretched."""
    l, p, l0, p0 = np.radians(lon), np.radians(lat), math.radians(lon0), math.radians(lat0)
    dl = (l - l0 + np.pi) % (2 * np.pi) - np.pi
    k = np.sqrt(2 / (1 + math.sin(p0) * np.sin(p) + math.cos(p0) * np.cos(p) * np.cos(dl)))
    return k * np.cos(p) * np.sin(dl), -(k * (math.cos(p0) * np.sin(p) - math.sin(p0) * np.cos(p) * np.cos(dl)))

paths, silhouettes = {}, {}
for cc in codes:
    geo = json.load(open(SRC / f'data/{cca3[cc]}.geo.json', encoding='utf-8'))
    polys = [p for ft in geo['features'] for p in polygons(ft.get('geometry'))]
    if not polys:
        print('no outline for', cc)   # Kosovo has none in this dataset
        continue
    if cc == 'US':   # mainland only: drop Alaska and Hawaii
        polys = [p for p in polys if np.array(p[0])[:, 0].mean() > -130 and np.array(p[0])[:, 1].mean() > 24]
    if cc == 'MA':   # Morocco without (disputed) Western Sahara, whose border follows 27°40'N
        polys = [[r for r in (clip_north_of(r, 27.667) for r in p) if len(r) > 3] for p in polys]
        polys = [p for p in polys if p]

    def rough_area(p):
        r = np.array(p[0]); x = r[:, 0] * np.cos(np.radians(r[:, 1].mean()))
        return area(np.c_[x, r[:, 1]])
    main_ring = np.array(max(polys, key=rough_area)[0])
    lon0 = math.degrees(math.atan2(np.sin(np.radians(main_ring[:, 0])).mean(), np.cos(np.radians(main_ring[:, 0])).mean()))
    lat0 = main_ring[:, 1].mean()

    projected = [[np.c_[equal_area(np.array(r)[:, 0], np.array(r)[:, 1], lon0, lat0)] for r in p] for p in polys]
    areas = [area(p[0]) for p in projected]
    m = int(np.argmax(areas)); centre = projected[m][0].mean(0); size = math.sqrt(areas[m])
    # Keep big islands, and small ones only if they are close to the mainland.
    kept = [p for p, a in zip(projected, areas)
            if a >= 0.3 * areas[m] or (a >= 0.003 * areas[m] and np.hypot(*(p[0].mean(0) - centre)) <= 2.0 * size)]

    pts = np.vstack([p[0] for p in kept]); lo, hi = pts.min(0), pts.max(0)
    scale = 92 / max(hi - lo); offset = (100 - (hi - lo) * scale) / 2
    d, outer = [], []
    for p in kept:
        for j, ring in enumerate(p):
            q = simplify((ring - lo) * scale + offset, 0.18)
            if len(q) < 4 or (j > 0 and area(q) < 4):   # skip tiny lakes/holes
                continue
            d.append('M' + 'L'.join(f'{x:.1f} {y:.1f}'.replace('.0 ', ' ').replace('.0L', 'L') for x, y in q) + 'Z')
            if j == 0:
                outer.append(q)
    paths[cc] = ''.join(d)
    img = Image.new('L', (32, 32), 0); draw = ImageDraw.Draw(img)
    for q in outer:
        draw.polygon([tuple(v * 0.32) for v in q], fill=255)
    silhouettes[cc] = np.asarray(img) > 127

# Similar outlines: overlap of the 32x32 silhouettes, nudged towards the same region.
similar = {}
for a in paths:
    scores = []
    for b in paths:
        if a != b:
            inter, union = (silhouettes[a] & silhouettes[b]).sum(), (silhouettes[a] | silhouettes[b]).sum()
            scores.append((1 - inter / union - 0.12 * (region[a] == region[b]), b))
    similar[a] = [b for _, b in sorted(scores)[:12]]

json.dump({'paths': paths, 'sim': similar}, open(DATA / 'shapes.json', 'w'), separators=(',', ':'))
print(f'{len(paths)} outlines written to data/shapes.json')
