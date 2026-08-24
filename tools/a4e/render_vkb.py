#!/usr/bin/env python3
"""
controls.json x layers.json x bindings -> the page-3 SVG and the four HTML tables.

Rules read off the hand-authored original:
  * a control's label field is shaded when it carries no binding on that layer;
  * the two modifier controls appear -- shaded and labelled -- only on layers
    that do not hold them, and vanish entirely on layers that do;
  * the spare button is always shaded and always labelled;
  * label fields the roster claims for no control stay shaded on every layer.
"""
from __future__ import annotations

import json
import pathlib

from svgutil import esc, num

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / 'data'

# tails short enough to stand alone once a shared prefix is dropped
SENSE_WORDS = {'CW', 'CCW', 'INC', 'DEC', 'INCREASE', 'DECREASE'}

ARIA = ("The official VKB Gladiator NXT EVO keybind template, filled in four "
        "times &#8212; once per modifier layer &#8212; with the A-4E-C bindings "
        "written into each control's label box.")


def load():
    ctl = json.loads((DATA / 'controls.json').read_text(encoding='utf-8'))
    layers = json.loads((DATA / 'layers.json').read_text(encoding='utf-8'))
    ab = json.loads((DATA / 'abbrev.json').read_text(encoding='utf-8'))
    return ctl, layers, ab


ELLIPSIS = '\u2026'


def shorten(cmd: str, table: dict, width_units: int = 347, size: int = 26) -> str:
    """DCS command name -> uppercase short form that fits a label field.

    Returns a value ending in an ellipsis when even the mechanical shortenings
    were not enough; build.py reports those so you can add a hand-written short
    form to data/abbrev.json rather than shipping a clipped label.
    """
    if cmd in table:
        return table[cmd]
    s = cmd.upper()
    for a, b in (('CONTINUOUS ', ''), (' ELSE STOP', ''), (' ELSE OFF', ''),
                 ('INCREASE', 'INC'), ('DECREASE', 'DEC'), ('DOWN', 'DN'),
                 ('LEFT', 'L'), ('RIGHT', 'R'), ('SELECT', 'SEL'),
                 ('WEAPON', 'WPN'), ('ANTENNA', 'ANT'), ('TOGGLE', ''),
                 ('  ', ' ')):
        if _fits(s, width_units, size):
            break
        s = s.replace(a, b).strip()
    # monospace at 26 units with 0.5 tracking fits ~21 characters in 347 units
    limit = _char_limit(width_units, size)
    return s if len(s) <= limit else s[:limit - 1].rstrip() + ELLIPSIS


def _char_limit(width_units: int, size: int) -> int:
    return int((width_units - 60) / (size * 0.60 + 0.5))


def _fits(s: str, width_units: int, size: int) -> bool:
    return len(s) <= _char_limit(width_units, size)


def index_bindings(bindings):
    """(input, sorted modifier names) -> command name."""
    out = {}
    for b in bindings:
        key = (b['input'], tuple(sorted(b.get('modifiers') or [])))
        out.setdefault(key, b['command'])
    return out


