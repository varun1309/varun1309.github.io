"""
Turn DCS input .lua files into one flat list of effective bindings.

Accepts either shape without being told which:

  * a Saved Games profile     Config/Input/A-4E-C/joystick/<device>.diff.lua
    -> {keyDiffs = {...}, axisDiffs = {...}}, holding only the deltas from
       default, each with `added` and/or `removed` combo lists.
  * a mod default             Mods/aircraft/A-4E-C/Input/A-4E-C/joystick/default.lua
    -> {keyCommands = {...}, axisCommands = {...}}, the full catalogue with
       display names and categories.
  * Config/Input/modifiers.lua -> {name = {device=, key=}}, which is what turns
    JOY_BTN28 into the label "F2".

A diff on its own cannot tell "unbound" from "bound to the mod default", so pass
the default alongside the diff to get a complete picture. `merge()` applies
removals then additions, the same order DCS does.
"""
from __future__ import annotations

import dataclasses
import pathlib
import re

import lua


@dataclasses.dataclass(frozen=True)
class Binding:
    kind: str                # 'key' | 'axis'
    command: str             # display name, exactly as the DCS UI shows it
    input: str               # 'JOY_BTN6', 'JOY_BTN_POV1_U', 'JOY_RZ', ...
    modifiers: tuple         # ('JOY_BTN28',) -- raw keys, resolve with a ModifierMap
    cmd_id: str = ''
    category: str = ''
    origin: str = ''         # 'default' | 'diff'

    @property
    def is_axis(self) -> bool:
        return self.kind == 'axis'

    def key(self):
        return (self.input, tuple(sorted(self.modifiers)))


def _listish(v):
    """DCS writes both [1]={...} tables and bare lists; yield values in order."""
    if v is None:
        return []
    if isinstance(v, dict):
        num = sorted((k for k in v if isinstance(k, int)))
        if num:
            return [v[k] for k in num]
        return [v]
    if isinstance(v, list):
        return v
    return [v]


def _combos(entry):
    """Combo list from any of the three field names DCS has used."""
    for field in ('combos', 'added', 'removed'):
        if field in entry:
            yield field, _listish(entry[field])


def _modifiers_of(combo) -> tuple:
    mods = _listish(combo.get('reformers'))
    return tuple(str(m) for m in mods if isinstance(m, str))


def _shape(tbl: dict) -> str:
    if 'keyDiffs' in tbl or 'axisDiffs' in tbl:
        return 'diff'
    if 'keyCommands' in tbl or 'axisCommands' in tbl:
        return 'default'
    # modifiers.lua: flat map of name -> {device=, key=}
    vals = [v for v in tbl.values() if isinstance(v, dict)]
    if vals and all('key' in v and 'combos' not in v and 'added' not in v
                    for v in vals):
        return 'modifiers'
    raise ValueError('unrecognised DCS input file: no keyDiffs/keyCommands/'
                     'modifier entries found')


def read(path) -> tuple:
    """-> (shape, parsed table). shape is 'diff' | 'default' | 'modifiers'."""
    tbl = lua.load(path)
    if not isinstance(tbl, dict):
        raise ValueError(f'{path}: expected a table, got {type(tbl).__name__}')
    return _shape(tbl), tbl


class ModifierMap:
    """JOY_BTN28 <-> 'F2'."""

    def __init__(self, table: dict | None = None):
        self.by_key = {}
        for name, spec in (table or {}).items():
            if isinstance(spec, dict) and isinstance(spec.get('key'), str):
                self.by_key[spec['key']] = str(name)

    @classmethod
    def load(cls, path):
        shape, tbl = read(path)
        if shape != 'modifiers':
            raise ValueError(f'{path}: looks like a {shape} file, not modifiers.lua')
        return cls(tbl)

    def name(self, key: str) -> str:
        return self.by_key.get(key, key)

    def names(self, keys) -> tuple:
        return tuple(sorted(self.name(k) for k in keys))


