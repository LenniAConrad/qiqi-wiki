// SPDX-License-Identifier: GPL-3.0-only
//! Equal-area biome survey and deterministic, interior-biased photography sites.
use std::{collections::BTreeMap, env, fs};
use voxelgame_core::world::{Biome, GeneratorVersion, World};
const RADIUS_METRES: i64 = 55_296;
const STRIDE_METRES: usize = 144;
const SEEDS: [u64; 11] = [812, 7, 91, 614, 913, 4242, 9001, 12039, 14, 2, 33];
#[derive(Clone, Copy)]
struct Site {
    seed: u64,
    x: i64,
    z: i64,
    height: f64,
    water: f64,
    score: i64,
}
fn mix(mut x: u64) -> u64 {
    x = (x ^ (x >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
    x = (x ^ (x >> 27)).wrapping_mul(0x94d049bb133111eb);
    x ^ (x >> 31)
}
fn hash_name(name: &str) -> u64 {
    name.bytes().fold(0xcbf2_9ce4_8422_2325_u64, |hash, byte| {
        (hash ^ u64::from(byte)).wrapping_mul(0x0100_0000_01b3)
    })
}

/// Frame the chosen real habitat without an intervening ridge hiding it.
/// This runs only for the final 92 photo sites and cannot affect survey counts.
fn clear_camera(site: Site) -> [f64; 3] {
    let world = World::new(site.seed);
    let terrain = world.terrain_sampler();
    let target_y = (site.height + 3.0).max(site.water);
    let mut best = ([0.0; 3], f64::INFINITY);
    for (dx, dz) in [
        (-24, -32),
        (24, -32),
        (32, -24),
        (32, 24),
        (24, 32),
        (-24, 32),
        (-32, 24),
        (-32, -24),
    ] {
        let (camera_x, camera_z) = (site.x + dx, site.z + dz);
        let back = terrain.surface_column(camera_x * 2, camera_z * 2);
        let mut camera_y = (site.height + 24.0)
            .max((back.height + 1) as f64 / 2.0 + 20.0)
            .max(site.water + 15.0);
        for step in 1..8 {
            let t = step as f64 / 8.0;
            let x = (camera_x as f64 + (site.x - camera_x) as f64 * t) * 2.0;
            let z = (camera_z as f64 + (site.z - camera_z) as f64 * t) * 2.0;
            let ground = terrain.surface_column(x.round() as i64, z.round() as i64);
            let clearance_y = (ground.height + 1) as f64 / 2.0 + 3.0;
            camera_y = camera_y.max((clearance_y - t * target_y) / (1.0 - t) - 1.62);
        }
        if camera_y < best.1 {
            best = ([camera_x as f64, camera_y, camera_z as f64], camera_y);
        }
    }
    best.0
}
fn main() {
    let output = env::args().nth(1).expect("output JSON path");
    let mut counts = BTreeMap::<String, u64>::new();
    let mut best = BTreeMap::<String, Site>::new();
    for seed in SEEDS {
        let world = World::new(seed);
        let t = world.terrain_sampler();
        let mut seen = BTreeMap::<String, u64>::new();
        let mut candidates = BTreeMap::<String, Vec<(i64, i64)>>::new();
        for z in (-RADIUS_METRES..=RADIUS_METRES).step_by(STRIDE_METRES) {
            for x in (-RADIUS_METRES..=RADIUS_METRES).step_by(STRIDE_METRES) {
                let c = t.surface_column(x * 2, z * 2);
                let name = c.biome.name().to_owned();
                *counts.entry(name.clone()).or_default() += 1;
                let n = seen.entry(name.clone()).or_default();
                *n += 1;
                let sites = candidates.entry(name).or_default();
                if sites.len() < 48 {
                    sites.push((x, z));
                } else {
                    let slot =
                        mix((x as u64).wrapping_mul(31) ^ (z as u64).rotate_left(19) ^ seed) % *n;
                    if slot < 48 {
                        sites[slot as usize] = (x, z);
                    }
                }
            }
        }
        for (name, sites) in candidates {
            for (x, z) in sites {
                let c = t.surface_column(x * 2, z * 2);
                let height = (c.height + 1) as f64 / 2.;
                let water = c.water.map_or(height, |w| (w.level + 1) as f64 / 2.);
                let mut score = 0;
                for r in [32, 64, 128] {
                    for (dx, dz) in [(-r, 0), (r, 0), (0, -r), (0, r), (-r, -r), (r, r)] {
                        let n = t.surface_column((x + dx) * 2, (z + dz) * 2);
                        score += if n.biome == c.biome { 100 } else { 0 };
                    }
                }
                // Prefer broad habitat interiors with a readable shoreline.
                score -= ((water - height).max(0.) * 0.2) as i64;
                // A snowy summit's bare cliff can carry the same biome label
                // as its snow cap. Prefer a visible cap among equally broad
                // interiors; the frequency count above remains unbiased.
                if c.biome == Biome::SnowyPeaks && c.material == voxelgame_core::world::Block::SNOW
                {
                    score += 20;
                }
                let site = Site {
                    seed,
                    x,
                    z,
                    height,
                    water,
                    score,
                };
                // Interior scores saturate on most seeds, so a strict
                // comparison let the first seed win every tie and the atlas
                // showed one world. Ties are broken by a per-biome hash so
                // the photographed sites spread across the survey seeds.
                let tie_break = |seed: u64| mix(seed ^ hash_name(&name));
                if best.get(&name).map_or(true, |b| {
                    score > b.score || (score == b.score && tie_break(seed) < tie_break(b.seed))
                }) {
                    best.insert(name.clone(), site);
                }
            }
        }
        eprintln!(
            "seed {seed}: {} biomes; cumulative {}",
            seen.len(),
            counts.len()
        );
    }
    let mut rows = Vec::new();
    for biome in Biome::ALL {
        let name = biome.name();
        let count = counts.get(name).copied().unwrap_or(0);
        let s = best
            .get(name)
            .expect("Every biome needs a natural sampled site");
        let camera = clear_camera(*s);
        rows.push(format!("{{\"id\":\"{biome:?}\",\"name\":\"{name}\",\"count\":{count},\"seed\":\"{}\",\"x\":{},\"z\":{},\"height\":{},\"water\":{},\"camera\":{:?},\"interiorScore\":{}}}",s.seed,s.x,s.z,s.height,s.water,camera,s.score));
    }
    let generator_version = GeneratorVersion::Current as u32;
    fs::write(output,format!("{{\"generatorVersion\":{generator_version},\"seeds\":{:?},\"radiusMetres\":{RADIUS_METRES},\"strideMetres\":{STRIDE_METRES},\"totalSamples\":{},\"biomes\":[{}]}}\n",SEEDS,counts.values().sum::<u64>(),rows.join(",\n"))).unwrap();
}
