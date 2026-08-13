#!/usr/bin/env python3
"""
Port the standalone A-4E-C guide into a Jekyll post.

Two problems to solve:
  1. The guide ships a complete stylesheet that styles bare `body`, `h1`,
     `table`, `code` etc. Dropped into the site as-is it would fight main.css
     in both directions. So: rename every custom property to --a4e-* and
     prefix every selector with .a4e, turning it into a scoped component.
  2. The template photo is a ~325 KB base64 data URI. In a git repo that
     belongs on disk as a real asset, served and cached normally.
"""
import base64, re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC  = pathlib.Path(sys.argv[1])  # path to the standalone guide HTML
POST = ROOT / '_posts' / '2026-08-13-a4e-c-cockpit-avionics.html'
IMG  = ROOT / 'assets' / 'img' / 'vkb-gladiator-nxt-evo-template.jpg'
IMG_URL = '/assets/img/vkb-gladiator-nxt-evo-template.jpg'

html = SRC.read_text(encoding='utf-8')

# ---------------------------------------------------------------- 1. split
m = re.search(r'<style>(.*?)</style>', html, re.S)
css = m.group(1)
body = html[m.end():]
# drop the <title> tag; the Jekyll layout owns the document title
body = re.sub(r'<title>.*?</title>\s*', '', html[:m.start()], flags=re.S) + body

# ------ 1b. drop the guide's own masthead; the layout owns title/standfirst.
# Keep its lede paragraphs — they carry framing the standfirst doesn't.
mh = re.search(r'<header class="masthead">(.*?)</header>', body, re.S)
if mh:
    ledes = re.findall(r'<p class="lede">.*?</p>', mh.group(1), re.S)
    body = body[:mh.start()] + '<div class="intro">\n' + '\n'.join(ledes) \
           + '\n  </div>' + body[mh.end():]

# ------------------------------------------------- 2. extract the data URI
n_img = 0
def pull_image(mo):
    global n_img
    n_img += 1
    IMG.parent.mkdir(parents=True, exist_ok=True)
    IMG.write_bytes(base64.b64decode(mo.group(1)))
    return f'href="{IMG_URL}"'
body = re.sub(r'href="data:image/jpeg;base64,([A-Za-z0-9+/=]+)"', pull_image, body)

# --------------------------------------------- 3. rename custom properties
tokens = sorted(set(re.findall(r'--([a-zA-Z0-9-]+)\s*:', css)), key=len, reverse=True)
for t in tokens:
    css  = re.sub(rf'--{re.escape(t)}\b', f'--a4e-{t}', css)
    body = re.sub(rf'--{re.escape(t)}\b', f'--a4e-{t}', body)

# ------------------------------------------------- 4. avoid id collisions
for old, new in (('pg1', 'a4epg1'), ('pg2', 'a4epg2'), ('pg3', 'a4epg3'),
                 ('page1', 'a4epage1'), ('page2', 'a4epage2'), ('page3', 'a4epage3'),
                 ('evo', 'a4eevo'), ('stk', 'a4estk'), ('ar', 'a4ear'), ('a2', 'a4ea2')):
    css  = re.sub(rf'#{old}\b', f'#{new}', css)
    css  = re.sub(rf'\.{old}\b', f'.{new}', css)
    body = body.replace(f'id="{old}"', f'id="{new}"')
    body = body.replace(f'for="{old}"', f'for="{new}"')
    body = body.replace(f'href="#{old}"', f'href="#{new}"')
    body = body.replace(f'url(#{old})', f'url(#{new})')
    body = re.sub(rf'class="([^"]*)\b{old}\b([^"]*)"',
                  lambda mo: f'class="{mo.group(1)}{new}{mo.group(2)}"', body)

# ------------------------------------------------------ 5. scope selectors
def scope_selector(sel: str) -> str:
    sel = sel.strip()
    if not sel:
        return sel
    # token-only blocks stay at document root so the theme media query works
    if sel.startswith(':root'):
        return sel
    if sel == '*' or sel.startswith('*,'):
        return ', '.join('.a4e ' + s.strip() for s in sel.split(','))
    if sel == 'body':
        return '.a4e'
    out = []
    for part in sel.split(','):
        part = part.strip()
        if not part:
            continue
        out.append('.a4e' if part == 'body' else f'.a4e {part}')
    return ', '.join(out)

def scope_block(text: str) -> str:
    res, i, n = [], 0, len(text)
    while i < n:
        brace = text.find('{', i)
        if brace == -1:
            res.append(text[i:])
            break
        prelude = text[i:brace]
        # find the matching close brace
        depth, j = 1, brace + 1
        while j < n and depth:
            if text[j] == '{': depth += 1
            elif text[j] == '}': depth -= 1
            j += 1
        inner = text[brace + 1:j - 1]
        stripped = prelude.strip()
        if stripped.startswith('@'):
            at = stripped.split('{')[0]
            if at.startswith(('@media', '@supports')):
                res.append(prelude + '{' + scope_block(inner) + '}')
            else:                      # @font-face, @keyframes — leave alone
                res.append(prelude + '{' + inner + '}')
        else:
            # preserve comments sitting in front of the selector
            lead = ''
            cm = list(re.finditer(r'/\*.*?\*/', prelude, re.S))
            if cm:
                lead = prelude[:cm[-1].end()]
                prelude = prelude[cm[-1].end():]
            res.append(lead + '\n' + scope_selector(prelude) + ' {' + inner + '}')
        i = j
    return ''.join(res)

css = scope_block(css)

# Present the guide as an inset document rather than letting its warm paper
# butt straight against the site's cooler background.
css += '''

  /* ---- embedded-in-site adjustments ---- */
  .a4e {
    border: 1px solid var(--a4e-rule);
    border-radius: 10px;
    margin-top: 4px;
  }
  .a4e .wrap { padding: 36px 28px 60px; }
  .a4e .intro { margin-bottom: 4px; }
  .a4e .intro .lede:last-child { margin-bottom: 0; }
  @media (max-width: 620px) {
    .a4e .wrap { padding: 26px 16px 44px; }
  }
'''

# ------------------------------------------------------------- 6. assemble
front = '''---
layout: post
title: "DCS A-4E-C: where every avionics panel is, and how to work it"
standfirst: >-
  The Skyhawk labels half its cockpit by function and half by part number, which
  makes it look like systems are missing. A cockpit map, the operating procedure
  for each system with its real switch detents, and a four-layer HOTAS mapping.
description: >-
  A reference for the DCS A-4E-C Skyhawk: a plan-view cockpit map, per-system
  operating procedures with exact switch detents read from the mod source, and a
  four-layer VKB Gladiator NXT EVO keybind mapping.
embed: true
---

'''

POST.parent.mkdir(parents=True, exist_ok=True)
POST.write_text(front + '<div class="a4e">\n<style>\n' + css.strip()
                + '\n</style>\n' + body.strip() + '\n</div>\n', encoding='utf-8')

print(f'post      : {POST.relative_to(ROOT)}  ({POST.stat().st_size/1024:.0f} KB)')
print(f'image     : {IMG.relative_to(ROOT)}  ({IMG.stat().st_size/1024:.0f} KB), extracted {n_img}')
print(f'tokens    : {len(tokens)} renamed')
leaked = [s for s in re.findall(r'(?m)^([^@\s/][^{}]*)\{', css) if '.a4e' not in s and ':root' not in s]
print(f'unscoped  : {leaked if leaked else "none"}')