def render_svg(ctl, layers, ab, bindings) -> str:
    L = ctl['layout']
    img = ctl['image']
    idx = index_bindings(bindings)
    meta = ab['meta']
    controls = ctl['controls']
    sheet = L['sheetH']
    total = sheet * len(layers) + (sheet - img['h'] - L['imageDy'])

    out = [f'<svg viewBox="0 0 {img["w"]} {total}" role="img" aria-label="{ARIA}">',
           '<defs>',
           f'<image id="{img["id"]}" x="0" y="0" width="{img["w"]}" '
           f'height="{img["h"]}" href="{img["href"]}"/>',
           '</defs>']

    for i, spec in enumerate(layers):
        mods = tuple(sorted(spec['modifiers']))
        dy = i * sheet
        out += [f'<g transform="translate(0,{dy})" font-family="ui-monospace, Menlo, monospace">',
                f'<rect x="0" y="18" width="{img["w"]}" height="{L["headerH"]}" fill="{L["headBg"]}"/>',
                f'<rect x="0" y="18" width="10" height="{L["headerH"]}" fill="{L["accent"]}"/>',
                f'<text x="44" y="86" font-size="46" letter-spacing="4" '
                f'fill="{L["accent"]}">LAYER {spec["n"]}</text>',
                f'<text x="300" y="86" font-size="46" letter-spacing="3" '
                f'fill="{L["ink"]}">{spec["svgTitle"]}</text>',
                f'<text x="{img["w"] - 44}" y="86" font-size="38" letter-spacing="3" '
                f'fill="{L["headMuted"]}" text-anchor="end">{spec["svgChip"]}</text>',
                f'<g transform="translate(0,{L["imageDy"]})">',
                f'<use href="#{img["id"]}"/>']

        shades, held, labels = [], [], []
        for c in controls:
            if c['box'] is None and c['anchor'] is None:
                continue                                  # axis rows, table only
            cid = c['id']
            if cid in meta:
                spec_m = meta[cid]
                if cid.upper() in mods:
                    # The layer holds this modifier. Its field is tinted in the
                    # accent rather than shaded grey -- it is in use, not free --
                    # and says so instead of naming a command.
                    held.append(c['box'])
                    labels.append((c['anchor'], spec_m['held'], True,
                                   spec_m.get('heldTracking', '1')))
                    continue
                shades.append(c['box'])
                labels.append((c['anchor'], spec_m['text'], True, None))
                continue
            cmd = idx.get((c['input'], mods))
            if cmd is None:
                shades.append(c['box'])
            else:
                labels.append((c['anchor'], shorten(cmd, ab['map']), False, None))
        for box in ctl['unassignedTemplateFields']:
            shades.append(box)

        for x, y, w, h in held:
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                       f'fill="{L["accent"]}" fill-opacity="{L["heldShade"]}"/>')
        for x, y, w, h in shades:
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                       f'fill="#000" fill-opacity="{L["shade"]}"/>')
        for (ax, ay), text, accent, tracking in labels:
            fill = L['accent'] if accent else L['ink']
            track = tracking or L['letterSpacing']
            out.append(f'<text x="{ax}" y="{ay}" font-size="{L["fontSize"]}" '
                       f'letter-spacing="{track}" fill="{fill}">'
                       f'{esc(text)}</text>')
        out.append('</g></g>')
    out.append('</svg>')
    return '\n'.join(out)


def _is_axis(control, bindings) -> bool:
    if control.get('role'):
        return True
    return any(b['input'] == control['input'] and b.get('kind') == 'axis'
               for b in bindings)


def _shares_prefix(a: str, b: str) -> bool:
    return bool(a) and bool(b) and a.split(' ')[0] == b.split(' ')[0]


def _is_axis(control, bindings) -> bool:
    if control.get('role'):
        return True
    return any(b['input'] == control['input'] and b.get('kind') == 'axis'
               for b in bindings)


def _join_arms(cells):
    """'A3 up'+'A3 down' -> 'A3 &#8593; / &#8595;'; identical names collapse."""
    uniq = list(dict.fromkeys(cells))
    if len(uniq) == 1:
        return esc(uniq[0])
    heads = {c.split(' ')[0] for c in uniq}
    if len(heads) == 1 and all(' ' in c for c in uniq):
        head = uniq[0].split(' ')[0]
        return esc(head + ' ' + ' / '.join(c.split(' ', 1)[1] for c in uniq))
    return esc(' / '.join(uniq))


def _join_binds(binds):
    """Render one Bind cell.

    Axis binds are prose in the original, not <code>, because they name an axis
    rather than a DCS command. Where two commands share a leading phrase the post
    drops the repeat -- but only when what remains is a bare sense word, so
    "Weapon Function CW / CCW" collapses and "Speedbrake Open / Close" does not.
    """
    live = [b for b in binds if b]
    if not live:
        return ''
    if len({v for _, v in live}) == 1:
        live = live[:1]
    texts = [v for _, v in live]
    if len(texts) == 2:
        a, b = (t.split(' ') for t in texts)
        common = 0
        while common < len(a) - 1 and common < len(b) - 1 and a[common] == b[common]:
            common += 1
        tail = ' '.join(b[common:])
        if common and tail.upper() in SENSE_WORDS:
            texts = [texts[0], tail]
    return ' / '.join(
        f'<code>{esc(t)}</code>' if kind == 'code' else esc(t)
        for (kind, _), t in zip(live, texts))


