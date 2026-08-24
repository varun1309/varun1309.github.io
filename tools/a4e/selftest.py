#!/usr/bin/env python3
"""
Prove the data files still describe the post.

Renders every generated region from data/ and compares it against what is
currently in the post, element by element rather than byte by byte: attribute
sets and text content must match exactly, while whitespace and the order of
non-overlapping siblings may differ.

    python3 tools/a4e/selftest.py

Run it after editing anything under data/ or any renderer. A failure means the
drawing changed -- which is fine if you meant it (rerun build.py), and a bug if
you did not.
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import inject                                                # noqa: E402
import render_pages                                          # noqa: E402
import render_vkb                                            # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
POST = HERE.parents[1] / '_posts' / '2026-08-13-a4e-c-cockpit-avionics.html'

TAGS = ('rect|text|circle|polygon|line|path|marker|use|image|tr|td|th|code|'
        'div|table|thead|tbody|h3|span')


def elements(fragment: str) -> collections.Counter:
    frag = re.sub(r'<!--.*?-->', '', fragment, flags=re.S)
    c = collections.Counter()
    for m in re.finditer(rf'<({TAGS})\b([^>]*?)/?>', frag):
        attrs = tuple(sorted(re.findall(r'([\w:-]+)="([^"]*)"', m.group(2))))
        c[(m.group(1), attrs)] += 1
    for m in re.finditer(r'>([^<>]+)<', frag):
        t = re.sub(r'\s+', ' ', m.group(1)).strip()
        if t:
            c[('#text', t)] += 1
    return c


def main() -> int:
    text = POST.read_text(encoding='utf-8')
    found = inject.regions(text)
    ctl, layers, ab = render_vkb.load()
    bindings = json.loads((HERE / 'data' / 'bindings.json')
                          .read_text(encoding='utf-8'))['bindings']
    blocks = {
        'cockpit': render_pages.render_cockpit(),
        'navchain': render_pages.render_nav(),
        'vkb-svg': render_vkb.render_svg(ctl, layers, ab, bindings),
        'vkb-tables': render_vkb.render_tables(ctl, layers, ab, bindings),
    }
    failures = 0
    for name, block in blocks.items():
        start, end, _ = found[name]
        want, got = elements(text[start:end]), elements(block)
        missing, extra = want - got, got - want
        n = sum(want.values())
        if missing or extra:
            failures += 1
            print(f'  FAIL {name:<11} {n} elements in the post, '
                  f'{sum(got.values())} rendered')
            for k, v in list(missing.items())[:6]:
                print(f'         in post, not rendered  x{v}: {k[0]} {dict(k[1]) if k[0] != "#text" else k[1]}')
            for k, v in list(extra.items())[:6]:
                print(f'         rendered, not in post  x{v}: {k[0]} {dict(k[1]) if k[0] != "#text" else k[1]}')
        else:
            print(f'  ok   {name:<11} {n} elements match')

    controls = ctl['controls']
    inputs = [c['input'] for c in controls]
    dupes = [i for i, n in collections.Counter(inputs).items() if n > 1]
    if dupes:
        failures += 1
        print(f'  FAIL controls.json: two controls share a DCS input: {dupes}')
    else:
        print(f'  ok   controls.json {len(controls)} controls, inputs unique')

    unplaced = [b for b in bindings if b['input'] not in set(inputs)]
    if unplaced:
        print(f'  note {len(unplaced)} bindings are on inputs no control claims '
              f'(they render nowhere): '
              f'{sorted({b["input"] for b in unplaced})}')

    print('\nselftest: PASS' if not failures else f'\nselftest: {failures} FAILED')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
