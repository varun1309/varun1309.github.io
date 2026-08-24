# Updating the HOTAS mapping after a re-map

The keybind drawing and its tables are generated from
`assets/config/a4ec.cfg.diff.lua`, the DCS export that lives in this repo.
Re-map in DCS, replace that one file, run one command.

```bash
# 1. export from DCS, then overwrite the config in the repo
cp "/path/to/Saved Games/DCS/Config/Input/A-4E-C/joystick/<device>.diff.lua" \
   assets/config/a4ec.cfg.diff.lua

# 2. see what would change, without writing anything
python3 tools/a4e/build.py --dry-run assets/config/a4ec.cfg.diff.lua

# 3. do it
python3 tools/a4e/build.py assets/config/a4ec.cfg.diff.lua

# 4. check and commit
python3 tools/a4e/selftest.py
git add -A && git commit && git push
```

Step 2 is worth doing every time. It prints the whole reconciliation before
touching the post, and everything you need to react to is in that output.

## Where DCS keeps the file

Exact paths vary by install — `DCS.openbeta` versus `DCS`, a relocated Saved
Games folder, the mod in the game directory versus Saved Games. Search for the
filename rather than trusting a path. In DCS, **Controls → Save profile as…**
also writes the same shape.

Optionally pass two more files, in any order — each is classified by reading it:

| File | Why you might add it |
|---|---|
| `.../Mods/aircraft/A-4E-C/Input/A-4E-C/joystick/default.lua` | A diff holds **only your changes**. Without the default, a control still sitting on the DCS default renders as unbound. |
| `Saved Games/DCS/Config/Input/modifiers.lua` | Only needed if your export stores modifiers as raw buttons (`JOY_BTN28`) rather than names (`F2`). The current config stores names, so this is not needed — and `build.py` only asks for it when it sees raw names. |

## Reading the report

Four things get printed. Each has a specific response.

**Added and removed bindings.** Sanity-check the list against what you actually
changed in DCS. A long `-` list with a short `+` list usually means a file is
missing rather than that you unbound thirty things.

**`bindings on inputs the roster does not describe`.** A binding on a button the
drawing has no slot for — a keyboard bind, a second device, or a control missing
from the roster. These are listed but **not drawn**. To place one, add an entry
to `data/controls.json` with its `input`, plus a `box` and `anchor` for its
printed field on the template. To leave it in the tables only, add the entry with
`"box": null, "anchor": null`.

**`label(s) too long ... and clipped`.** Real DCS command names run long
(`Trim Switch - NOSE DOWN`). A field holds **16 characters**. The report emits
copy-pasteable lines; paste them into `data/abbrev.json` under `map` and edit the
short form to something you would actually want printed:

```json
"AN/ARN-52 TACAN Mode Switch - CCW": "TACAN MODE CCW",
```

Without an entry the label still renders, just truncated with an ellipsis.

**`per layer`.** Counts per modifier combination. A layer showing `0` when you
expect binds means its modifier name in `data/layers.json` does not match the
name in the export's `reformers`.

## A new modifier

If you add one in DCS, add a layer to `data/layers.json`. `modifiers` must match
the names the export uses, spelled identically:

```json
{ "modifiers": ["Pinky"], "n": 5, "title": "zoom",
  "svgTitle": "ZOOM", "chip": "Hold Pinky", "svgChip": "HOLD PINKY" }
```

The template sheet, its heading and its table all follow. Sheet height, the SVG
`viewBox` and the aria-label are all derived from the layer count.

## When a label lands in the wrong place

That control's `anchor` (text baseline) or `box` (the shaded field) is wrong in
`data/controls.json`. Most likely on a control that had no binding before, since
those coordinates had never been exercised. `data/template_fields.json` lists
every printed field detected on the template JPG, in the same units, which is the
quickest way to find the right numbers.

## Checks

```bash
python3 tools/a4e/selftest.py            # do the data files still describe the post?
python3 tools/a4e/build.py --check       # exit 1 if the post is stale
python3 tools/a4e/build.py --dry-run …   # render and report, write nothing
```

Re-running `build.py` is idempotent: a second run reports `nothing (already
current)`.

## Previewing

```bash
bundle exec jekyll serve      # http://localhost:4000
```

Needs Ruby 3+. The macOS system Ruby (2.6) is too old, so this needs
`brew install ruby` or rbenv first.

Without Jekyll you can still check the generated markup by opening the post body
in a browser — strip the front matter, wrap it in a minimal HTML page, and serve
the repo root so `/assets/img/...` resolves. What that catches, and Jekyll does
not, is label overflow: no label may be wider than 271 units, measured with
`getBBox()`.

## Commit the data too

`build.py` rewrites `data/bindings.json` from your export. Commit it — a bare
`python3 tools/a4e/build.py` with no arguments redraws from it, so it is the
record of the published mapping, not a scratch file.

## Gotchas seen in real exports

- **`changed`** — DCS writes this instead of `added` when a combo's filter
  (curve, deadzone, invert) is edited but the binding stays. It counts as a live
  binding; a parser that only reads `added` silently drops it.
- **`removed` without the default** — removals reference bindings that only exist
  in `default.lua`. Harmless, but they cannot be applied unless you pass it.
- **Modifier spelling** — `reformers` may hold names (`F2`) or raw buttons
  (`JOY_BTN28`). Names need no `modifiers.lua`; raw buttons do.

See `README.md` in this directory for how the generator is put together and what
each file does.
