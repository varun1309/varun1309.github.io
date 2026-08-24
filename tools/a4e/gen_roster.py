#!/usr/bin/env python3
"""
Build controls.json / layers.json / abbrev.json / bindings_current.json.

The roster below is the one piece of this toolchain that needed a human: which
physical VKB control sits at which label field, and what DCS calls that control.
Everything else (box, anchor, current labels) is joined in from the geometry
harvest, so a typo here shows up immediately as a shifted label in the round-trip
check rather than silently.

`input` is the join key against a DCS .lua. If DCS reports your stick's hat as
POV2 rather than POV1, or the analog wheel as JOY_RZ rather than JOY_SLIDER1,
correct it here and nowhere else.
"""
import json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / 'data'
GEO = json.loads((DATA / '_vkb_geometry.json').read_text())

# id, VKB control name, DCS input, button label for the table, L1 anchor label
ROSTER = [
    ('throttle',  'Base analog wheel', 'JOY_SLIDER1',      'Alog',  'THROTTLE AXIS'),
    ('fire1',     'Fire 1',            'JOY_BTN1',         '1',     'GUN-ROCKET FIRE'),
    ('fire2',     'Fire 2',            'JOY_BTN2',         '2',     'BOMB RELEASE'),
    ('pov_u',     'POV &#8593;',        'JOY_BTN_POV1_U',   '&mdash;', 'TRIM NOSE DN'),
    ('pov_d',     'POV &#8595;',        'JOY_BTN_POV1_D',   '&mdash;', 'TRIM NOSE UP'),
    ('pov_l',     'POV &#8592;',        'JOY_BTN_POV1_L',   '&mdash;', 'TRIM L WING DN'),
    ('pov_r',     'POV &#8594;',        'JOY_BTN_POV1_R',   '&mdash;', 'TRIM R WING DN'),
    ('pov_ul',    'POV &#8598;',        'JOY_BTN_POV1_UL',  '&mdash;', 'FORCE CURSOR'),
    ('a2',        'A2 (red)',          'JOY_BTN3',         '3',     'CHAFF CYCLE'),
    ('b1',        'B1 SpeedFire',      'JOY_BTN4',         '4',     'RADIO MIC PTT'),
    ('d1',        'D1',                'JOY_BTN5',         '5',     'WHEEL BRAKE'),
    ('a3_u',      'A3 &#8593;',         'JOY_BTN6',         '6',     'SPEEDBRAKE OPEN'),
    ('a3_d',      'A3 &#8595;',         'JOY_BTN8',         '8',     'SPEEDBRAKE CLOSE'),
    ('a3_l',      'A3 &#8592;',         'JOY_BTN9',         '9',     'FLAPS UP (HOLD)'),
    ('a3_r',      'A3 &#8594;',         'JOY_BTN7',         '7',     'FLAPS DN (HOLD)'),
    ('a3_push',   'A3 push',           'JOY_BTN10',        '10',    'GEAR UP/DOWN'),
    ('a4_u',      'A4 &#8593;',         'JOY_BTN11',        '11',    'AFCS ENGAGE/OFF'),
    ('a4_d',      'A4 &#8595;',         'JOY_BTN13',        '13',    'AFCS ALT/OFF'),
    ('a4_l',      'A4 &#8592;',         'JOY_BTN14',        '14',    'APC POWER STBY'),
    ('a4_r',      'A4 &#8594;',         'JOY_BTN12',        '12',    'APC PWR ENGAGE'),
    ('a4_push',   'A4 push',           'JOY_BTN15',        '15',    'AFCS SEL/OFF'),
    ('c1_u',      'C1 &#8593;',         'JOY_BTN16',        '16',    'WPN FUNC CW'),
    ('c1_d',      'C1 &#8595;',         'JOY_BTN18',        '18',    'WPN FUNC CCW'),
    ('c1_l',      'C1 &#8592;',         'JOY_BTN19',        '19',    'GUN READY'),
    ('c1_r',      'C1 &#8594;',         'JOY_BTN17',        '17',    'PROFILE/PLAN'),
    ('c1_push',   'C1 push',           'JOY_BTN20',        '20',    'MASTER ARM ON'),
    ('en2_cw',    'En2',               'JOY_BTN23',        '23',    'AFCS HDG INC'),
    ('en2_ccw',   'En2',              'JOY_BTN24',        '24',    'AFCS HDG DEC'),
    ('en1_cw',    'En1',               'JOY_BTN25',        '25',    'ANT TILT CW'),
    ('en1_ccw',   'En1',              'JOY_BTN26',        '26',    'ANT TILT CCW'),
    ('f1',        'F1',                'JOY_BTN27',        '27',    'SPARE / UNUSED'),
    ('f2',        'F2',                'JOY_BTN28',        '28',    'F2 MODIFIER'),
    ('f3',        'F3',                'JOY_BTN29',        '29',    'F3 MODIFIER'),
]

