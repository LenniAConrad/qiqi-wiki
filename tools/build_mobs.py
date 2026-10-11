#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Render a compact animal reference from the preserved atlas catalogs."""
from html import escape
import json
from pathlib import Path

from reference_layout import article_open, article_close

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = (('mammals', 'Mammals'), ('birds', 'Birds'),
            ('reptiles-amphibians', 'Reptiles & amphibians'),
            ('fish', 'Fish'), ('invertebrates', 'Invertebrates'))


def read_catalogs():
    return tuple(json.loads((ROOT / f'data/{name}.json').read_text())
                 for name in ('animals', 'habitats', 'biomes'))


def mob_anchor(animal):
    return 'mob-' + animal['slug']


def habitat_names(animal, habitats, biomes):
    """Use named atlas habitats; fail instead of substituting unknown names."""
    names = {b['id']: b['name'] for b in biomes['biomes']}
    if not set(animal['habitats']) <= set(habitats):
        raise ValueError(f'{animal["id"]}: habitat catalog entry missing')
    return sorted(((key, names[key]) for key in animal['habitats']), key=lambda pair: pair[1])


def model_view(animal):
    views = animal.get('views', [])
    return next((v for v in views if v['pose'] == 'idle' and v['angle'] == 'three-quarter'),
                views[0] if views else None)


def render(animals, habitats, biomes):
    out = [article_open('Mobs', 'mobs.html',
                       'Animals are passive and never attack you. Find their habitats below, or browse their models in the animal atlas.',
                       FAMILIES, 'build_mobs.py'),
           '<p><a href="animals.html">Open the full animal gallery</a> for all model views. '
           'An animal’s habitat list shows where it can appear; terrain, water and nearby animals also affect spawning.</p>']
    for key, label in FAMILIES:
        members = sorted((a for a in animals['animals'] if a['category'] == label), key=lambda a: a['name'])
        out.append(f'<section class="guide-section" id="{key}"><h2>{escape(label)}</h2>'
                   '<div class="table-wrap"><table class="key-table mob-table">'
                   f'<caption>{len(members)} animals</caption><thead><tr><th scope="col">Animal</th>'
                   '<th scope="col">Where it lives</th><th scope="col">Model</th></tr></thead><tbody>')
        for animal in members:
            links = ', '.join(f'<a href="atlas.html#biome={escape(bid)}">{escape(name)}</a>'
                              for bid, name in habitat_names(animal, habitats, biomes))
            view = model_view(animal)
            model = (f'<a href="{escape(view["image"])}"><img class="mob-model" '
                     f'src="{escape(view["image"])}" width="72" height="72" loading="lazy" decoding="async" '
                     f'alt="{escape(animal["name"])} — {escape(view["label"])}"></a>' if view else '')
            anchor = mob_anchor(animal)
            out.append(f'<tr id="{anchor}"><th scope="row"><a href="#{anchor}">'
                       f'{escape(animal["name"])}</a><p class="mob-description">{escape(animal["description"])}</p></th>'
                       f'<td data-label="Where it lives">{links}</td><td data-label="Model">{model}</td></tr>')
        out.append('</tbody></table></div></section>')
    out.append(f'<p class="reference-receipt">Animal atlas: {animals["catalogCount"]} species, '
               f'<time datetime="{animals["date"]}">{animals["date"]}</time>. '
               '<a href="data/animals.json">Model and habitat provenance</a>. '
               'These are static model previews, individually framed rather than shown at a shared scale.</p>')
    return ''.join(out) + article_close()


def main():
    catalogs = read_catalogs()
    (ROOT / 'mobs.html').write_text(render(*catalogs))
    print(f'Built {catalogs[0]["catalogCount"]} atlas animals in the Mobs reference')


if __name__ == '__main__':
    main()
