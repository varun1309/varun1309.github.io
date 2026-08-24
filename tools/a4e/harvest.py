#!/usr/bin/env python3
"""
One-time-but-repeatable extraction of the three hand-authored SVGs in the
A-4E-C post into the JSON under tools/a4e/data/.

Run it against the post as it stands today and the renderers reproduce those
SVGs byte for byte -- that round trip is what proves the data files are a
faithful description and not an approximation. After that the JSON is the
source of truth and this script is only needed if the post is ever re-authored
by hand.

The four POV label boxes that no layer currently shades are recovered by
detecting the printed label fields on the template JPG (see detect_fields()).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = pathlib.Path(__file__).resolve().parent / 'data'
POST = ROOT / '_posts' / '2026-08-13-a4e-c-cockpit-avionics.html'
TEMPLATE = ROOT / 'assets' / 'img' / 'vkb-gladiator-nxt-evo-template.jpg'

FAMILY_OPACITY = {'util': '0.12'}
DEFAULT_OPACITY = '0.14'
EMPH_OPACITY = '0.22'


# ------------------------------------------------------------------ helpers
def svgs(html: str):
    out, i = [], 0
    while True:
        a = html.find('<svg', i)
        if a < 0:
            return out
        b = html.index('</svg>', a) + 6
        out.append(html[a:b])
        i = b


def attr(tag: str, name: str, cast=str):
    m = re.search(rf'{name}="([^"]*)"', tag)
    return cast(m.group(1)) if m else None


def family_of(tag: str):
    m = re.search(r'--a4e-fam-(\w+)\)', tag)
    return m.group(1) if m else None


def jdump(name: str, obj):
    p = DATA / name
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'  data/{name:<16} {p.stat().st_size / 1024:6.1f} KB')


# ----------------------------------------------------------- page 1: cockpit
def harvest_cockpit(svg: str):
    rects = re.findall(r'<rect [^>]*/>', svg)
    texts = re.findall(r'<text [^>]*>(?:[^<]*)</text>', svg)

    def txt_at(x, y, tol=1):
        for t in texts:
            if abs(attr(t, 'x', float) - x) <= tol and abs(attr(t, 'y', float) - y) <= tol:
                return re.sub(r'^<text[^>]*>|</text>$', '', t)
        return None

    panels = []
    for r in rects:
        fam = family_of(r)
        if not fam:
            continue
        x, y = attr(r, 'x', float), attr(r, 'y', float)
        w, h = attr(r, 'width', float), attr(r, 'height', float)
        emph = 'stroke-width="1.8"' in r
        label = txt_at(x + 10, y + 18) or txt_at(x + 8, y + 15)
        sub = txt_at(x + 8, y + 30)
        panels.append({'x': x, 'y': y, 'w': w, 'h': h, 'family': fam,
                       'label': label, 'sub': sub, 'emph': emph,
                       'opacity': attr(r, 'fill-opacity')})

    # containers: the three outline rects with no family fill
    containers = []
    for r in rects:
        if family_of(r) or 'fill="none"' not in r:
            continue
        x, y = attr(r, 'x', float), attr(r, 'y', float)
        # Container titles carry the wider tracking (1.5); the FORWARD/MIDDLE/AFT
        # zone captions sit at similar coordinates with 1.2, so key off tracking
        # rather than position or the consoles get titled "FORWARD".
        title = None
        for t in texts:
            if 'letter-spacing="1.5"' not in t:
                continue
            ty, tx = attr(t, 'y', float), attr(t, 'x', float)
            if abs(ty - (y + 19)) <= 1 or abs(ty - (y - 8)) <= 1:
                if abs(tx - (x + 12)) <= 2 or abs(tx - (x + 8)) <= 2:
                    title = {'text': re.sub(r'^<text[^>]*>|</text>$', '', t),
                             'x': tx, 'y': ty}
                    break
        containers.append({'x': x, 'y': y, 'w': attr(r, 'width', float),
                           'h': attr(r, 'height', float), 'title': title})

    zones = [{'text': re.sub(r'^<text[^>]*>|</text>$', '', t),
              'x': attr(t, 'x', float), 'y': attr(t, 'y', float)}
             for t in texts if 'opacity="0.45" letter-spacing="1.2"' in t]

    def group_of(p):
        if p['y'] < 220:
            return 'main'
        return 'left' if p['x'] < 450 else 'right'

    spec = {
        'viewBox': attr(svg[:svg.index('>')], 'viewBox'),
        'aria': attr(svg[:svg.index('>')], 'aria-label'),
        'marker': 'a4ear',
        'orientation': {
            'arrow': attr(next(t for t in re.findall(r'<polygon [^>]*/>', svg)), 'points'),
            'label': txt_at(450, 38), 'x': 450, 'y': 38,
        },
        'containers': containers,
        'zoneLabels': zones,
        'groupFontSize': {'main': '10.5', 'left': '10', 'right': '10'},
        'groups': {g: [{k: p[k] for k in ('x', 'y', 'w', 'h', 'family', 'label',
                                          'sub', 'emph', 'opacity')}
                       for p in panels if group_of(p) == g]
                   for g in ('main', 'left', 'right')},
        # zone captions live inside their console's <g> so they inherit its font
        'zonesByGroup': {g: [z for z in zones
                             if (g == 'left' and z['x'] < 450)
                             or (g == 'right' and z['x'] >= 450)]
                         for g in ('left', 'right')},
        'decor': {
            'stick': {'cx': 450, 'cy': 410, 'r': 13, 'label': 'STICK', 'labelY': 440},
            'seat': {'x': 396, 'y': 460, 'w': 108, 'h': 120, 'rx': 10,
                     'label': 'SEAT', 'labelY': 525},
        },
    }
    return spec


# ---------------------------------------------------------- page 2: navchain
def harvest_nav(svg: str):
    head = svg[:svg.index('>')]
    nodes = []
    for r in re.findall(r'<rect [^>]*/>', svg):
        x, y = attr(r, 'x', float), attr(r, 'y', float)
        w, h = attr(r, 'width', float), attr(r, 'height', float)
        lines = []
        for t in re.findall(r'<text [^>]*>[^<]*</text>', svg):
            tx, ty = attr(t, 'x', float), attr(t, 'y', float)
            if x <= tx <= x + w and y <= ty <= y + h and 'text-anchor' not in t:
                lines.append({'text': re.sub(r'^<text[^>]*>|</text>$', '', t),
                              'dx': round(tx - x, 1), 'dy': round(ty - y, 1),
                              'opacity': attr(t, 'opacity'), 'size': attr(t, 'font-size')})
        lines.sort(key=lambda l: l['dy'])
        nodes.append({'x': x, 'y': y, 'w': w, 'h': h,
                      'family': family_of(r), 'emph': 'stroke-width="1.8"' in r,
                      'dashed': 'stroke-dasharray' in r,
                      'opacity': attr(r, 'fill-opacity'), 'lines': lines})

    arrows = [{'x1': float(a), 'y1': float(b), 'x2': float(c), 'y2': float(d)}
              for a, b, c, d in re.findall(
                  r'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)"/>', svg)]

    labels = []
    for t in re.findall(r'<text [^>]*font-size="9.5"[^>]*>[^<]*</text>', svg):
        labels.append({'text': re.sub(r'^<text[^>]*>|</text>$', '', t),
                       'x': attr(t, 'x', float), 'y': attr(t, 'y', float),
                       'anchor': attr(t, 'text-anchor')})
    return {'viewBox': attr(head, 'viewBox'), 'aria': attr(head, 'aria-label'),
            'marker': 'a4ea2', 'nodes': nodes, 'arrows': arrows, 'arrowLabels': labels}


# --------------------------------------------------- page 3: template fields
def detect_fields():
    """Find the printed label fields on the template: pairs of long dark rules."""
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        print('  ! Pillow/numpy missing, skipping field detection', file=sys.stderr)
        return []
    im = Image.open(TEMPLATE).convert('L')
    a = np.asarray(im).astype('int16')
    dark = a < 128
    H, W = dark.shape
    scale = 3300.0 / W
    rules = []
    for y in range(H):
        idx = np.flatnonzero(dark[y])
        if idx.size < 200:
            continue
        start = prev = idx[0]
        for v in idx[1:]:
            if v - prev > 4:
                if prev - start >= 250:
                    rules.append((y, int(start), int(prev)))
                start = v
            prev = v
        if prev - start >= 250:
            rules.append((y, int(start), int(prev)))
    merged = []
    for y, x0, x1 in sorted(rules):
        if any(abs(m[0] - y) <= 3 and abs(m[1] - x0) < 12 and abs(m[2] - x1) < 12
               for m in merged):
            continue
        merged.append((y, x0, x1))
    fields = []
    for i, (y0, a0, b0) in enumerate(merged):
        for y1, a1, b1 in merged[i + 1:]:
            if 48 <= y1 - y0 <= 80 and abs(a1 - a0) < 14 and abs(b1 - b0) < 14:
                fields.append([round(a0 * scale), round(y0 * scale),
                               round((b0 - a0) * scale), round((y1 - y0) * scale)])
                break
    out = []
    for f in sorted(fields, key=lambda f: (f[1], f[0])):
        if any(abs(g[0] - f[0]) <= 18 and abs(g[1] - f[1]) <= 18 for g in out):
            continue
        out.append(f)
    return out


def harvest_vkb(svg: str, html: str):
    parts = re.split(r'<g transform="translate\(0,(\d+)\)" font-family', svg)
    layers = []
    for i in range(1, len(parts), 2):
        off, blk = int(parts[i]), parts[i + 1]
        heads = re.findall(r'<text x="(\d+)" y="86"[^>]*>([^<]*)</text>', blk)
        boxes = {tuple(map(int, m)) for m in re.findall(
            r'<rect x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)" fill="#000"', blk)}
        lbls = {(int(x), int(y)): (t, f) for x, y, f, t in re.findall(
            r'<text x="(\d+)" y="(\d+)" font-size="26" letter-spacing="0.5" '
            r'fill="(#[0-9A-Fa-f]+)">([^<]*)</text>', blk)}
        layers.append({'offset': off, 'heads': [h[1] for h in heads],
                       'boxes': boxes, 'labels': lbls})

    anchors = sorted({a for L in layers for a in L['labels']}, key=lambda p: (p[1], p[0]))
    allboxes = sorted({b for L in layers for b in L['boxes']}, key=lambda b: (b[1], b[0]))

    # pair anchor <-> box on the offset the author used most (+76,+53)-ish
    cand = []
    for b in allboxes:
        for a in anchors:
            dx, dy = a[0] - b[0], a[1] - b[1]
            if 10 <= dx <= 120 and 40 <= dy <= 115:
                cand.append((abs(dx - 76) + abs(dy - 56), b, a))
    cand.sort()
    box_of, used = {}, set()
    for _, b, a in cand:
        if a in box_of or b in used:
            continue
        box_of[a], _ = b, used.add(b)

    detected = detect_fields()
    derived = {}
    for a in anchors:
        if a in box_of:
            continue
        hits = [f for f in detected
                if f[0] - 40 <= a[0] <= f[0] + f[2] + 40 and f[1] - 10 <= a[1] <= f[1] + f[3] + 30]
        if hits:
            box_of[a] = tuple(hits[0])
            derived[a] = True
    return layers, anchors, allboxes, box_of, derived, detected


# ---------------------------------------------------------------------- main
def main():
    html = POST.read_text(encoding='utf-8')
    s1, s2, s3 = svgs(html)[:3]
    DATA.mkdir(parents=True, exist_ok=True)
    print('harvesting:')
    jdump('cockpit.json', harvest_cockpit(s1))
    jdump('navchain.json', harvest_nav(s2))
    layers, anchors, allboxes, box_of, derived, detected = harvest_vkb(s3, html)
    jdump('template_fields.json',
          {'note': 'label fields detected on the template JPG, SVG units',
           'fields': detected})
    jdump('_vkb_geometry.json',
          {'anchors': [list(a) for a in anchors],
           'boxes': [list(b) for b in allboxes],
           'boxOfAnchor': {f'{a[0]},{a[1]}': list(b) for a, b in box_of.items()},
           'derivedFromTemplate': [list(a) for a in derived],
           'layers': [{'offset': L['offset'], 'heads': L['heads'],
                       'labels': {f'{k[0]},{k[1]}': v for k, v in L['labels'].items()},
                       'boxes': [list(b) for b in sorted(L['boxes'])]} for L in layers]})
    print(f'\n  anchors {len(anchors)}   boxes {len(allboxes)}   '
          f'paired {len(box_of)}   recovered-from-JPG {len(derived)}   '
          f'fields-on-template {len(detected)}')


if __name__ == '__main__':
    main()