def _row(chunk) -> str:
    vkb = _join_arms([c['vkb'] for c, _, _ in chunk])
    btn = ' / '.join(dict.fromkeys(c['button'] for c, _, _ in chunk))
    txt = _join_binds([(k, v) for _, k, v in chunk])
    return (f'        <tr><td class="pn">{vkb}</td>'
            f'<td class="num">{btn}</td><td>{txt}</td></tr>')


def render_tables(ctl, layers, ab, bindings) -> str:
    """One table per layer.

    Row shape follows the original: the two arms of a hat share a row only when
    they carry two senses of the same command ("Trim Nose Down / Up"); unrelated
    commands on the same hat get a row each. The spare button and the two
    modifiers are described once, on the unmodified layer, because they are
    hardware notes rather than bindings.
    """
    idx = index_bindings(bindings)
    meta = ab['meta']
    by_id = {c['id']: c for c in ctl['controls']}
    pair_max = ctl['layout'].get('pairMaxChars', 14)
    out = []
    for spec in layers:
        mods = tuple(sorted(spec['modifiers']))
        base = not mods
        rows = []
        for group in ctl['rows']:
            entries = []
            for cid in group:
                c = by_id[cid]
                if cid in meta:
                    if base:
                        entries.append((c, 'raw', meta[cid]['table']))
                    continue
                if c.get('role'):
                    if base:
                        entries.append((c, 'raw', c['role']))
                    continue
                cmd = idx.get((c['input'], mods))
                if cmd:
                    entries.append((c, 'raw' if _is_axis(c, bindings) else 'code', cmd))
            if not entries:
                continue
            chunks = [[entries[0]]]
            for e in entries[1:]:
                prev = chunks[-1][-1]
                # Two arms of one hat share a row when they read as one idea:
                # a shared leading phrase, or two labels short enough that the
                # combined cell stays scannable. Anything longer gets its own
                # row, which is what the original does for the unrelated
                # commands stacked on the POV hat in layers 2 and 4.
                short = max(len(prev[2]), len(e[2])) <= pair_max
                together = (e[2] == prev[2] or _shares_prefix(prev[2], e[2]) or short
                            or (len(group) > 2 and e[1] == 'raw' == prev[1]))
                if together:
                    chunks[-1].append(e)
                else:
                    chunks.append([e])
            rows.extend(_row(c) for c in chunks)
        if not rows:
            rows.append('        <tr><td class="pn">&mdash;</td>'
                        '<td class="num">&mdash;</td>'
                        '<td>Nothing mapped on this layer</td></tr>')
        out.append(
            f'    <div class="layerhead"><h3>Layer {spec["n"]} &mdash; {spec["title"]}'
            f'</h3><span class="modchip">{spec["chip"]}</span></div>\n'
            '    <div class="scroller"><table>\n'
            '      <thead><tr><th>VKB control</th><th>Button</th><th>Bind</th></tr>'
            '</thead><tbody>\n' + '\n'.join(rows) +
            '\n      </tbody></table></div>')
    return '\n\n'.join(out)


def main(bindings_path=None):
    ctl, layers, ab = load()
    src = pathlib.Path(bindings_path or DATA / 'bindings.json')
    bindings = json.loads(src.read_text(encoding='utf-8'))['bindings']
    return render_svg(ctl, layers, ab, bindings), render_tables(ctl, layers, ab, bindings)


if __name__ == '__main__':
    import sys
    svg, tables = main(sys.argv[1] if len(sys.argv) > 1 else None)
    pathlib.Path('/tmp/a4ework/out_vkb.svg').write_text(svg)
    pathlib.Path('/tmp/a4ework/out_vkb_tables.html').write_text(tables)
    print(f'svg    {len(svg)} chars, {svg.count(chr(10)) + 1} lines')
    print(f'tables {len(tables)} chars')
