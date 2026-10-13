# SPDX-License-Identifier: GPL-3.0-only
"""Keep conditional ambient species from disappearing during gallery refreshes."""
import unittest

from build_animals import animal_category, source_habitats


BIOMES = {'WetlandFen', 'FloodedGrassland', 'InlandDelta', 'RiverDelta'}
CONDITIONAL = '''
    if matches!(
        biome,
        Biome::WetlandFen | Biome::FloodedGrassland | Biome::InlandDelta | Biome::RiverDelta
    ) && (hash >> 40) % 8 == 0
    {
        return Some(Species::Swan);
    }
'''


def source(prelude=''):
    return '''fn ambient_species_for_biome(biome: Biome, hash: u64) -> Option<Species> {
''' + prelude + '''
    let guild: &[Species] = match biome {
        Biome::WetlandFen | Biome::FloodedGrassland => &[Species::Duck, Species::Goose],
        Biome::InlandDelta | Biome::RiverDelta => { &[Species::Duck, Species::Duck] }
    };
    (!guild.is_empty()).then(|| guild[hash as usize % guild.len()])
}'''


class AnimalSource(unittest.TestCase):
    def test_legacy_static_guilds_keep_their_candidates(self):
        habitats, covered = source_habitats(source(), ['Duck', 'Goose'], BIOMES)
        self.assertEqual(covered, BIOMES)
        self.assertEqual(habitats, {'Duck': BIOMES, 'Goose': {'WetlandFen', 'FloodedGrassland'}})

    def test_conditional_swan_keeps_all_four_candidate_habitats(self):
        habitats, _ = source_habitats(source(CONDITIONAL), ['Duck', 'Goose', 'Swan'], BIOMES)
        self.assertEqual(habitats['Swan'], BIOMES)
        self.assertEqual(animal_category('Swan'), 'Birds')
        self.assertEqual(habitats['Goose'], {'WetlandFen', 'FloodedGrassland'})

    def test_unreviewed_condition_is_not_silently_ignored(self):
        with self.assertRaisesRegex(ValueError, 'pre-guild'):
            source_habitats(source(CONDITIONAL.replace('% 8 == 0', '% 8 == 9')),
                            ['Duck', 'Goose', 'Swan'], BIOMES)

    def test_conditional_species_must_belong_to_the_catalog(self):
        with self.assertRaisesRegex(ValueError, 'Unknown species'):
            source_habitats(source(CONDITIONAL), ['Duck', 'Goose'], BIOMES)

    def test_source_biomes_must_match_the_atlas(self):
        with self.assertRaisesRegex(ValueError, 'Unknown biome'):
            source_habitats(source(), ['Duck', 'Goose'], BIOMES - {'WetlandFen'})


if __name__ == '__main__':
    unittest.main()
