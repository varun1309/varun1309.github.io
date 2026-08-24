"""
Replace marked regions of the post in place.

Each generated block is fenced by a pair of comments:

    <!-- a4e:gen vkb-svg -->  ... generated ...  <!-- /a4e:gen vkb-svg -->

Everything outside the fences is left byte for byte alone, which is what makes
this safe to run against a 1000-line post whose prose is hand-written.
"""
from __future__ import annotations

import re

OPEN = '<!-- a4e:gen {name} -->'
CLOSE = '<!-- /a4e:gen {name} -->'


class MarkerError(RuntimeError):
    pass


def regions(text: str) -> dict:
    """name -> (start_of_inner, end_of_inner, indent)."""
    out = {}
    for m in re.finditer(r'([ \t]*)<!-- a4e:gen ([\w-]+) -->', text):
        indent, name = m.group(1), m.group(2)
        close = text.find(CLOSE.format(name=name), m.end())
        if close < 0:
            raise MarkerError(f'{name}: opening marker has no closing marker')
        # The span runs to the closing marker itself, not to the start of its
        # line, so whatever indentation currently sits in front of it is inside
        # the replaced region and gets rewritten canonically every run. That
        # keeps the operation idempotent instead of drifting an indent per build.
        out[name] = (m.end(), close, indent)
    return out


def apply(text: str, blocks: dict) -> tuple:
    """Substitute each named block. -> (new_text, [names_changed])"""
    found = regions(text)
    missing = set(blocks) - set(found)
    if missing:
        raise MarkerError(f'no markers in the post for: {sorted(missing)}')
    changed = []
    # right to left so earlier offsets stay valid
    for name in sorted(blocks, key=lambda n: found[n][0], reverse=True):
        start, end, indent = found[name]
        body = blocks[name].strip('\n')
        new = '\n' + '\n'.join(indent + ln if ln.strip() else ln
                               for ln in body.split('\n')) + '\n' + indent
        if text[start:end] != new:
            changed.append(name)
        text = text[:start] + new + text[end:]
    return text, sorted(changed)
