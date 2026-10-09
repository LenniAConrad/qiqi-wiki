#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Export real island plans, terrain and private climate fields for the atlas.

No worldgen formula is reimplemented here. The core's ignored devtools tests
export its private plans/fields, and island_grid queries World.surface_column.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

SITE = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_snapshot(game: Path) -> dict[str, str]:
    files = [game / "Cargo.toml", game / "Cargo.lock", game / "crates/voxelgame-core/Cargo.toml"]
    files += sorted((game / "crates/voxelgame-core/src").rglob("*.rs"))
    return {str(path.relative_to(game)): digest(path) for path in files}


def run(command: list[str], cwd: Path, extra_env: dict[str, str] | None = None) -> None:
    print("Running:", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env={**os.environ, **(extra_env or {})}, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=SITE.parent / "Voxelgame")
    parser.add_argument("--output", type=Path, default=SITE / ".cache/island-atlas")
    parser.add_argument("--sites", type=Path, default=SITE / "tools/island_sites.json")
    parser.add_argument("--cargo", default="cargo")
    parser.add_argument("--target-dir", type=Path, help="share a Cargo target directory with other frozen-source samplers")
    parser.add_argument("--resolution", type=int, default=1025)
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--without-climate", action="store_true")
    args = parser.parse_args()
    if not 17 <= args.resolution <= 2049:
        parser.error("resolution must be 17..2049")
    game = args.game.resolve()
    output = args.output.resolve()
    grids = output / "grids"
    grids.mkdir(parents=True, exist_ok=True)
    sources = source_snapshot(game)
    run([args.cargo, "test", "-p", "voxelgame-core", "--features", "devtools",
         "export_island_atlas_candidates", "--", "--ignored", "--nocapture"], game)
    candidate_path = game / ".cache/island-atlas/candidates.csv"
    with candidate_path.open() as handle:
        candidates = list(csv.DictReader(handle))
    (output / "candidates.csv").write_bytes(candidate_path.read_bytes())
    # Build against --game itself, never the live checkout hardcoded in the
    # maintained survey manifest. This keeps an isolated source snapshot
    # authoritative even while unrelated game work continues elsewhere.
    project = output / "sampler-project"
    (project / "src/bin").mkdir(parents=True, exist_ok=True)
    sampler_source = SITE / "tools/survey/src/bin/island_grid.rs"
    shutil.copy2(sampler_source, project / "src/bin/island_grid.rs")
    shutil.copy2(SITE / "tools/survey/Cargo.lock", project / "Cargo.lock")
    core = json.dumps(str(game / "crates/voxelgame-core"))
    (project / "Cargo.toml").write_text(
        '# SPDX-License-Identifier: GPL-3.0-only\n'
        '[package]\nname = "qiqi-biome-survey"\nversion = "0.1.0"\n'
        'edition = "2021"\nrust-version = "1.75"\nlicense = "GPL-3.0-only"\n'
        f'[dependencies]\nvoxelgame-core = {{ path = {core} }}\n'
    )
    target = args.target_dir.resolve() if args.target_dir else output / "sampler-target"
    run([args.cargo, "build", "--release", "--locked", "--manifest-path",
         str(project / "Cargo.toml"), "--target-dir", str(target), "--bin", "island_grid"], SITE)
    sampler = target / "release/island_grid"
    selected = json.loads(args.sites.read_text())["islands"]
    islands = []
    versions = set()
    climate_rows = []
    for site in selected:
        matches = [row for row in candidates if row["shape"] == site["id"]
                   and row["seed"] == site["seed"]
                   and [int(row["cell_x"]), int(row["cell_z"])] == site["cell"]]
        if len(matches) != 1:
            raise RuntimeError(f"curated site no longer appears in actual plan export: {site}")
        plan = matches[0]
        centre = [float(plan["centre_x"]), float(plan["centre_z"])]
        half = site["spanMetres"] // 2
        cx, cz = map(round, centre)
        bounds = [cx - half, cz - half, cx + half, cz + half]
        stem = grids / site["slug"]
        run([str(sampler), site["id"], site["seed"], *map(str, bounds),
             str(args.resolution), str(stem)], SITE)
        sample = json.loads(stem.with_suffix(".json").read_text())
        version = sample["generatorVersion"]
        versions.add(version)
        dry_bounds = sample["dryBoundsMetres"]
        if dry_bounds is None or sample["sampledDryAreaKm2"] <= 0:
            raise RuntimeError(f"curated island has no sampled dry terrain: {site['id']}")
        binary = stem.with_suffix(".bin")
        if binary.stat().st_size != args.resolution ** 2 * 12:
            raise RuntimeError(f"bad grid length: {binary}")
        climate_rows.append([site["id"], site["seed"], *bounds, args.resolution])
        islands.append({
            "id": site["id"], "name": "Twin-lobed" if site["id"] == "TwinLobed" else site["id"],
            "shape": plan["shape"], "slug": site["slug"], "description": site["description"],
            "seed": plan["seed"], "identity": plan["identity"], "cell": site["cell"],
            "centerMetres": centre, "sizeMetres": [float(plan["major_radius"]) * 2, float(plan["minor_radius"]) * 2],
            "tier": plan["tier"], "rangeHeadingDegrees": float(plan["heading_degrees"]),
            "growthFactor": float(plan["growth"]), "satelliteCount": int(plan["satellites"]),
            "boundsMetres": dict(zip(["minX", "minZ", "maxX", "maxZ"], bounds)),
            "dryBoundsMetres": dict(zip(["minX", "minZ", "maxX", "maxZ"], dry_bounds)),
            "areaKm2": sample["sampledDryAreaKm2"], "areaMethod": sample["areaMethod"],
            "heightRangeMetres": sample["heightRangeMetres"], "gridStem": str(stem),
            "gridResolution": args.resolution, "gridSha256": digest(binary), "views": [],
        })
    if len(versions) != 1:
        raise RuntimeError(f"mixed generator versions: {versions}")
    version = versions.pop()
    with (output / "climate-input.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "seed", "minX", "minZ", "maxX", "maxZ", "resolution"])
        writer.writerows(climate_rows)
    if not args.without_climate:
        run([args.cargo, "test", "-p", "voxelgame-core", "--features", "devtools",
             "export_island_atlas_climate", "--", "--ignored", "--nocapture"], game,
            {"VOXELGAME_ATLAS_CLIMATE_INPUT": str(output / "climate-input.csv"),
             "VOXELGAME_ATLAS_CLIMATE_OUTPUT": str(grids)})
        for island in islands:
            path = grids / f"{island['slug']}-climate.json"
            climate = json.loads(path.read_text())
            if climate["generatorVersion"] != version or climate["resolution"] != args.resolution:
                raise RuntimeError(f"climate provenance mismatch: {path}")
            binary = grids / climate["dataFile"]
            if binary.stat().st_size != args.resolution ** 2 * 24:
                raise RuntimeError(f"bad climate grid length: {binary}")
            island["climateStem"] = str(path.with_suffix(""))
            island["climateSha256"] = digest(binary)
    if sources != source_snapshot(game):
        raise RuntimeError("game source changed while sampling; rerun from a frozen snapshot")
    catalog = {"schemaVersion": 1, "generatorVersion": version, "date": args.date,
               "sizeMethod": "Planned long and short ellipse axes, not a measured coastline diameter.",
               "islands": islands}
    (output / "geometry.json").write_text(json.dumps(catalog, indent=2) + "\n")
    provenance = {"generatorVersion": version, "date": args.date,
                  "method": "Actual core island plans and surface-column terrain; private terrain_profile climate fields.",
                  "sourceFiles": sources, "samplerSha256": digest(sampler),
                  "samplerSourceSha256": digest(sampler_source), "samplerLockSha256": digest(project / "Cargo.lock"),
                  "candidateCsvSha256": digest(candidate_path), "sitesSha256": digest(args.sites)}
    (output / "grid-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"Ready: {output / 'geometry.json'} ({len(islands)} generation-{version} islands)", flush=True)


if __name__ == "__main__":
    main()
