// SPDX-License-Identifier: GPL-3.0-only
//! Export actual procedural terrain for an offline island overview.
//! Usage: island_grid ID SEED MIN_X MIN_Z MAX_X MAX_Z RESOLUTION OUTPUT_STEM
//! Coordinates and surface heights are metres. Samples include both endpoints.

use std::{collections::BTreeMap, env, fs, io, path::Path, thread};
use voxelgame_core::world::{Block, GeneratorVersion, World, VOXELS_PER_METRE};

fn argument<T: std::str::FromStr>(value: &str) -> io::Result<T> {
    value
        .parse()
        .map_err(|_| io::Error::new(io::ErrorKind::InvalidInput, value.to_owned()))
}

fn main() -> io::Result<()> {
    let args: Vec<_> = env::args().collect();
    if args.len() != 9 {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "ID SEED MIN_X MIN_Z MAX_X MAX_Z RESOLUTION OUTPUT_STEM",
        ));
    }
    let id = &args[1];
    let name = match id.as_str() {
        "Rounded" => "Rounded",
        "Long" => "Long",
        "Crescent" => "Crescent",
        "TwinLobed" => "Twin-lobed",
        "Rugged" => "Rugged",
        "Atoll" => "Atoll",
        _ => {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "unknown island family",
            ))
        }
    };
    let seed: u64 = argument(&args[2])?;
    let bounds: [i64; 4] = [
        argument(&args[3])?,
        argument(&args[4])?,
        argument(&args[5])?,
        argument(&args[6])?,
    ];
    let resolution: usize = argument(&args[7])?;
    let span = bounds[2] - bounds[0];
    if !(17..=2049).contains(&resolution)
        || span <= 0
        || span > 100_000
        || bounds[3] - bounds[1] != span
    {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "square positive bounds and 17..2049 samples required",
        ));
    }
    let spacing = span as f64 / (resolution - 1) as f64;
    let workers = thread::available_parallelism()
        .map_or(1, usize::from)
        .min(4);
    let stripes = thread::scope(|scope| {
        let mut jobs = Vec::new();
        for worker in 0..workers {
            let first = worker * resolution / workers;
            let last = (worker + 1) * resolution / workers;
            jobs.push(scope.spawn(move || {
                let world = World::new(seed);
                let terrain = world.terrain_sampler();
                let mut bytes = Vec::with_capacity((last - first) * resolution * 12);
                let mut palette = BTreeMap::new();
                let mut dry_weight = 0.0;
                let mut minimum = f32::INFINITY;
                let mut maximum = f32::NEG_INFINITY;
                let mut dry_bounds = [
                    f64::INFINITY,
                    f64::INFINITY,
                    f64::NEG_INFINITY,
                    f64::NEG_INFINITY,
                ];
                for row in first..last {
                    let z = bounds[1] as f64 + row as f64 * spacing;
                    for column in 0..resolution {
                        let x = bounds[0] as f64 + column as f64 * spacing;
                        let sample = terrain.surface_column(
                            (x * VOXELS_PER_METRE as f64).round() as i64,
                            (z * VOXELS_PER_METRE as f64).round() as i64,
                        );
                        let ground = (sample.height + 1) as f32 / VOXELS_PER_METRE as f32;
                        let water = sample
                            .water
                            .map_or(f32::NAN, |w| (w.level + 1) as f32 / VOXELS_PER_METRE as f32);
                        let water_material = sample.water.map_or(Block::AIR, |w| w.material);
                        bytes.extend_from_slice(&ground.to_le_bytes());
                        bytes.extend_from_slice(&water.to_le_bytes());
                        bytes.extend_from_slice(&[
                            sample.material.0,
                            sample.biome as u8,
                            water_material.0,
                            0,
                        ]);
                        palette.insert(sample.material.0, sample.material.color());
                        palette.insert(water_material.0, water_material.color());
                        minimum = minimum.min(ground);
                        maximum = maximum.max(ground);
                        if sample.water.is_none() {
                            let wx = if column == 0 || column == resolution - 1 {
                                0.5
                            } else {
                                1.0
                            };
                            let wz = if row == 0 || row == resolution - 1 {
                                0.5
                            } else {
                                1.0
                            };
                            dry_weight += wx * wz;
                            dry_bounds[0] = dry_bounds[0].min(x);
                            dry_bounds[1] = dry_bounds[1].min(z);
                            dry_bounds[2] = dry_bounds[2].max(x);
                            dry_bounds[3] = dry_bounds[3].max(z);
                        }
                    }
                }
                (bytes, palette, dry_weight, minimum, maximum, dry_bounds)
            }));
        }
        jobs.into_iter()
            .map(|job| job.join().unwrap())
            .collect::<Vec<_>>()
    });
    let stem = Path::new(&args[8]);
    if let Some(parent) = stem.parent() {
        fs::create_dir_all(parent)?;
    }
    let binary = stem.with_extension("bin");
    let sidecar = stem.with_extension("json");
    let mut bytes = Vec::with_capacity(resolution * resolution * 12);
    let mut palette = BTreeMap::new();
    let mut dry_weight = 0.0;
    let mut minimum = f32::INFINITY;
    let mut maximum = f32::NEG_INFINITY;
    let mut dry_bounds = [
        f64::INFINITY,
        f64::INFINITY,
        f64::NEG_INFINITY,
        f64::NEG_INFINITY,
    ];
    for (stripe, colors, dry, low, high, bounds) in stripes {
        bytes.extend(stripe);
        palette.extend(colors);
        dry_weight += dry;
        minimum = minimum.min(low);
        maximum = maximum.max(high);
        dry_bounds[0] = dry_bounds[0].min(bounds[0]);
        dry_bounds[1] = dry_bounds[1].min(bounds[1]);
        dry_bounds[2] = dry_bounds[2].max(bounds[2]);
        dry_bounds[3] = dry_bounds[3].max(bounds[3]);
    }
    let palette = palette
        .into_iter()
        .map(|(id, c)| format!("\"{id}\":[{},{},{},{}]", c[0], c[1], c[2], c[3]))
        .collect::<Vec<_>>()
        .join(",");
    let area = dry_weight * spacing * spacing / 1_000_000.0;
    let dry_bounds = if dry_weight > 0.0 {
        format!("{dry_bounds:?}")
    } else {
        "null".to_owned()
    };
    let metadata = format!("{{\n\"schemaVersion\":1,\"id\":\"{id}\",\"name\":\"{name}\",\"seed\":\"{seed}\",\"generatorVersion\":{},\n\"resolution\":{resolution},\"bounds\":{:?},\"spacingMetres\":{spacing},\"northUp\":true,\"recordBytes\":12,\"dataFile\":\"{}\",\n\"palette\":{{{palette}}},\"heightRangeMetres\":[{minimum},{maximum}],\"dryBoundsMetres\":{dry_bounds},\"sampledDryAreaKm2\":{area},\"areaMethod\":\"Endpoint surface samples with trapezoidal area weights; all dry terrain inside the map frame.\"\n}}\n",GeneratorVersion::Current as u8,bounds,binary.file_name().unwrap().to_string_lossy());
    fs::write(&binary, bytes)?;
    fs::write(&sidecar, metadata)?;
    eprintln!("{}: {resolution}² samples, {spacing:.3}m spacing, {area:.3}km² dry, height{minimum}..{maximum}m",sidecar.display());
    Ok(())
}
