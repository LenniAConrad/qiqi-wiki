<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Trailhead webfont

`trailhead.woff2` is the game's own Trailhead pixel face, which the game source
describes as an original typeface drawn for Voxelgame. It was converted from the
Rust glyph tables in `crates/voxelgame-render/src/font.rs` and `font/latin1.rs`
at Voxelgame font source commit `64926d80` (checkout `251b9e46`). Like the game
and this wiki it is GPL-3.0-only; see `../LICENSE`.

Coverage follows the game's own character mapping: printable ASCII and
U+00A0–U+00FF, 191 code points in 190 glyphs. The game's fallback box is
`.notdef`. Accented letters are the game's composed bitmaps, so accented
capitals sit two pixels lower, as they do in the game. No glyphs were drawn for
the wiki. The game has none for curly quotes, en or em dashes, the ellipsis or
arrows, so browsers use the next font in the stack. The Chinese name glyphs and
the GNU Unifont furniture subset are excluded.

Regenerate or check it with fontTools and brotli installed. The tool reads
committed game files with `git show` and never modifies the checkout; pass
`--game PATH` if the checkout is not at `/home/lennart/Code/Voxelgame`:

```sh
python3 tools/build_trailhead_font.py
python3 tools/build_trailhead_font.py --check
```

`--check` rebuilds the font from the commit recorded in its name table and
compares the bytes.

## Metrics for CSS

One design pixel is 100 units and the em is 1100 units: ascender 800,
descender 300, no line gap, cap height 700 and x-height 500. The nine-row cell
has one blank row above and below it. Use font-size multiples of 11px: 11px
draws 1 CSS pixel per design pixel, 22px draws 2 and 33px draws 3. With
`line-height` equal to the font size, the baseline falls on a whole pixel, for
example 16px down a 22px line. Taller lines stay sharp when they add an even
number of CSS pixels. There is no bold; use weight 400 with
`font-synthesis: none`.
