#!/usr/bin/env python3
"""
cockpit.json -> the page-1 plan view;  navchain.json -> the page-2 flow diagram.

Neither drawing has anything to do with a DCS input export -- a cockpit is laid
out in space and the nav chain is a set of system relationships, and no .lua
knows either. What data-driving them buys is that adding a panel, recolouring a
system family or retitling a box is a line of JSON instead of hand-editing
coordinates inside a hundred lines of SVG.

Panel `y` may be omitted, in which case it flows from the previous panel in its
group using `rowGap`; the harvested files carry explicit values so the round-trip
is exact.
"""
from __future__ import annotations

import json
import pathlib

from svgutil import esc, num

DATA = pathlib.Path(__file__).resolve().parent / 'data'
MONO = 'ui-monospace, monospace'
ROW_GAP = 29


def _paint(family, emph, opacity=None):
    """Family fill/stroke. `opacity` is carried in the data because the post uses
    a different weight for the same family in the main panel and the consoles."""
    if not family:
        return ''
    var = f'var(--a4e-fam-{family})'
    op = opacity or ('0.22' if emph else ('0.12' if family == 'util' else '0.14'))
    out = f' fill="{var}" fill-opacity="{op}" stroke="{var}"'
    return out + ' stroke-width="1.8"' if emph else out


def render_cockpit(spec=None) -> str:
    s = spec or json.loads((DATA / 'cockpit.json').read_text(encoding='utf-8'))
    o, d = s['orientation'], s['decor']
    L = [f'<svg viewBox="{s["viewBox"]}" role="img" aria-label="{s["aria"]}">',
         '  <defs>',
         f'    <marker id="{s["marker"]}" viewBox="0 0 10 10" refX="9" refY="5" '
         'markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
         '      <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/>',
         '    </marker>', '  </defs>', '',
         f'  <polygon points="{o["arrow"]}" fill="currentColor" opacity="0.45"/>',
         f'  <text x="{num(o["x"])}" y="{num(o["y"])}" font-family="{MONO}" '
         f'font-size="10.5" letter-spacing="1.6" fill="currentColor" opacity="0.5" '
         f'text-anchor="middle">{esc(o["label"])}</text>', '']

    for c in s['containers']:
        L.append(f'  <rect x="{num(c["x"])}" y="{num(c["y"])}" width="{num(c["w"])}" '
                 f'height="{num(c["h"])}" rx="4" fill="none" stroke="currentColor" '
                 'stroke-opacity="0.32"/>')
        t = c['title']
        L.append(f'  <text x="{num(t["x"])}" y="{num(t["y"])}" font-family="{MONO}" '
                 f'font-size="10.5" letter-spacing="1.5" fill="currentColor" '
                 f'opacity="0.55">{esc(t["text"])}</text>')
    L.append('')

    for group, panels in s['groups'].items():
        size = s['groupFontSize'][group]
        L.append(f'  <g font-family="{MONO}" font-size="{size}" fill="currentColor">')
        for z in s.get('zonesByGroup', {}).get(group, []):
            L.append(f'    <text x="{num(z["x"])}" y="{num(z["y"])}" opacity="0.45" '
                     f'letter-spacing="1.2">{esc(z["text"])}</text>')
        prev_bottom = None
        for p in panels:
            y = p.get('y')
            if y is None:
                y = prev_bottom + (s.get('rowGap', ROW_GAP) - p['h'])
            prev_bottom = y + p['h']
            dx, dy = (10, 18) if group == 'main' else (8, 15)
            L.append(f'    <rect x="{num(p["x"])}" y="{num(y)}" width="{num(p["w"])}" '
                     f'height="{num(p["h"])}" rx="2"'
                     f'{_paint(p["family"], p["emph"], p.get("opacity"))}/>')
            L.append(f'    <text x="{num(p["x"] + dx)}" y="{num(y + dy)}">'
                     f'{esc(p["label"])}</text>')
            if p.get('sub'):
                L.append(f'    <text x="{num(p["x"] + dx)}" y="{num(y + dy + 15)}" '
                         f'opacity="0.7">{esc(p["sub"])}</text>')
        L.append('  </g>')
    L.append('')

    st, se = d['stick'], d['seat']
    L += [f'  <circle cx="{num(st["cx"])}" cy="{num(st["cy"])}" r="{num(st["r"])}" '
          'fill="none" stroke="currentColor" stroke-opacity="0.4"/>',
          f'  <text x="{num(st["cx"])}" y="{num(st["labelY"])}" font-family="{MONO}" '
          f'font-size="10" fill="currentColor" opacity="0.45" text-anchor="middle">'
          f'{esc(st["label"])}</text>',
          f'  <rect x="{num(se["x"])}" y="{num(se["y"])}" width="{num(se["w"])}" '
          f'height="{num(se["h"])}" rx="{num(se["rx"])}" fill="currentColor" '
          'fill-opacity="0.05" stroke="currentColor" stroke-opacity="0.3"/>',
          f'  <text x="{num(se["x"] + se["w"] / 2)}" y="{num(se["labelY"])}" '
          f'font-family="{MONO}" font-size="10.5" letter-spacing="1.4" '
          f'fill="currentColor" opacity="0.45" text-anchor="middle">'
          f'{esc(se["label"])}</text>',
          '</svg>']
    return '\n'.join(L)


