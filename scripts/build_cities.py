"""Builds data/cities.json: every capital plus the famous cities in data/extra_cities.txt,
with coordinates and Italian names.

Inputs: data/flags.json, data/extra_cities.txt, vendor/natural-earth-vector (public domain),
        vendor/countries (to translate 3-letter country codes)
"""
import json, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA, VENDOR = ROOT / 'data', ROOT / 'vendor'
places = [f['properties'] for f in json.load(open(VENDOR / 'natural-earth-vector/geojson/ne_50m_populated_places.geojson', encoding='utf-8'))['features']]
cca2 = {c['cca3']: c['cca2'] for c in json.load(open(VENDOR / 'countries/countries.json', encoding='utf-8'))}
flags = json.load(open(DATA / 'flags.json', encoding='utf-8'))
BY = {f['c']: f for f in flags}

def norm(s):
    return unicodedata.normalize('NFD', s or '').encode('ascii', 'ignore').decode().lower().replace('.', '').replace('-', ' ').strip()

def country_of(p):
    return p['ISO_A2'] if p['ISO_A2'] in BY else (cca2.get(p['ADM0_A3']) or cca2.get(p['SOV_A3']))

def names_of(p):
    return {norm(p['NAME']), norm(p['NAMEASCII']), norm(p['NAME_EN']), *[norm(x) for x in (p['NAMEALT'] or '').split('|')]}

def find(code, name):
    """The most populous Natural Earth place with this name, preferably in this country."""
    m = [p for p in places if norm(name) in names_of(p) and country_of(p) == code] or [p for p in places if norm(name) in names_of(p)]
    return max(m, key=lambda p: p['POP_MAX']) if m else None

# Places Natural Earth does not list (or lists under an older capital): coordinates added by hand.
MANUAL = {
    'BI': (-3.4271, 29.9246), 'XK': (42.6629, 21.1655), 'NR': (-0.5477, 166.9209), 'PW': (7.5006, 134.6242),
    'Porto': (41.150, -8.611), 'Nice': (43.710, 7.262), 'Cologne': (50.938, 6.960), 'Liverpool': (53.408, -2.991),
    'Rotterdam': (51.922, 4.479), 'Antwerp': (51.219, 4.402), 'Gothenburg': (57.709, 11.974), 'Bangalore': (12.972, 77.594),
}
ITALIAN = {'Porto': 'Porto', 'Nice': 'Nizza', 'Cologne': 'Colonia', 'Antwerp': 'Anversa', 'Gothenburg': 'Göteborg'}
DISPLAY = {'Sao Paulo': 'São Paulo', 'Cordoba': 'Córdoba', 'Medellin': 'Medellín', 'Krakow': 'Kraków', 'St. Petersburg': 'Saint Petersburg'}

cities = []
for f in flags:                                   # 1. every capital (independent countries only)
    if f.get('x') or not f['cap']:
        continue
    if f['c'] in MANUAL:
        lat, lon = MANUAL[f['c']]
    else:
        p = find(f['c'], "Saint John's" if f['c'] == 'AG' else f['cap'])
        if not p:
            print('no coordinates for', f['cap']); continue
        lat, lon = p['LATITUDE'], p['LONGITUDE']
    cities.append(dict(id='cap-' + f['c'], n=f['cap'], ni=f['capi'], cc=f['c'], r=f['r'], t=f['t'], lat=round(lat, 3), lon=round(lon, 3), cap=1))

for line in open(DATA / 'extra_cities.txt', encoding='utf-8'):   # 2. famous non-capitals: CODE|Name|tier
    code, name, tier = line.strip().split('|')
    country = 'HK' if name == 'Hong Kong' else code
    if name in MANUAL:
        (lat, lon), italian = MANUAL[name], ITALIAN.get(name, name)
    else:
        p = find(code, name)
        if not p:
            print('no coordinates for', name); continue
        lat, lon, italian = p['LATITUDE'], p['LONGITUDE'], p.get('NAME_IT') or p['NAME']
    cities.append(dict(id='city-' + name.lower().replace(' ', '-').replace('.', ''), n=DISPLAY.get(name, name), ni=italian,
                       cc=country, r=BY[country]['r'], t=int(tier), lat=round(lat, 3), lon=round(lon, 3), cap=0))

json.dump(cities, open(DATA / 'cities.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(f'{len(cities)} cities written to data/cities.json')