# controls with no field on the template -- table rows only
AXES_ONLY = [
    ('axis_x', 'X', 'JOY_X',  'axes', 'Roll'),
    ('axis_y', 'Y', 'JOY_Y',  'axes', 'Pitch'),
    ('axis_z', 'Z', 'JOY_RZ', 'axes', 'Rudder'),
]

# rows in the printed tables pair the two arms of a hat; keep that shape
ROWS = [
    ['throttle'], ['axis_x', 'axis_y', 'axis_z'], ['fire1'], ['fire2'],
    ['pov_u', 'pov_d'], ['pov_l', 'pov_r'], ['pov_ul'],
    ['a2'], ['b1'], ['d1'],
    ['a3_u', 'a3_d'], ['a3_l', 'a3_r'], ['a3_push'],
    ['a4_u', 'a4_d'], ['a4_l', 'a4_r'], ['a4_push'],
    ['c1_u', 'c1_d'], ['c1_l', 'c1_r'], ['c1_push'],
    ['en2_cw', 'en2_ccw'], ['en1_cw', 'en1_ccw'],
    ['f1'], ['f2', 'f3'],
]

LAYERS = [
    {'modifiers': [],             'n': 1, 'title': 'fly &amp; fire',
     'svgTitle': 'FLY &amp; FIRE', 'chip': 'No modifier', 'svgChip': 'NO MODIFIER'},
    {'modifiers': ['F2'],         'n': 2, 'title': 'flight config &amp; sensors',
     'svgTitle': 'FLIGHT CONFIG &amp; SENSORS', 'chip': 'Hold F2', 'svgChip': 'HOLD F2'},
    {'modifiers': ['F3'],         'n': 3, 'title': 'weapons',
     'svgTitle': 'WEAPONS', 'chip': 'Hold F3', 'svgChip': 'HOLD F3'},
    {'modifiers': ['F2', 'F3'],   'n': 4, 'title': 'carrier ops &amp; housekeeping',
     'svgTitle': 'CARRIER OPS &amp; HOUSEKEEPING', 'chip': 'Hold F2 + F3',
     'svgChip': 'HOLD F2 + F3'},
]

# DCS command name -> the short form that fits a 347-unit label field.
ABBREV = {
    'Gun-Rocket Trigger': 'GUN-ROCKET FIRE', 'Bomb Release': 'BOMB RELEASE',
    'Trim Nose Down': 'TRIM NOSE DN', 'Trim Nose Up': 'TRIM NOSE UP',
    'Trim Left Wing Down': 'TRIM L WING DN',
    'Trim Right Wing Down': 'TRIM R WING DN',
    'Force Cursor To Show Toggle': 'FORCE CURSOR',
    'Chaff Dispenser Cycle': 'CHAFF CYCLE', 'Radio Mic PTT': 'RADIO MIC PTT',
    'Wheel Brake On Else Off': 'WHEEL BRAKE',
    'Speedbrake Open': 'SPEEDBRAKE OPEN', 'Speedbrake Close': 'SPEEDBRAKE CLOSE',
    'Flaps Handle Up Else Stop': 'FLAPS UP (HOLD)',
    'Flaps Handle Down Else Stop': 'FLAPS DN (HOLD)',
    'Landing Gear Up/Down': 'GEAR UP/DOWN',
    'AFCS Engage/Off': 'AFCS ENGAGE/OFF', 'AFCS ALT/Off': 'AFCS ALT/OFF',
    'APC Power Stby': 'APC POWER STBY', 'APC Power Engage': 'APC PWR ENGAGE',
    'AFCS SEL/Off': 'AFCS SEL/OFF',
    'Weapon Function CW': 'WPN FUNC CW', 'Weapon Function CCW': 'WPN FUNC CCW',
    'Gun Ready': 'GUN READY', 'Profile/Plan': 'PROFILE/PLAN',
    'Master Armament On': 'MASTER ARM ON',
    'AFCS HDG Continuous Inc': 'AFCS HDG INC',
    'AFCS HDG Continuous Dec': 'AFCS HDG DEC',
    'Antenna Tilt Rotary CW': 'ANT TILT CW',
    'Antenna Tilt Rotary CCW': 'ANT TILT CCW',
    'Throttle': 'THROTTLE AXIS', 'Throttle axis': 'THROTTLE AXIS',
    'Exterior Lights On/Off': 'EXT LIGHTS', 'NVG Toggle': 'NVG TOGGLE',
    'NVG Gain Decrease': 'NVG GAIN DEC', 'NVG Gain Increase': 'NVG GAIN INC',
    'AWRS Qty Select CW': 'AWRS QTY CW', 'AWRS Qty Select CCW': 'AWRS QTY CCW',
    'AWRS Mode CCW': 'AWRS MODE CCW', 'AWRS Mode CW': 'AWRS MODE CW',
    'Catapult Hook-Up': 'CATAPULT HOOK', 'Pilot Salute': 'PILOT SALUTE',
    'Canopy Open/Close': 'CANOPY OPN/CLS', 'JATO Button': 'JATO BUTTON',
    'VOIP PTT': 'VOIP PTT',
}