def render_nav(spec=None) -> str:
    s = spec or json.loads((DATA / 'navchain.json').read_text(encoding='utf-8'))
    L = [f'<svg viewBox="{s["viewBox"]}" role="img" aria-label="{s["aria"]}">',
         '  <defs>',
         f'    <marker id="{s["marker"]}" viewBox="0 0 10 10" refX="9" refY="5" '
         'markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
         '      <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/>',
         '    </marker>', '  </defs>',
         f'  <g font-family="{MONO}" font-size="11" fill="currentColor">']

    for n in s['nodes']:
        if n['family']:
            paint = _paint(n['family'], n['emph'], n['opacity'])
        else:
            paint = (f' fill="currentColor" fill-opacity="{n["opacity"]}" '
                     'stroke="currentColor" stroke-opacity="'
                     + ('0.4' if n['dashed'] else '0.5') + '"')
        dash = ' stroke-dasharray="4 3"' if n['dashed'] else ''
        L.append(f'    <rect x="{num(n["x"])}" y="{num(n["y"])}" width="{num(n["w"])}" '
                 f'height="{num(n["h"])}" rx="3"{paint}{dash}/>')
        for ln in n['lines']:
            extra = ''
            if ln.get('size'):
                extra += f' font-size="{ln["size"]}"'
            if ln.get('opacity'):
                extra += f' opacity="{ln["opacity"]}"'
            L.append(f'    <text x="{num(n["x"] + ln["dx"])}" '
                     f'y="{num(n["y"] + ln["dy"])}"{extra}>{esc(ln["text"])}</text>')

    L.append(f'    <g stroke="currentColor" stroke-width="1.4" fill="none" '
             f'marker-end="url(#{s["marker"]})">')
    for a in s['arrows']:
        L.append(f'      <line x1="{num(a["x1"])}" y1="{num(a["y1"])}" '
                 f'x2="{num(a["x2"])}" y2="{num(a["y2"])}"/>')
    L.append('    </g>')
    for lb in s['arrowLabels']:
        anchor = f' text-anchor="{lb["anchor"]}"' if lb.get('anchor') else ''
        L.append(f'    <text x="{num(lb["x"])}" y="{num(lb["y"])}" font-size="9.5" '
                 f'opacity="0.65"{anchor}>{esc(lb["text"])}</text>')
    L += ['  </g>', '</svg>']
    return '\n'.join(L)


if __name__ == '__main__':
    for name, fn in (('cockpit', render_cockpit), ('nav', render_nav)):
        out = fn()
        pathlib.Path(f'/tmp/a4ework/out_{name}.svg').write_text(out)
        print(f'{name:<8} {len(out)} chars, {out.count(chr(10)) + 1} lines')
