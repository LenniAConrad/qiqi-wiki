// SPDX-License-Identifier: GPL-3.0-only
//! Recheck curated atlas locations against the current generator.
//! Input: id,seed,x,z,camera_x,camera_z CSV, without a header.
use std::{env, fs};
use voxelgame_core::world::World;

fn main() {
    let args: Vec<_> = env::args().collect();
    let input = fs::read_to_string(&args[1]).unwrap();
    let mut rows = Vec::new();
    for line in input.lines() {
        let p: Vec<_> = line.split(',').collect();
        let world = World::new(p[1].parse().unwrap());
        let t = world.terrain_sampler();
        let column = |x: &str, z: &str| {
            t.surface_column(
                (x.parse::<f64>().unwrap() * 2.0).floor() as i64,
                (z.parse::<f64>().unwrap() * 2.0).floor() as i64,
            )
        };
        let c = column(p[2], p[3]);
        let camera = column(p[4], p[5]);
        assert_eq!(format!("{:?}", c.biome), p[0], "stale biome location");
        let height = (c.height + 1) as f64 / 2.0;
        let water = c.water.map_or(height, |w| (w.level + 1) as f64 / 2.0);
        let camera_ground = (camera.height + 1) as f64 / 2.0;
        rows.push(format!(
            "\"{}\":{{\"height\":{height},\"water\":{water},\"cameraGround\":{camera_ground}}}",
            p[0]
        ));
    }
    fs::write(&args[2], format!("{{{}}}\n", rows.join(",\n"))).unwrap();
}