def _parse_default(tbl: dict):
    added = []
    for kind, field in (('key', 'keyCommands'), ('axis', 'axisCommands')):
        for entry in _listish(tbl.get(field)):
            if not isinstance(entry, dict):
                continue
            name = str(entry.get('name', '') or '')
            cid = str(entry.get('_id', entry.get('id', '')) or '')
            cat = entry.get('category')
            cat = ' / '.join(str(c) for c in _listish(cat)) if cat else ''
            for combo in _listish(entry.get('combos')):
                if isinstance(combo, dict) and isinstance(combo.get('key'), str):
                    added.append(Binding(kind, name, combo['key'],
                                         _modifiers_of(combo), cid, cat, 'default'))
    return added, []


def _parse_diff(tbl: dict):
    added, removed = [], []
    for kind, field in (('key', 'keyDiffs'), ('axis', 'axisDiffs')):
        for cid, entry in (tbl.get(field) or {}).items():
            if not isinstance(entry, dict):
                continue
            name = str(entry.get('name', '') or '')
            for which, combos in _combos(entry):
                if which == 'combos':
                    continue
                for combo in combos:
                    if not (isinstance(combo, dict) and isinstance(combo.get('key'), str)):
                        continue
                    b = Binding(kind, name, combo['key'], _modifiers_of(combo),
                                str(cid), '', 'diff')
                    (added if which == 'added' else removed).append(b)
    return added, removed


def parse(path) -> tuple:
    """-> (added, removed) lists of Binding for one file."""
    shape, tbl = read(path)
    if shape == 'modifiers':
        raise ValueError(f'{path}: modifiers.lua carries no bindings; '
                         'pass it as --modifiers')
    return (_parse_default if shape == 'default' else _parse_diff)(tbl)


def merge(default_files=(), diff_files=()) -> list:
    """Effective bindings: defaults, then each diff's removals, then additions."""
    live: dict = {}
    names: dict = {}

    def remember(b: Binding):
        if b.command:
            names.setdefault(b.cmd_id, b.command)
        if b.category:
            names.setdefault(('cat', b.cmd_id), b.category)

    for p in default_files:
        add, _ = parse(p)
        for b in add:
            remember(b)
            live[b.key()] = b
    for p in diff_files:
        add, rem = parse(p)
        for b in add + rem:
            remember(b)
        for b in rem:
            live.pop(b.key(), None)
            # a removal may name only the command, with the combo already gone
            for k, v in list(live.items()):
                if b.cmd_id and v.cmd_id == b.cmd_id and b.input == v.input:
                    live.pop(k, None)
        for b in add:
            live[b.key()] = b

    out = []
    for b in live.values():
        cmd = b.command or names.get(b.cmd_id, '') or b.cmd_id
        cat = b.category or names.get(('cat', b.cmd_id), '')
        out.append(dataclasses.replace(b, command=cmd, category=cat))
    out.sort(key=lambda b: (len(b.modifiers), sorted(b.modifiers), _input_sort(b.input)))
    return out


def _input_sort(inp: str):
    m = re.match(r'JOY_BTN(\d+)$', inp)
    return (0, int(m.group(1)), '') if m else (1, 0, inp)


def describe(bindings, mods: ModifierMap | None = None) -> str:
    mods = mods or ModifierMap()
    by_layer: dict = {}
    for b in bindings:
        by_layer.setdefault(mods.names(b.modifiers), []).append(b)
    lines = []
    for layer in sorted(by_layer, key=lambda t: (len(t), t)):
        tag = ' + '.join(layer) if layer else 'no modifier'
        lines.append(f'[{tag}]  {len(by_layer[layer])} bindings')
        for b in by_layer[layer]:
            lines.append(f'    {b.input:<22} {b.command}')
    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    for p in sys.argv[1:]:
        shape, _ = read(p)
        print(f'== {pathlib.Path(p).name}: {shape}')
    files = [p for p in sys.argv[1:] if read(p)[0] != 'modifiers']
    mfiles = [p for p in sys.argv[1:] if read(p)[0] == 'modifiers']
    mm = ModifierMap.load(mfiles[0]) if mfiles else ModifierMap()
    defs = [p for p in files if read(p)[0] == 'default']
    difs = [p for p in files if read(p)[0] == 'diff']
    print(describe(merge(defs, difs), mm))
