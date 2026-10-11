# SPDX-License-Identifier: GPL-3.0-only
"""Habitat, image and search regressions for the compact Mobs article."""
import copy
import unittest

import build_mobs
import build_wiki
import validate_mobs


class MobsReference(unittest.TestCase):
    def setUp(self):
        self.animals, self.habitats, self.biomes = build_mobs.read_catalogs()

    def test_every_atlas_animal_has_an_anchor_and_search_record(self):
        validate_mobs.validate(self.animals, self.habitats, self.biomes)
        records = [r for r in build_wiki.search_records() if r['kind'] == 'Mob']
        self.assertEqual({r['href'] for r in records},
                         {'mobs.html#' + build_mobs.mob_anchor(a) for a in self.animals['animals']})
        self.assertEqual(len(records), self.animals['catalogCount'])
        for a in self.animals['animals']:
            record = next(r for r in records if r['title'] == a['name'])
            for name in (self.animals['biomes'][bid] for bid in a['habitats']):
                self.assertIn(name, record['text'])

    def test_optional_identifier_or_non_animal_image_is_rejected(self):
        for mutation in ('id', 'image'):
            animals = copy.deepcopy(self.animals)
            if mutation == 'id':
                animals['animals'][0]['id'] = 'voxelgame_wwii:pack'
            else:
                animals['animals'][0]['views'][0]['image'] = 'images/tank.webp'
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                validate_mobs.validate(animals, self.habitats, self.biomes)

    def test_habitat_names_cannot_be_guessed(self):
        a = copy.deepcopy(self.animals['animals'][0])
        a['habitats'] = ['UnknownBiome']
        with self.assertRaises(ValueError):
            build_mobs.habitat_names(a, self.habitats, self.biomes)

    def test_model_preview_is_small_lazy_and_optional(self):
        html = build_mobs.render(self.animals, self.habitats, self.biomes)
        self.assertEqual(html.count('class="mob-model"'), self.animals['catalogCount'])
        self.assertIn('width="72" height="72" loading="lazy"', html)
        animals = copy.deepcopy(self.animals)
        animals['animals'][0]['views'] = []
        html = build_mobs.render(animals, self.habitats, self.biomes)
        self.assertEqual(html.count('class="mob-model"'), self.animals['catalogCount'] - 1)


if __name__ == '__main__':
    unittest.main()
