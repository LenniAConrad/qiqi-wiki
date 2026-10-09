// SPDX-License-Identifier: GPL-3.0-only
//! Refine selected photo sites without changing survey frequency measurements.
use std::{env, fs};
use voxelgame_core::world::{Biome, Block, World};
fn main() {
    let args: Vec<_> = env::args().collect();
    let input = fs::read_to_string(&args[1]).unwrap();
    let mut rows = Vec::new();
    for line in input.lines() {
        let p: Vec<_> = line.split(',').collect();
        let id = p[0];
        let seed: u64 = p[1].parse().unwrap();
        let ox: i64 = p[2].parse().unwrap();
        let oz: i64 = p[3].parse().unwrap();
        let biome = Biome::ALL
            .into_iter()
            .find(|b| format!("{b:?}") == id)
            .unwrap();
        let world = World::new(seed);
        let t = world.terrain_sampler();
        let mut best = None;
        for z in (oz - 1536..=oz + 1536).step_by(24) {
            for x in (ox - 1536..=ox + 1536).step_by(24) {
                let c = t.surface_column(x * 2, z * 2);
                if c.biome != biome {
                    continue;
                }
                if id == "SnowyPeaks" && !matches!(c.material, Block::SNOW | Block::PACKED_SNOW) {
                    continue;
                }
                if id == "TepuiPlateau"
                    && !matches!(c.material, Block::WET_STONE | Block::RICH_TURF)
                {
                    continue;
                }
                if id == "SeaStacks"
                    && !matches!(c.material, Block::LAYERED_SANDSTONE | Block::GUANO_ROCK)
                {
                    continue;
                }
                let h = (c.height + 1) as f64 / 2.;
                let water = c.water.map_or(h, |w| (w.level + 1) as f64 / 2.);
                for (dx, dz) in [
                    (0, -48),
                    (-48, 0),
                    (48, 0),
                    (0, 48),
                    (-36, -36),
                    (36, 36),
                    (36, -36),
                    (-36, 36),
                ] {
                    let n = t.surface_column((x + dx) * 2, (z + dz) * 2);
                    let nh = (n.height + 1) as f64 / 2.;
                    let nw = n.water.map_or(nh, |w| (w.level + 1) as f64 / 2.);
                    let (score, camera, target_y) = if id == "DeepKelpForest" {
                        if !(6.0..14.0).contains(&(water - h)) || n.biome != biome {
                            continue;
                        }
                        let cx = x + dx / 4;
                        let cz = z + dz / 4;
                        let cam = t.surface_column(cx * 2, cz * 2);
                        let cy = ((cam.height + 1) as f64 / 2. + 3.0).max(h + 3.0);
                        (
                            100.0 - (water - h - 9.0).abs(),
                            [cx as f64, cy, cz as f64],
                            h + 1.,
                        )
                    } else if id == "SnowyPeaks" || id == "SeaStacks" || id == "TepuiPlateau" {
                        (
                            h - (h - nh).abs() * 2.,
                            [(x + dx) as f64, h.max(nh) + 45., (z + dz) as f64],
                            h,
                        )
                    } else {
                        (
                            h - nh,
                            [(x + dx) as f64, (nh + 14.).max(nw + 12.), (z + dz) as f64],
                            h - 2.,
                        )
                    };
                    if best.as_ref().map_or(true, |(s, _)| score > *s) {
                        let look = [
                            ((x as f64 - camera[0]).atan2(z as f64 - camera[2])).to_degrees(),
                            (target_y - camera[1] - 1.62)
                                .atan2((x as f64 - camera[0]).hypot(z as f64 - camera[2]))
                                .to_degrees(),
                        ];
                        let row=format!("\"{id}\":{{\"id\":\"{id}\",\"seed\":\"{seed}\",\"x\":{x},\"z\":{z},\"height\":{h},\"water\":{water},\"camera\":{camera:?},\"look\":{look:?}}}");
                        best = Some((score, row));
                    }
                }
            }
        }
        let (score, row) = best.expect("No refined site");
        eprintln!("{id}: score {score}");
        rows.push(row);
    }
    fs::write(&args[2], format!("{{{}}}\n", rows.join(",\n"))).unwrap();
}
