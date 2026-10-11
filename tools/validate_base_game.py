# SPDX-License-Identifier: GPL-3.0-only
"""Reject optional content in the actual staged website (including data/scripts)."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re

# Namespace IDs from the source ledger's six compiled providers at dd29d91.
PACK_IDS = ('chinese_village:pack', 'circuits:pack', 'voxelgame_sundown:pack',
            'voxelgame_verdun:pack', 'voxelgame_wwii:pack', 'zijing_nerds:pack')
PAYLOAD = re.compile(r'optional-pack|\b(?:' + '|'.join(map(re.escape, PACK_IDS)) + r')\b', re.I)


class Navigation(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_nav = 0
        self.bad = False

    def handle_starttag(self, tag, attrs):
        if tag == 'nav':
            self.in_nav += 1
        if tag == 'a' and self.in_nav:
            href = dict(attrs).get('href', '')
            self.bad |= bool(re.search(r'(?:^|[/#])mods?(?:[./#-]|$)|villages\.html', href, re.I))

    def handle_endtag(self, tag):
        if tag == 'nav':
            self.in_nav = max(0, self.in_nav - 1)

    def handle_data(self, data):
        if self.in_nav and re.fullmatch(r'\s*Mods\s*', data, re.I):
            self.bad = True


def validate(root):
    errors = []
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        name = path.relative_to(root).as_posix()
        if name.startswith(('images/villages/', 'data/villages.')) or name.startswith('villages.'):
            errors.append(f'{name}: optional gallery')
        if path.suffix in ('.html', '.json', '.js', '.css', '.md', '.csv'):
            value = path.read_text(encoding='utf-8')
            if PAYLOAD.search(value):
                errors.append(f'{name}: optional content status or pack ID')
            if path.suffix == '.html':
                nav = Navigation()
                nav.feed(value)
                if nav.bad:
                    errors.append(f'{name}: optional content navigation')
    if errors:
        raise ValueError('\n'.join(errors))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    validate(parser.parse_args().root)
    print('PASS: staged website contains base-game content only')
