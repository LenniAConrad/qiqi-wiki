// SPDX-License-Identifier: GPL-3.0-only
//! Sample a local photography map without changing the frequency survey.
//! Usage: photo_grid SEED X Z RADIUS STRIDE OUTPUT.csv (coordinates in metres).
use std::{
    env,
    fs::File,
    io::{BufWriter, Write},
};
use voxelgame_core::world::World;
fn main() {
    let args: Vec<_> = env::args().collect();
    assert_eq!(args.len(), 7, "SEED X Z RADIUS STRIDE OUTPUT.csv");
    let seed = args[1].parse::<u64>().expect("seed");
    let x = args[2].parse::<i64>().expect("x");
    let z = args[3].parse::<i64>().expect("z");
    let radius = args[4].parse::<i64>().expect("radius");
    let stride = args[5].parse::<usize>().expect("stride");
    assert!(radius > 0 && stride > 0);
    let world = World::new(seed);
    let sampler = world.terrain_sampler();
    let mut output = BufWriter::new(File::create(&args[6]).unwrap());
    writeln!(output, "x,z,height,water,biome,material").unwrap();
    for cz in (z - radius..=z + radius).step_by(stride) {
        for cx in (x - radius..=x + radius).step_by(stride) {
            let c = sampler.surface_column(cx * 2, cz * 2);
            let height = (c.height + 1) as f64 / 2.0;
            let water = c.water.map_or(height, |w| (w.level + 1) as f64 / 2.0);
            writeln!(
                output,
                "{cx},{cz},{height},{water},{:?},{:?}",
                c.biome, c.material
            )
            .unwrap();
        }
    }
}
