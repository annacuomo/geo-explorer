"""Builds data/world.json: simplified lon/lat outlines of every country, used to draw the
spinning globe and the city maps.

Coordinates are stored as integers (tenths of a degree), each point as the difference
from the previous one, which keeps the file around 60 KB.

Inputs: vendor/countries (mledoze/countries, ODbL)
"""
import glob, json
from pathlib import Path
import numpy as np
from geo_utils import simplify, area, polygons

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'vendor/countries'
cca2 = {c['cca3'].lower(): c['cca2'] for c in json.load(open(SRC / 'countries.json', encoding='utf-8'))}

world = {}
for f in sorted(glob.glob(str(SRC / 'data/*.geo.json'))):
    code = cca2.get(Path(f).name.split('.')[0])
    if not code or code == 'AQ':   # no Antarctica
        continue
    rings = [np.array(p[0])[:, :2] for ft in json.load(open(f, encoding='utf-8'))['features'] for p in polygons(ft.get('geometry'))]
    if not rings:
        continue
    biggest = max(area(r) for r in rings)
    out = []
    for r in rings:
        if area(r) < 0.08 and area(r) < biggest:   # drop tiny islands, but keep each country's main piece
            continue
        q = simplify(r, 0.22)
        if len(q) < 4:
            continue
        flat, px, py = [], 0, 0
        for x, y in np.round(q * 10).astype(int):
            flat += [int(x - px), int(y - py)]; px, py = x, y
        out.append(flat)
    if out:
        world[code] = out

json.dump(world, open(ROOT / 'data/world.json', 'w'), separators=(',', ':'))
print(f'{len(world)} countries written to data/world.json')
