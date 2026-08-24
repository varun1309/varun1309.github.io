#!/usr/bin/env python3
"""
Regenerate the generated parts of the A-4E-C post.

    python3 tools/a4e/build.py                        # redraw from data/bindings.json
    python3 tools/a4e/build.py Gladiator.diff.lua     # take bindings from a DCS export
    python3 tools/a4e/build.py default.lua mine.diff.lua modifiers.lua
    python3 tools/a4e/build.py --check                # fail if the post is stale
    python3 tools/a4e/build.py --dry-run mine.diff.lua

Argument order does not matter; each .lua is classified by its contents. Pass the
mod's default.lua alongside your diff so unbound controls can be told apart from
controls still on the DCS default, and modifiers.lua so layers can be named.

Only the four fenced regions of the post are touched.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import dcs                                                   # noqa: E402
import inject                                                # noqa: E402
import render_pages                                          # noqa: E402
import render_vkb                                            # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / 'data'
POST = ROOT / '_posts' / '2026-08-13-a4e-c-cockpit-avionics.html'


def classify(paths):
    kinds = {'default': [], 'diff': [], 'modifiers': []}
    for p in paths:
        shape, _ = dcs.read(p)
        kinds[shape].append(p)
    return kinds


def bindings_from_lua(paths, roster_inputs):
    kinds = classify(paths)
    mods = dcs.ModifierMap.load(kinds['modifiers'][0]) if kinds['modifiers'] \
        else dcs.ModifierMap()
    merged = dcs.merge(kinds['default'], kinds['diff'])
    out, offstick = [], []
    for b in merged:
        rec = {'input': b.input, 'modifiers': list(mods.names(b.modifiers)),
               'command': b.command, 'kind': b.kind}
        (out if b.input in roster_inputs else offstick).append(rec)
    return out, offstick, kinds, mods


def summarise(bindings, layers):
    per = {}
    for b in bindings:
        per[tuple(sorted(b['modifiers']))] = per.get(tuple(sorted(b['modifiers'])), 0) + 1
    return {' + '.join(spec['modifiers']) or 'no modifier':
            per.get(tuple(sorted(spec['modifiers'])), 0) for spec in layers}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('lua', nargs='*', help='DCS input .lua files, in any order')
    ap.add_argument('--dry-run', action='store_true',
                    help='render and report, write nothing')
    ap.add_argument('--check', action='store_true',
                    help='exit 1 if regenerating would change the post')
    ap.add_argument('--post', type=pathlib.Path, default=POST)
    args = ap.parse_args(argv)

    ctl, layers, ab = render_vkb.load()
    roster_inputs = {c['input'] for c in ctl['controls']}
    bindings_path = DATA / 'bindings.json'
    previous = json.loads(bindings_path.read_text(encoding='utf-8'))['bindings']

    offstick, kinds, mods = [], None, None
    if args.lua:
        bindings, offstick, kinds, mods = bindings_from_lua(args.lua, roster_inputs)
        print('read:')
        for shape, paths in kinds.items():
            for p in paths:
                print(f'  {shape:<10} {p}')
        if not kinds['modifiers']:
            print('  ! no modifiers.lua given: layers are matched on raw button '
                  'names, so any layer whose modifier is not literally called '
                  '"F2"/"F3" will come out empty')
        if not kinds['default']:
            print('  ! no default.lua given: a control still on the mod default '
                  'will render as unbound')
    else:
        bindings = previous
        print(f'no .lua given; redrawing from data/bindings.json '
              f'({len(bindings)} bindings)')

    if args.lua:
        added = [b for b in bindings if b not in previous]
        dropped = [b for b in previous if b not in bindings]
        print(f'\nbindings: {len(bindings)} on the stick '
              f'(+{len(added)} / -{len(dropped)} vs data/bindings.json)')
        for b in added[:40]:
            m = '+'.join(b['modifiers'])
            print(f'  + {b["input"]:<20} {("[" + m + "] ") if m else "":<10}{b["command"]}')
        for b in dropped[:40]:
            m = '+'.join(b['modifiers'])
            print(f'  - {b["input"]:<20} {("[" + m + "] ") if m else "":<10}{b["command"]}')
        if offstick:
            print(f'\n{len(offstick)} bindings on inputs the roster does not '
                  f'describe (not drawn; add them to data/controls.json to place '
                  f'them on the template):')
            seen = set()
            for b in offstick:
                if b['input'] in seen:
                    continue
                seen.add(b['input'])
                print(f'    {b["input"]:<24} {b["command"]}')
                if len(seen) >= 15:
                    print(f'    ... and {len(offstick) - 15} more')
                    break

    print('\nper layer: ' + ', '.join(f'{k}: {v}'
                                      for k, v in summarise(bindings, layers).items()))

    # a label that had to be clipped to fit its field needs a hand-written
    # short form; report rather than quietly shipping "TACAN CHANNEL 10..."
    clipped = []
    for b in bindings:
        short = render_vkb.shorten(b['command'], ab['map'])
        if short.endswith(render_vkb.ELLIPSIS):
            clipped.append((b['command'], short))
    if clipped:
        print(f'\n{len(clipped)} label(s) too long for a 347-unit field and '
              f'clipped. Add a short form to data/abbrev.json:')
        for cmd, short in dict.fromkeys(clipped):
            print(f'    "{cmd}": "{short.rstrip(render_vkb.ELLIPSIS)}",')

    blocks = {
        'cockpit': render_pages.render_cockpit(),
        'navchain': render_pages.render_nav(),
        'vkb-svg': render_vkb.render_svg(ctl, layers, ab, bindings),
        'vkb-tables': render_vkb.render_tables(ctl, layers, ab, bindings),
    }
    text = args.post.read_text(encoding='utf-8')
    new, changed = inject.apply(text, blocks)

    if args.check:
        stale = changed or bindings != previous
        print(f'\ncheck: {"STALE -> " + ", ".join(changed) if stale else "up to date"}')
        return 1 if stale else 0

    if args.dry_run:
        print(f'\ndry run: would rewrite {", ".join(changed) or "nothing"}')
        return 0

    if args.lua:
        bindings_path.write_text(json.dumps(
            {'note': 'Effective on-stick bindings. Regenerated by build.py from a '
                     'DCS input export; edit the .lua in DCS, not this file.',
             'bindings': bindings}, indent=2, ensure_ascii=False) + '\n',
            encoding='utf-8')
    if changed:
        args.post.write_text(new, encoding='utf-8')
    print(f'\nwrote: {", ".join(changed) or "nothing (already current)"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
