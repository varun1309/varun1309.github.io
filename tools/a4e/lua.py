"""
Minimal reader for the Lua table literals DCS writes into its input files.

DCS input files are `return { ... }` or `local x = { ... } return x`. They only
ever contain tables, strings, numbers, booleans and nil -- no function calls, no
arithmetic, no concatenation. That is a small enough language to parse directly,
which keeps this toolchain free of a Lua runtime (`lua` and `lupa` are both
absent on a stock macOS box).

Handles: [key] = value and bare key = value, both list and record entries in the
same table, single/double/long-bracket strings, escapes, comments, trailing
commas, semicolon separators, and numbers in decimal or hex.
"""
from __future__ import annotations


class LuaSyntaxError(ValueError):
    def __init__(self, msg: str, text: str, pos: int):
        line = text.count('\n', 0, pos) + 1
        col = pos - (text.rfind('\n', 0, pos) + 1) + 1
        near = text[max(0, pos - 30):pos + 30].replace('\n', ' ')
        super().__init__(f'{msg} at line {line} col {col}: ...{near}...')
        self.line, self.col = line, col


_WS = ' \t\r\n'
_NAME_START = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')
_NAME_BODY = _NAME_START | set('0123456789')


class _Parser:
    def __init__(self, text: str):
        self.t = text
        self.i = 0
        self.n = len(text)

    # ------------------------------------------------------------ scanning
    def err(self, msg: str):
        raise LuaSyntaxError(msg, self.t, self.i)

    def skip(self):
        """Whitespace and comments."""
        t, n = self.t, self.n
        while self.i < n:
            c = t[self.i]
            if c in _WS:
                self.i += 1
            elif t.startswith('--', self.i):
                self.i += 2
                if self.i < n and t[self.i] == '[':
                    lvl = self._long_level()
                    if lvl is not None:
                        self._long_string(lvl)
                        continue
                nl = t.find('\n', self.i)
                self.i = n if nl < 0 else nl + 1
            else:
                return

    def _long_level(self):
        """At a '[', return the level of a `[==[` opener, else None."""
        j = self.i + 1
        lvl = 0
        while j < self.n and self.t[j] == '=':
            lvl += 1
            j += 1
        return lvl if j < self.n and self.t[j] == '[' else None

    def _long_string(self, lvl: int) -> str:
        close = ']' + '=' * lvl + ']'
        start = self.i + lvl + 2
        if self.t.startswith('\n', start):      # opener eats one leading newline
            start += 1
        end = self.t.find(close, start)
        if end < 0:
            self.err('unterminated long string')
        self.i = end + len(close)
        return self.t[start:end]

    def literal(self, s: str) -> bool:
        self.skip()
        if self.t.startswith(s, self.i):
            self.i += len(s)
            return True
        return False

    def expect(self, s: str):
        if not self.literal(s):
            self.err(f'expected {s!r}')

    def peek(self) -> str:
        self.skip()
        return self.t[self.i] if self.i < self.n else ''

    # -------------------------------------------------------------- values
    def name(self):
        self.skip()
        if self.i >= self.n or self.t[self.i] not in _NAME_START:
            return None
        j = self.i
        while j < self.n and self.t[j] in _NAME_BODY:
            j += 1
        out, self.i = self.t[self.i:j], j
        return out

    _ESC = {'a': '\a', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r',
            't': '\t', 'v': '\v', '\\': '\\', '"': '"', "'": "'", '\n': '\n'}

    def string(self) -> str:
        q = self.t[self.i]
        if q == '[':
            lvl = self._long_level()
            if lvl is None:
                self.err('expected string')
            return self._long_string(lvl)
        self.i += 1
        out = []
        while True:
            if self.i >= self.n:
                self.err('unterminated string')
            c = self.t[self.i]
            if c == q:
                self.i += 1
                return ''.join(out)
            if c != '\\':
                out.append(c)
                self.i += 1
                continue
            self.i += 1
            e = self.t[self.i]
            if e in self._ESC:
                out.append(self._ESC[e])
                self.i += 1
            elif e == 'x':
                out.append(chr(int(self.t[self.i + 1:self.i + 3], 16)))
                self.i += 3
            elif e == 'z':                       # skip following whitespace
                self.i += 1
                while self.i < self.n and self.t[self.i] in _WS:
                    self.i += 1
            elif e.isdigit():
                j = self.i
                while j < self.n and self.t[j].isdigit() and j - self.i < 3:
                    j += 1
                out.append(chr(int(self.t[self.i:j])))
                self.i = j
            else:
                out.append(e)
                self.i += 1

    def number(self):
        j = self.i
        if self.t.startswith(('0x', '0X'), j):
            j += 2
            while j < self.n and self.t[j] in '0123456789abcdefABCDEF':
                j += 1
            out, self.i = int(self.t[self.i:j], 16), j
            return out
        while j < self.n and (self.t[j].isdigit() or self.t[j] in '+-.eE'):
            # '+'/'-' only legal straight after an exponent marker
            if self.t[j] in '+-' and self.t[j - 1] not in 'eE':
                break
            j += 1
        raw, self.i = self.t[self.i:j], j
        try:
            return int(raw)
        except ValueError:
            return float(raw)

    def value(self):
        self.skip()
        if self.i >= self.n:
            self.err('unexpected end of input')
        c = self.t[self.i]
        if c == '{':
            return self.table()
        if c in '"\'':
            return self.string()
        if c == '[' and self._long_level() is not None:
            return self.string()
        if c.isdigit() or (c in '+-.' and self.i + 1 < self.n):
            return self.number()
        kw = self.name()
        if kw == 'true':
            return True
        if kw == 'false':
            return False
        if kw == 'nil':
            return None
        self.err(f'unexpected value {kw or c!r}')

    def table(self):
        self.expect('{')
        out, idx = {}, 1
        while True:
            self.skip()
            if self.literal('}'):
                return out
            save = self.i
            key = None
            if self.peek() == '[':                       # [key] = value
                lvl = self._long_level()
                if lvl is None:
                    self.i += 1
                    key = self.value()
                    self.expect(']')
                    self.expect('=')
            else:
                nm = self.name()
                if nm is not None and self.literal('='):
                    key = nm
                else:
                    self.i = save                        # positional entry
            if key is None:
                out[idx] = self.value()
                idx += 1
            else:
                out[key] = self.value()
            self.skip()
            if not (self.literal(',') or self.literal(';')):
                self.expect('}')
                return out


def loads(text: str):
    """Parse the table a DCS input .lua returns."""
    p = _Parser(text)
    # `return {...}`  |  `local d = {...} ... return d`  |  a bare `{...}`
    p.skip()
    if p.t.startswith('return', p.i):
        p.i += 6
        return p.value()
    brace = text.find('{', p.i)
    if brace < 0:
        raise LuaSyntaxError('no table found', text, p.i)
    p.i = brace
    return p.value()


def load(path) -> dict:
    import pathlib
    raw = pathlib.Path(path).read_bytes()
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            return loads(raw.decode(enc))
        except UnicodeDecodeError:
            continue
    raise ValueError(f'cannot decode {path}')