# labels that are about the mapping rather than a DCS command
# `held` is what a modifier's own field says on the layer that holds it: the
# button is not available for a binding there, so the drawing states why rather
# than shading the field as if it were free.
META = {
    'f1': {'text': 'SPARE / UNUSED', 'accent': True,
           'table': 'Spare &mdash; deliberately unassigned'},
    'f2': {'text': 'F2 MODIFIER', 'accent': True, 'table': 'Modifiers',
           'held': 'HELD &#8212; MODIFIER', 'heldTracking': '1'},
    'f3': {'text': 'F3 MODIFIER', 'accent': True, 'table': 'Modifiers',
           'held': 'HELD &#8212; MODIFIER', 'heldTracking': '1'},
}

# the offset the author used from box origin to text baseline, per anchor
def main():
    boxof = {k: v for k, v in GEO['boxOfAnchor'].items()}
    derived = {f'{a[0]},{a[1]}' for a in GEO['derivedFromTemplate']}
    l1 = GEO['layers'][0]['labels']
    by_label = {v[0]: k for k, v in l1.items()}

    controls, missing = [], []
    for cid, vkb, inp, btn, l1label in ROSTER:
        key = by_label.get(l1label)
        if key is None:
            missing.append((cid, l1label))
            continue
        ax, ay = (int(v) for v in key.split(','))
        box = boxof.get(key)
        controls.append({
            'id': cid, 'vkb': vkb, 'input': inp, 'button': btn,
            'anchor': [ax, ay], 'box': box,
            'boxFromTemplate': key in derived,
            'accent': cid in META,
        })
    for cid, vkb, inp, btn, role in AXES_ONLY:
        controls.append({'id': cid, 'vkb': vkb, 'input': inp, 'button': btn,
                         'anchor': None, 'box': None, 'role': role,
                         'boxFromTemplate': False, 'accent': False})

    if missing:
        raise SystemExit(f'roster does not match the harvest: {missing}')

    # Label fields the post shades on every layer because no control owns them.
    # Taken from the harvest, not from JPG detection: the template has more
    # printed fields than the guide chooses to shade, and shading the extras
    # would change the drawing.
    taken = {tuple(c['box']) for c in controls if c['box']}
    spare = [list(b) for b in (tuple(x) for x in GEO['boxes']) if b not in taken]
    detected = json.loads((DATA / 'template_fields.json').read_text())['fields']
    unshaded = [f for f in detected
                if not any(abs(f[0] - t[0]) <= 20 and abs(f[1] - t[1]) <= 20
                           for t in list(taken) + [tuple(s) for s in spare])]

    out = {
        'note': 'One entry per physical VKB control. `input` is the join key '
                'against a DCS .lua; `box` shades the field when the control is '
                'unbound on a layer; `anchor` is the text baseline when it is bound.',
        'image': {'href': '/assets/img/vkb-gladiator-nxt-evo-template.jpg',
                  'id': 'a4eevo', 'w': 3300, 'h': 2550},
        'layout': {'sheetH': 2700, 'headerH': 104, 'imageDy': 150,
                   'fontSize': 26, 'letterSpacing': '0.5',
                   'ink': '#16180F', 'accent': '#8A5A0F',
                   'headBg': '#E7E5DD', 'headMuted': '#6A6D60', 'pairMaxChars': 14,
                   'shade': '0.055', 'heldShade': '0.20',
                   'shade': '0.055'},
        'rows': ROWS,
        'controls': controls,
        'unassignedTemplateFields': spare,
        'printedButUnused': {
            'note': 'Fields detected on the template JPG that no control owns '
                    'and the drawing leaves alone. Move one into a control entry '
                    'if you start using that button.',
            'fields': unshaded},
    }
    (DATA / 'controls.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    (DATA / 'layers.json').write_text(json.dumps(LAYERS, indent=2, ensure_ascii=False) + '\n')
    (DATA / 'abbrev.json').write_text(json.dumps(
        {'note': 'DCS command name -> short label for the template field. '
                 'Anything absent falls back to shorten() in render_vkb.py.',
         'map': ABBREV, 'meta': META}, indent=2, ensure_ascii=False) + '\n')
    print(f'controls.json  {len(controls)} controls '
          f'({sum(1 for c in controls if c["boxFromTemplate"])} boxes recovered from JPG, '
          f'{len(spare)} shaded spare, {len(unshaded)} printed-but-unused)')
    print(f'layers.json    {len(LAYERS)} layers')
    print(f'abbrev.json    {len(ABBREV)} abbreviations')


if __name__ == '__main__':
    main()
