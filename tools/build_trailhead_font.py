#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Convert the game's original Trailhead pixel face into fonts/trailhead.woff2.

Rows, widths and advances are parsed from the committed Rust tables of the
sibling Voxelgame checkout with `git show`; the checkout is never modified.
The font follows the game's character-to-cell mapping for printable ASCII and
U+00A0..U+00FF, including its aliases (no-break space, soft hyphen) and its
computed accented letters. The bounded Chinese name cells and the GNU Unifont
furniture subset are excluded. Characters the game would draw as its fallback
box stay out of the cmap so browsers use the next font; the box is .notdef.

One design pixel is 100 units and the em is 1100 units: the nine-row cell
plus one blank row above and below. At font-size N * 11px every design pixel
is N CSS pixels (22px draws 2px pixels). Without arguments the font is
written; --check rebuilds it in memory from the recorded source commit.
"""
import argparse
import hashlib
import io
import re
import subprocess
from collections import namedtuple
from pathlib import Path

from fontTools import agl
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'fonts/trailhead.woff2'
GAME = Path('/home/lennart/Code/Voxelgame')
FONT = 'crates/voxelgame-render/src/font'
SOURCES = {'font': f'{FONT}.rs', 'latin1': f'{FONT}/latin1.rs', 'names': f'{FONT}/names.rs',
           'cjk': f'{FONT}/cjk.rs', 'upload': 'crates/voxelgame-render/src/gpu_textures.rs'}
HISTORY = (f'{FONT}.rs', FONT)          # the font source commit is their last change
PIXEL = 100                             # font units per design pixel
CAP_ROWS = 7                            # rows above the baseline; two descender rows follow
ASCENT, DESCENT = 8 * PIXEL, 3 * PIXEL  # one blank row above and below the nine-row cell
EM = ASCENT + DESCENT
MAC_EPOCH = 2082844800                  # 1904-01-01 to 1970-01-01, for head timestamps
TRAILHEAD = 'pub(crate) fn trailhead_glyph(character: char) -> Glyph {'
VERSION = re.compile(r'Version 1\.000; voxelgame (\w+); font source (\w+)')
# accent() and resolve() port these functions. Comment and whitespace edits are
# ignored; any other change fails until the port has been reviewed again.
PORTED = {
    ('font', 'const fn glyph('): 'c9a0f9ad819c232a',
    ('font', 'pub(crate) fn raster_glyph('): 'a6a516377eca6ec8',
    ('latin1', 'fn accented('): 'b806e17f4b49dca3',
}

Glyph = namedtuple('Glyph', 'rows width advance')
CHAR = r"'(?:\\u\{[0-9A-Fa-f]{1,6}\}|\\['\"\\nrt0]|[^'\\\n])'"
INT = r'(?:0b[01_]+|0x[0-9A-Fa-f_]+|[0-9][0-9_]*)'
ROWS = (rf'\[(?:(?P<rows>\s*{INT}(?:\s*,\s*{INT})*\s*,?\s*)'  # [a, b, ...] or [fill; count]
        rf'|\s*(?P<fill>{INT})\s*;\s*(?P<count>{INT})\s*)\]')
CHAR_RE = re.compile(CHAR)


class SourceError(SystemExit):
    """The Rust tables no longer have the shape this converter understands."""

    def __init__(self, message):
        super().__init__(f'Trailhead source: {message}')


def rust_char(literal):
    body = literal[1:-1]
    if body.startswith('\\u{'):
        return chr(int(body[3:-1], 16))
    if body.startswith('\\'):
        return {'n': '\n', 'r': '\r', 't': '\t', '0': '\0'}.get(body[1], body[1])
    return body


def rust_int(literal):
    digits = literal.strip().replace('_', '')
    base = {'0b': 2, '0x': 16}.get(digits[:2], 10)
    return int(digits[2:] if base != 10 else digits, base)


def skip_literal(text, i):
    """End of the comment, string or char literal starting at i, else None."""
    if text.startswith('//', i):
        end = text.find('\n', i)
        return len(text) if end < 0 else end
    if text.startswith('/*', i):
        return text.index('*/', i) + 2
    if text[i] == '"':
        j = i + 1
        while text[j] != '"':
            j += 2 if text[j] == '\\' else 1
        return j + 1
    match = CHAR_RE.match(text, i) if text[i] == "'" else None
    return match.end() if match else None


def without_comments(text):
    out, i = [], 0
    while i < len(text):
        end = skip_literal(text, i)
        if end is None:
            out.append(text[i])
            end = i + 1
        else:
            out.append(' ' if text.startswith(('//', '/*'), i) else text[i:end])
        i = end
    return ''.join(out)


def block(text, opener):
    """Text from `opener` (ending in '{', occurring once) to its closing brace."""
    if not opener.endswith('{') or text.count(opener) != 1:
        raise SourceError(f'expected exactly one {opener!r}')
    start = text.index(opener)
    depth, i = 1, start + len(opener)
    while depth:
        if i >= len(text):
            raise SourceError(f'unbalanced braces after {opener!r}')
        end = skip_literal(text, i)
        if end is None:
            depth += {'{': 1, '}': -1}.get(text[i], 0)
            end = i + 1
        i = end
    return text[start:i]


def body(text, opener):
    return block(text, opener)[len(opener):-1]


def flat(text):
    return ' '.join(text.split())


def fingerprint(text):
    return hashlib.sha256(flat(text).encode()).hexdigest()[:16]


def arms(text, patterns, last):
    """Parse every arm of a match body; anything unexpected fails loudly."""
    found, i = [], 0
    while True:
        while i < len(text) and text[i].isspace():
            i += 1
        if i == len(text):
            break
        for kind, pattern in patterns.items():
            match = pattern.match(text, i)
            if match:
                found.append((kind, match))
                i = match.end()
                break
        else:
            raise SourceError(f'unexpected match arm near {text[i:i + 60]!r}')
    kinds = [kind for kind, _ in found]
    if kinds.count(last) != 1 or kinds[-1] != last:
        raise SourceError(f'match must end with exactly one {last} arm')
    keys = [match['key'] for _, match in found if 'key' in match.groupdict()]
    if len(set(keys)) != len(keys):
        raise SourceError('a match repeats a character')
    return found[:-1], found[-1][1]


def bitmap_arm(function, key=CHAR):
    return re.compile(rf'(?P<key>{key})\s*=>\s*{function}\(\s*{ROWS}\s*,\s*(?P<width>{INT})'
                      rf'\s*,\s*(?P<advance>{INT})\s*,?\s*\)\s*,?')


ALIAS = re.compile(rf'(?P<key>{CHAR})\s*=>\s*trailhead_glyph\(\s*(?P<target>{CHAR})\s*\)\s*,?')
COMPOSE = re.compile(rf'(?P<key>{CHAR})\s*=>\s*Some\(\(\s*(?P<base>{CHAR})\s*,\s*(?P<accent>\w+)\s*\)\)\s*,?')
NAME = re.compile(rf'(?P<key>{CHAR})\s*=>\s*{ROWS}\s*,?')
NONE = re.compile(r'_\s*=>\s*(?:return\s+)?None\s*,?')
RANGE = re.compile(rf'code\s*@\s*(?P<lo>{INT})\s*\.\.=\s*(?P<hi>{INT})\s*=>\s*[^,]+,')
SINGLE = re.compile(rf'(?P<code>{INT})\s*=>\s*{INT}\s*,')
OTHER = re.compile(r'_\s*=>\s*cjk::index\(character\)\.map_or\(\s*FALLBACK_CELL\s*,\s*\|index\|'
                   r'\s*CJK_FIRST_CELL\s*\+\s*index as u32\s*\)\s*,?')


def glyph_from(match):
    if match['fill'] is not None:
        rows = (rust_int(match['fill']),) * rust_int(match['count'])
    else:
        rows = tuple(rust_int(value) for value in match['rows'].split(',') if value.strip())
    glyph = Glyph(rows, rust_int(match['width']), rust_int(match['advance']))
    if len(rows) != 9 or glyph.width > 9 or glyph.advance < glyph.width:
        raise SourceError(f'bad metrics in {match[0][:60]!r}')
    return glyph


def keyed(found, kind, value):
    return {rust_char(match['key']): value(match) for arm, match in found if arm == kind}


def read_sources(game, commit):
    return {name: without_comments(git(game, 'show', f'{commit}:{path}', strip=False))
            for name, path in SOURCES.items()}


def check_structure(src):
    for (name, opener), expected in PORTED.items():
        signature = src[name][src[name].index(opener):].split('{', 1)[0] + '{'
        actual = fingerprint(block(src[name], signature))
        if actual != expected:
            raise SourceError(f'{SOURCES[name]} {opener}...) changed ({actual}); review the port')
    order = ('if let Some(glyph) = names::glyph(character) { return glyph; } '
             'if let Some(glyph) = latin1::glyph(character) { return glyph; } match character {')
    lookup = body(src['font'], TRAILHEAD)
    if flat(lookup) != flat(f'{order} {body(lookup, "match character {")} }}'):
        raise SourceError('trailhead_glyph() lookup order changed')
    if 'if let Some((base, accent)) = composition { return Some(accented(base, accent)); }' not in flat(src['latin1']):
        raise SourceError('latin1::glyph() no longer applies its composition table first')
    if 'if bits & (1 << (u32::from(glyph.width) - 1 - column)) != 0 {' not in flat(src['upload']):
        raise SourceError('atlas upload no longer draws the high bit in the left column')


def coverage(src, names):
    """Latin code points with generic atlas cells; explicit name cells are excluded."""
    found, _ = arms(body(src['font'], 'match character as u32 {'),
                    {'range': RANGE, 'single': SINGLE, 'other': OTHER}, 'other')
    singles = {rust_int(m['code']) for kind, m in found if kind == 'single'}
    if singles != {ord(key) for key in names}:
        raise SourceError('explicit atlas cells no longer match names.rs')
    lo, hi = (rust_char(value) for value in re.search(
        rf"if !\(({CHAR})\.\.=({CHAR})\)\.contains\(&character\)",
        flat(body(src['cjk'], 'pub(super) fn index(character: char) -> Option<usize> {'))).groups())
    ranges = [(rust_int(m['lo']), rust_int(m['hi'])) for kind, m in found if kind == 'range']
    codes = [code for start, end in ranges for code in range(start, end + 1)]
    if not codes or max(codes) >= ord(lo) or len(set(codes)) != len(codes):
        raise SourceError('generic atlas ranges overlap each other or the Chinese subset')
    if {ord(key) for key in names} & set(codes) or 'GLYPHS[index(character)?]' not in src['cjk']:
        raise SourceError('Chinese glyphs could shadow a Latin cell')
    return codes


def accent_rules(latin1):
    text = flat(block(latin1, 'fn accented(base: char, accent: Accent) -> Glyph {'))
    marks = {name: (rust_int(a), rust_int(b)) for name, a, b in
             re.findall(rf'Accent::(\w+) => \[({INT}), ({INT})\]', text)}
    cedilla = {int(row): rust_int(value) for row, value in re.findall(
        rf'glyph\.rows\[(\d)\] = ({INT});', body(text, 'Accent::Cedilla => {'))}
    slash = re.search(r'glyph\.rows\[\.\.7\]\.iter_mut\(\)\.zip\(\[([^\]]*)\]\)', text)[1]
    ring = re.search(rf'if matches!\(accent, Accent::Ring\) {{.*glyph\.rows\[2\] = ({INT});', text)[1]
    return marks, cedilla, [rust_int(value) for value in slash.split(',')], rust_int(ring)


def accent(glyph, base, mark, rules):
    """Port of latin1.rs accented(): same rows, width and advance as the game."""
    marks, cedilla, slash, ring = rules
    rows = list(glyph.rows)
    if mark == 'Cedilla':
        for row, value in cedilla.items():
            rows[row] = value
    elif mark == 'Slash':
        for row, value in enumerate(slash):
            rows[row] |= value
    else:
        if 'A' <= base <= 'Z':
            rows[2:9] = rows[0:7]
        top = marks[mark]
        rows[0], rows[1] = (value >> 1 if glyph.width == 3 else value for value in top)
        if mark == 'Ring':
            if 'a' <= base <= 'z':
                rows[3:8] = rows[2:7]
            rows[2] = ring
    return glyph._replace(rows=tuple(rows))


def load(game, commit):
    """Return the fallback box and {code point: (alias target, Glyph)} for the font."""
    src = read_sources(game, commit)
    check_structure(src)
    found, fallback = arms(body(body(src['font'], TRAILHEAD), 'match character {'),
                           {'glyph': bitmap_arm('glyph'), 'fallback': bitmap_arm('glyph', '_')}, 'fallback')
    ascii_glyphs, fallback = keyed(found, 'glyph', glyph_from), glyph_from(fallback)
    latin_body = body(src['latin1'], 'pub(super) fn glyph(character: char) -> Option<Glyph> {')
    found, _ = arms(body(latin_body, 'let composition = match character {'), {'compose': COMPOSE, 'none': NONE}, 'none')
    compose = keyed(found, 'compose', lambda m: (rust_char(m['base']), m['accent']))
    found, _ = arms(body(latin_body, 'Some(match character {'),
                    {'bitmap': bitmap_arm('bitmap'), 'alias': ALIAS, 'none': NONE}, 'none')
    latin, alias = keyed(found, 'bitmap', glyph_from), keyed(found, 'alias', lambda m: rust_char(m['target']))
    found, _ = arms(body(src['names'], 'let rows = match character {'), {'name': NAME, 'none': NONE}, 'none')
    names = keyed(found, 'name', lambda m: None)
    rules = accent_rules(src['latin1'])

    def resolve(character):
        """Port of trailhead_glyph(); None where the game shows its fallback box."""
        if character in compose:
            base, mark = compose[character]
            return accent(resolve(base), base, mark, rules)
        if character in alias:
            return resolve(alias[character])
        return latin.get(character) or ascii_glyphs.get(character)

    table = {}
    for code in coverage(src, names):
        glyph = resolve(chr(code))
        if glyph is None:
            continue
        if any(row >> glyph.width for row in glyph.rows):
            raise SourceError(f'U+{code:04X} has ink outside its width')
        target = chr(code)
        while target in alias:
            target = alias[target]
        table[code] = (ord(target), glyph)
    return fallback, table


def rectangles(glyph):
    """Horizontal pixel runs, merged downwards while a run repeats exactly."""
    active, done = {}, []
    for row, bits in enumerate((*glyph.rows, 0)):
        runs, start = [], None
        for column in range(glyph.width + 1):
            lit = column < glyph.width and bits >> (glyph.width - 1 - column) & 1
            if lit and start is None:
                start = column
            elif not lit and start is not None:
                runs.append((start, column))
                start = None
        for run in [run for run in active if run not in runs]:
            done.append((*run, active.pop(run), row))
        for run in runs:
            active.setdefault(run, row)
    return sorted(done, key=lambda rect: (rect[2], rect[0]))


def outline(glyph):
    """Non-overlapping clockwise squares; design row 0 is the cap line."""
    pen = TTGlyphPen(None)
    for left, right, top, bottom in rectangles(glyph):
        x0, x1 = left * PIXEL, right * PIXEL
        y0, y1 = (CAP_ROWS - bottom) * PIXEL, (CAP_ROWS - top) * PIXEL
        pen.moveTo((x0, y0))
        pen.lineTo((x0, y1))
        pen.lineTo((x1, y1))
        pen.lineTo((x1, y0))
        pen.closePath()
    return pen.glyph()


def build(game, head, commit):
    fallback, table = load(game, commit)
    timestamp = int(git(game, 'log', '-1', '--format=%ct', commit)) + MAC_EPOCH
    glyphs, cmap = {'.notdef': fallback}, {}
    for code, (target, glyph) in table.items():
        name = agl.UV2AGL.get(target, f'uni{target:04X}')
        if glyphs.setdefault(name, glyph) != glyph:
            raise SourceError(f'glyph name {name} is not unique')
        cmap[code] = name
    fb = FontBuilder(EM, isTTF=True)
    fb.updateHead(created=timestamp, modified=timestamp)
    fb.setupGlyphOrder(list(glyphs))
    fb.setupCharacterMap(cmap)
    fb.setupGlyf({name: outline(glyph) for name, glyph in glyphs.items()})
    glyf = fb.font['glyf']
    fb.setupHorizontalMetrics({name: (glyph.advance * PIXEL, getattr(glyf[name], 'xMin', 0))
                               for name, glyph in glyphs.items()})
    fb.setupHorizontalHeader(ascent=ASCENT, descent=-DESCENT, lineGap=0)
    source = f'voxelgame source {commit} (checkout {head})'
    fb.setupNameTable({
        'copyright': f'Original Voxelgame Trailhead typeface, GPL-3.0-only, converted for the qiqi wiki from {source}.',
        'familyName': 'Trailhead', 'styleName': 'Regular', 'fullName': 'Trailhead Regular',
        'uniqueFontIdentifier': f'Trailhead Regular; voxelgame {commit}', 'psName': 'Trailhead-Regular',
        'version': f'Version 1.000; voxelgame {head}; font source {commit}',
        'description': 'Nine-row bitmap face; one design pixel is 100 of 1100 units per em. '
                       'Use font-size multiples of 11px. Converted by tools/build_trailhead_font.py.',
        'licenseDescription': 'GPL-3.0-only: you can redistribute and/or modify this font under the '
                              'terms of the GNU General Public License version 3.',
        'licenseInfoURL': 'https://www.gnu.org/licenses/gpl-3.0.html',
    }, mac=False)
    fb.setupOS2(version=4, fsType=0, fsSelection=0x00C0, achVendID='NONE',
                sTypoAscender=ASCENT, sTypoDescender=-DESCENT, sTypoLineGap=0,
                usWinAscent=ASCENT, usWinDescent=DESCENT, sxHeight=5 * PIXEL, sCapHeight=CAP_ROWS * PIXEL,
                yStrikeoutSize=PIXEL, yStrikeoutPosition=3 * PIXEL, usDefaultChar=0, usBreakChar=32)
    fb.font['OS/2'].recalcCodePageRanges(fb.font)
    fb.setupPost(underlinePosition=-PIXEL, underlineThickness=PIXEL)
    fb.font.flavor = 'woff2'
    data = io.BytesIO()
    fb.save(data)
    return data.getvalue(), len(glyphs), len(cmap)


def git(game, *args, strip=True):
    try:
        out = subprocess.run(['git', '-C', str(game), *args], check=True, capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(f'git {" ".join(args)} failed in {game}: {getattr(error, "stderr", error)}')
    return out.strip() if strip else out


def current_revision(game):
    head = git(game, 'rev-parse', '--short', 'HEAD')
    commit = git(game, 'log', '-1', '--format=%h', '--', *HISTORY)
    if git(game, 'diff', '--name-only', commit, 'HEAD', '--', *HISTORY):
        raise SystemExit(f'Trailhead sources at HEAD differ from {commit}')
    if git(game, 'status', '--porcelain', '--', *HISTORY):
        print('note: uncommitted Trailhead edits in the game checkout are ignored')
    return head, commit


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, default=GAME, help='Voxelgame checkout (read with git show only)')
    parser.add_argument('--check', action='store_true',
                        help='Rebuild from the source commit recorded in the font and compare bytes')
    args = parser.parse_args()
    if args.check:
        recorded = VERSION.fullmatch(TTFont(OUTPUT)['name'].getDebugName(5) or '')
        if not recorded:
            raise SystemExit(f'{OUTPUT.relative_to(ROOT)} has no recorded source commit')
        data, _, _ = build(args.game, *recorded.groups())
        if data != OUTPUT.read_bytes():
            raise SystemExit(f'Stale {OUTPUT.relative_to(ROOT)}: run tools/build_trailhead_font.py')
        latest = current_revision(args.game)[1]
        if latest != recorded[2]:
            print(f'note: Trailhead sources changed since {recorded[2]} (now {latest}); rerun to refresh')
        print(f'{OUTPUT.relative_to(ROOT)} matches voxelgame font source {recorded[2]}')
        return
    head, commit = current_revision(args.game)
    data, glyphs, codes = build(args.game, head, commit)
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_bytes(data)
    print(f'Wrote {OUTPUT.relative_to(ROOT)}: {len(data)} bytes, {glyphs} glyphs, {codes} code points, '
          f'voxelgame {head}, font source {commit}')


if __name__ == '__main__':
    main()
