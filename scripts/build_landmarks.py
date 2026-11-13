"""Builds data/landmarks.json from the hand-written list in data/landmarks.txt,
and checks every coordinate:

- it should lie inside (or within 40 km of) its country's outline in data/world.json;
- if its "place" is also a city in data/cities.json, it should be within 60 km of that city.

Anything that fails is printed, so a typo in a latitude or a swapped sign is caught.
Places on tiny islands (not drawn in world.json) or offshore show up as warnings to eyeball.

Inputs: data/landmarks.txt, data/flags.json, data/world.json, data/cities.json
"""
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
flags = {f['c']: f for f in json.load(open(DATA / 'flags.json', encoding='utf-8'))}
cities = json.load(open(DATA / 'cities.json', encoding='utf-8'))
world_raw = json.load(open(DATA / 'world.json'))

def decode(flat):
    pts, x, y = [], 0, 0
    for i in range(0, len(flat), 2):
        x += flat[i]; y += flat[i + 1]; pts.append((x / 10, y / 10))
    return pts
world = {c: [decode(r) for r in rings] for c, rings in world_raw.items()}

def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))

def inside(pt, ring):
    lat, lon = pt; hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit

def km_to_country(pt, code):
    rings = world.get(code.split('-')[0] if code.startswith('GB-') else code)
    if not rings:
        return None
    if any(inside(pt, r) for r in rings):
        return 0
    return min(km(pt, (y, x)) for r in rings for x, y in r)

out, problems = [], []
for line in open(DATA / 'landmarks.txt', encoding='utf-8'):
    if not line.strip() or line.startswith('#'):
        continue
    lid, name, nome, code, place, luogo, lat, lon, tier, kind = line.rstrip('\n').split('|')
    lat, lon = float(lat), float(lon)
    d = km_to_country((lat, lon), code)
    if d is None or d > 40:
        problems.append(f'{name}: {"no outline for " + code if d is None else f"{d:.0f} km outside {code}"}')
    for c in cities:
        if c['n'] == place.split(',')[0] and c['cc'] in (code, code.split('-')[0]):
            if km((lat, lon), (c['lat'], c['lon'])) > 60:
                problems.append(f'{name}: {km((lat, lon), (c["lat"], c["lon"])):.0f} km from {c["n"]}')
    out.append(dict(id='lm-' + lid, n=name, ni=nome, cc=code, p=place, pi=luogo, lat=lat, lon=lon,
                    t=int(tier), k=kind, r=flags[code]['r']))

json.dump(out, open(DATA / 'landmarks.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(f'{len(out)} landmarks written to data/landmarks.json')
for p in problems:
    print('  check:', p)
