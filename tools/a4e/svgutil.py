"""Shared emitters. Numbers print as the post writes them: no trailing .0."""


def num(v):
    if isinstance(v, str):
        return v
    f = float(v)
    return str(int(f)) if f == int(f) else str(f)


def tag(name, /, _text=None, _selfclose=None, **attrs):
    parts = [name]
    for k, v in attrs.items():
        if v is None:
            continue
        parts.append(f'{k.replace("_", "-")}="{num(v)}"')
    open_ = ' '.join(parts)
    if _text is None and _selfclose is not False:
        return f'<{open_}/>'
    return f'<{open_}>{"" if _text is None else _text}</{name}>'


def esc(s: str) -> str:
    """Escape for SVG text content, leaving existing entities alone."""
    if s is None:
        return ''
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '&':
            j = s.find(';', i)
            if 0 < j <= i + 10 and s[i + 1:j].replace('#', '').isalnum():
                out.append(s[i:j + 1])
                i = j + 1
                continue
            out.append('&amp;')
        elif c == '<':
            out.append('&lt;')
        elif c == '>':
            out.append('&gt;')
        else:
            out.append(c)
        i += 1
    return ''.join(out)


def family_paint(family, emph=False, opacity=None):
    """fill/stroke pair for a system-family box, matching the post's palette use."""
    var = f'var(--a4e-fam-{family})'
    if opacity is None:
        opacity = '0.22' if emph else ('0.12' if family == 'util' else '0.14')
    out = {'fill': var, 'fill_opacity': opacity, 'stroke': var}
    if emph:
        out['stroke_width'] = '1.8'
    return out
