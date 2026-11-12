"""Assembles index.html: drops the JSON files from data/ into src/template.html.

This is the only step needed after editing the game's code in src/template.html.
Needs nothing beyond Python.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'

def embed(obj):
    # "</" would end the <script> tag early, so it is escaped.
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

load = lambda name: json.load(open(DATA / name, encoding='utf-8'))
page = (ROOT / 'src/template.html').read_text(encoding='utf-8')
page = (page.replace('__DATA__', embed(load('flags.json')))
            .replace('__SHAPES__', embed(load('shapes.json')))
            .replace('__WORLD__', embed(load('world.json')))
            .replace('__CITIES__', embed(load('cities.json'))))
(ROOT / 'index.html').write_text(page, encoding='utf-8')
print(f'index.html written ({len(page.encode()) // 1024} KB)')
