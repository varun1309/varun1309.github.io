# Regenerating the A-4E-C post

The HOTAS drawing and its four tables are generated from data. Re-map your stick
in DCS, export the profile, run one command, and the template picture and the
tables both follow.

```bash
python3 tools/a4e/build.py ~/path/Gladiator.diff.lua modifiers.lua default.lua
```

Arguments go in any order — each `.lua` is classified by reading it. Then preview:

```bash
bundle exec jekyll serve     # needs Ruby 3+; the macOS system Ruby (2.6) is too old
```

## There are no images to render

Every drawing in the post is inline SVG, so "rendering" is text generation — no
rasteriser, no image pipeline, no binary assets to regenerate. The one real image
is the VKB template photograph, which is `<use>`d four times and never redrawn.

## What comes from where

| File | What it holds |
|---|---|
| `data/controls.json` | one entry per physical VKB control: its DCS input name, its label field on the template, its text baseline |
| `data/layers.json` | the four modifier layers and their titles |
| `data/abbrev.json` | DCS command name → the short form that fits a label field |
| `data/bindings.json` | the effective bindings, rewritten by `build.py` from your `.lua` |
| `data/cockpit.json` | page 1, the plan-view cockpit map |
| `data/navchain.json` | page 2, the navigation flow diagram |
| `data/template_fields.json` | label fields detected on the template JPG, for reference |
| `data/_vkb_geometry.json` | raw harvest output; only `harvest.py` writes it |

Pages 1 and 2 are **not** derived from any `.lua` — a cockpit is laid out in space
and the nav chain is a set of system relationships, and no DCS export knows
either. They are data-driven so that adding a panel or recolouring a system
family is a line of JSON instead of hand-edited SVG coordinates.

## Which .lua to export

* `Saved Games/DCS/Config/Input/A-4E-C/joystick/<device>.diff.lua` — your
  bindings. **Holds only the changes from default**, so pass it together with:
* `Mods/aircraft/A-4E-C/Input/A-4E-C/joystick/default.lua` — the mod's own
  catalogue. Without it, a control still sitting on the DCS default is
  indistinguishable from an unbound one and renders as unbound.
* `Saved Games/DCS/Config/Input/modifiers.lua` — what makes `JOY_BTN28` display
  as `F2`. Without it, layers whose modifier is not literally named `F2`/`F3`
  come out empty.

No Lua runtime is needed; `lua.py` reads the table format directly.

## When something looks wrong

`build.py` prints, every run:

* added and removed bindings versus the previous state;
* bindings on inputs no control claims — a keyboard bind, a second device, or a
  button missing from the roster. These are **not drawn**, and saying so is the
  point: nothing is silently dropped;
* labels too long for a 347-unit field, as a copy-pasteable `abbrev.json` line;
* which of the four regions actually changed.

If a label lands in the wrong place, fix that control's `anchor`/`box` in
`controls.json`. If a whole control is misidentified, its `input` is wrong — that
is the only join key between the drawing and DCS.

## Layout rules the renderer follows

Read off the hand-authored original rather than invented:

* a control's label field is shaded when it carries no binding on that layer;
* a modifier held by a layer gets an accent tint and reads `HELD — MODIFIER`,
  because that field is in use rather than free;
* the spare button is always shaded and always labelled;
* two arms of one hat share a table row when they read as one idea — a shared
  leading phrase, or two labels under `layout.pairMaxChars` characters;
* a shared prefix is dropped only when what remains is a bare sense word, so
  "Weapon Function CW / CCW" collapses and "Speedbrake Open / Close" does not.

## Checks

```bash
python3 tools/a4e/selftest.py     # do the data files still describe the post?
python3 tools/a4e/build.py --check   # exit 1 if the post is stale
python3 tools/a4e/build.py --dry-run # render and report, write nothing
```

`selftest.py` compares element-by-element: attributes and text must match, while
whitespace and the order of non-overlapping siblings may differ.

## Re-harvesting

`harvest.py` and `gen_roster.py` rebuilt the data files from the hand-authored
SVGs and are kept for provenance. You only need them if the post is re-authored
by hand. `harvest.py` recovers the four POV label boxes that no layer shades by
detecting the printed fields on the template JPG (needs Pillow + numpy).

## Files

```
lua.py           Lua table reader, no runtime required
dcs.py           .lua -> normalised bindings; merges default + diff
render_vkb.py    page 3: the template SVG and the four tables
render_pages.py  page 1 and page 2
inject.py        marker-fenced in-place replacement
build.py         the entry point
selftest.py      round-trip check
harvest.py       one-off: post SVGs -> data (provenance)
gen_roster.py    one-off: the control roster (provenance)
```

The post carries four fences; everything outside them is hand-written prose and
is never touched:

```html
<!-- a4e:gen vkb-svg --> ... <!-- /a4e:gen vkb-svg -->
```
