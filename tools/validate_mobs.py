#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Check the dated animal reference and optional core-species membership."""
import argparse
from pathlib import Path
import re
from urllib.parse import urlsplit

import build_mobs
from validate_site_links import References
from validate_wiki import Page

ROOT = build_mobs.ROOT
SPECIES_SOURCE = 'crates/voxelgame-core/src/entities/mod.rs'


def validate(animals, habitats, biomes, game=None):
    rows = animals['animals']
    assert len(rows) == len({a['id'] for a in rows}) == len({a['slug'] for a in rows}) == animals['catalogCount']
    assert {a['category'] for a in rows} == {label for _, label in build_mobs.FAMILIES}
    assert animals['biomes'] == {b['id']: b['name'] for b in biomes['biomes']}
    value = build_mobs.render(animals, habitats, biomes)
    page = Page(value)
    assert page.breadcrumb and page.contents
    assert all(href[1:] in page.ids for href in page.anchors)
    for a in rows:
        assert re.fullmatch(r'[A-Z][A-Za-z0-9]*', a['id']), 'Only core species identifiers are supported'
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', a['slug'])
        assert build_mobs.mob_anchor(a) in page.ids
        assert a['habitats'] and len(a['habitats']) == len(set(a['habitats']))
        assert len(build_mobs.habitat_names(a, habitats, biomes)) == len(a['habitats'])
        for v in a.get('views', []):
            assert v['image'].startswith('images/animals/'), 'Only preserved animal images are supported'
    refs = References()
    refs.feed(value)
    for ref in refs.refs:
        url = urlsplit(ref)
        assert not url.scheme and not url.netloc and not url.path.startswith('/'), 'Reference must work offline'
        if url.path:
            target = (ROOT / url.path).resolve()
            assert target.is_relative_to(ROOT) and target.is_file(), f'Link missing: {ref}'
        if url.fragment.startswith('biome='):
            assert url.fragment[6:] in habitats and url.fragment[6:] in animals['biomes']
    if game:
        # This checks membership only; older images/habitats keep their original audit.
        body = (game / SPECIES_SOURCE).read_text().split('pub enum Species {', 1)[1].split('\n}', 1)[0]
        species = set(re.findall(r'^    ([A-Za-z0-9]+),$', body, re.M))
        assert species and {a['id'] for a in rows} <= species, 'Reference includes a non-core creature'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, help='Check species membership against a read-only snapshot')
    args = parser.parse_args()
    catalogs = build_mobs.read_catalogs()
    validate(*catalogs, args.game)
    assert (ROOT / 'mobs.html').read_text() == build_mobs.render(*catalogs), 'Stale mobs.html'
    print(f'PASS: {catalogs[0]["catalogCount"]} dated atlas animals, anchors, thumbnails and offline habitat links'
          + ('; core species membership checked' if args.game else ''))


if __name__ == '__main__':
    main()
