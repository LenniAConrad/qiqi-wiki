#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Package measured island grids and rendered views into the offline atlas."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
KINDS = ["map", "panorama", "temperature", "moisture", "elevation", "ruggedness"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--grids", type=Path, required=True)
    parser.add_argument("--renders", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    args = parser.parse_args()
    geometry = json.loads(args.geometry.read_text())
    manifest = json.loads(args.source_manifest.read_text())
    version = manifest["generatorVersion"]
    if geometry["generatorVersion"] != version:
        raise ValueError("island plan and source manifest generations differ")
    grid_provenance_path = args.geometry.parent / "grid-provenance.json"
    grid_provenance = json.loads(grid_provenance_path.read_text())
    if grid_provenance["generatorVersion"] != version:
        raise ValueError("stale grid provenance")
    generator_sources = {**manifest["generatorSourcesSha256"],
                         "crates/voxelgame-core/src/world/generator.rs": manifest["generatorSha256"]}
    if any(grid_provenance["sourceFiles"].get(name) != digest for name, digest in generator_sources.items()):
        raise ValueError("sampled generator differs from the frozen build")
    target = ROOT / "images/islands"
    target.mkdir(parents=True, exist_ok=True)
    islands = []
    for source in geometry["islands"]:
        slug = source["slug"]
        grid_path = args.grids / f"{slug}.json"
        grid = json.loads(grid_path.read_text())
        if grid["id"] != source["id"] or grid["seed"] != source["seed"] or grid["generatorVersion"] != version:
            raise ValueError(f"stale terrain grid {slug}")
        bounds = [source["boundsMetres"][key] for key in ["minX", "minZ", "maxX", "maxZ"]]
        if grid["bounds"] != bounds:
            raise ValueError(f"plan/grid bounds differ {slug}")
        grid_hash = sha(args.grids / grid["dataFile"])
        climate = json.loads((args.grids / f"{slug}-climate.json").read_text())
        climate_hash = sha(args.grids / climate["dataFile"])
        item = {key: value for key, value in source.items() if key not in ["gridStem", "scoutingSample", "views"]}
        item["areaKm2"] = grid["sampledDryAreaKm2"]
        item["areaMethod"] = grid["areaMethod"]
        item["heightRangeMetres"] = grid["heightRangeMetres"]
        item["sampleSpacingMetres"] = grid["spacingMetres"]
        item["terrainGridSha256"] = grid_hash
        item["climateGridSha256"] = climate_hash
        item["views"] = []
        for kind in KINDS:
            metadata = json.loads((args.renders / f"{slug}--{kind}.json").read_text())
            original = args.renders / metadata["file"]
            for key, expected in [("id", source["id"]), ("seed", source["seed"]), ("generatorVersion", version),
                                  ("bounds", bounds), ("terrainGridSha256", grid_hash), ("imageSha256", sha(original))]:
                if metadata[key] != expected:
                    raise ValueError(f"stale {slug}/{kind}: {key}")
            if kind in ["temperature", "moisture", "ruggedness"] and metadata["climateGridSha256"] != climate_hash:
                raise ValueError(f"stale climate image {slug}/{kind}")
            destination = target / f"{slug}--{kind}.webp"
            with Image.open(original) as image:
                if image.size != (metadata["width"], metadata["height"]):
                    raise ValueError(f"wrong dimensions {original}")
                image.convert("RGB").save(destination, "WEBP", quality=94, method=6)
            label = {"map": "Top-down terrain", "panorama": "Whole-island terrain panorama"}.get(kind, kind.capitalize())
            view = {"type": kind, "label": label, "image": destination.relative_to(ROOT).as_posix(),
                    "width": metadata["width"], "height": metadata["height"],
                    "imageSha256": sha(destination), "originalImageSha256": sha(original),
                    "alt": f"{source['name']} island: {label.lower()}, seed {source['seed']}",
                    "extentMetres": [bounds[2] - bounds[0], bounds[3] - bounds[1]],
                    "sampleSpacingMetres": grid["spacingMetres"]}
            if kind == "panorama":
                view.update({"verticalScale": metadata["verticalScale"], "renderer": metadata["renderer"],
                             "description": "4K offline rendering of actual sampled terrain and water at true vertical scale. Trees, caves and small structures are omitted.",
                             "cameraClipMetres": metadata["cameraClipMetres"]})
            else:
                view["northUp"] = True
                view["metresPerPixel"] = (bounds[2] - bounds[0]) / metadata["width"]
                view["description"] = f"Sampled every {grid['spacingMetres']:g} m; enlarged for display."
                if "legend" in metadata:
                    view["legend"] = metadata["legend"]
                    view["range"] = metadata["range"]
                    view["sampledRange"] = metadata["sampledRange"]
            item["views"].append(view)
        islands.append(item)
    atlas = {"schemaVersion": 1, "generatorVersion": version, "date": geometry["date"],
             "sizeMethod": geometry["sizeMethod"], "sourceManifestSha256": sha(args.source_manifest),
             "generatorSha256": manifest["generatorSha256"],
             "generatorSourcesSha256": manifest["generatorSourcesSha256"],
             "gridProvenance": grid_provenance,
             "renderToolsSha256": {name: sha(ROOT / "tools" / name) for name in ["map_islands.py", "render_islands.py"]},
             "renderMethod": "Offline terrain and water overview from production generator samples. No vertical exaggeration; vegetation, caves and small structures omitted.",
             "islands": islands}
    output = ROOT / "data/islands.json"
    output.write_text(json.dumps(atlas, indent=2) + "\n")
    output.with_suffix(".js").write_text("// SPDX-License-Identifier: GPL-3.0-only\nwindow.ISLAND_ATLAS = " + json.dumps(atlas, separators=(",", ":")) + ";\n")
    print(f"Packaged {len(islands)} islands / {len(islands) * len(KINDS)} views, generation {version}")


if __name__ == "__main__":
    main()
