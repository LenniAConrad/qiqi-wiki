#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate the shipped island catalog, image integrity and source provenance."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, help="Check generator source hashes against this checkout")
    args = parser.parse_args()
    data = json.loads((ROOT / "data/islands.json").read_text())
    javascript = (ROOT / "data/islands.js").read_text()
    assert json.loads(javascript.split("window.ISLAND_ATLAS = ", 1)[1].rstrip(";\n")) == data
    assert data["generatorVersion"] == 9
    assert data["gridProvenance"]["generatorVersion"] == data["generatorVersion"]
    for name, expected_hash in data["renderToolsSha256"].items():
        assert hashlib.sha256((ROOT / "tools" / name).read_bytes()).hexdigest() == expected_hash
    expected = {"Rounded", "Long", "Crescent", "TwinLobed", "Rugged", "Atoll"}
    assert {island["id"] for island in data["islands"]} == expected
    assert len(data["islands"]) == 6
    digests = set()
    count = 0
    for island in data["islands"]:
        assert 0 <= int(island["seed"]) < 2 ** 64
        assert 0 < island["areaKm2"] < 1000
        assert all(length > 0 for length in island["sizeMetres"])
        bounds = island["boundsMetres"]
        assert bounds["minX"] < island["centerMetres"][0] < bounds["maxX"]
        assert bounds["minZ"] < island["centerMetres"][1] < bounds["maxZ"]
        assert len(island["terrainGridSha256"]) == len(island["climateGridSha256"]) == 64
        assert {view["type"] for view in island["views"]} == {
            "map", "panorama", "temperature", "moisture", "elevation", "ruggedness"}
        for view in island["views"]:
            path = ROOT / view["image"]
            assert path.resolve().is_relative_to((ROOT / "images/islands").resolve())
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == view["imageSha256"]
            assert digest not in digests
            digests.add(digest)
            with Image.open(path) as image:
                assert image.format == "WEBP"
                assert image.size == (view["width"], view["height"])
                extrema = image.convert("RGB").getextrema()
                assert max(high - low for low, high in extrema) > 50
            if view["type"] == "panorama":
                assert (view["width"], view["height"]) == (3840, 2160)
                assert view["verticalScale"] == 1
                assert view["cameraClipMetres"] > max(view["extentMetres"])
                assert "offline" in view["description"]
            else:
                assert (view["width"], view["height"]) == (2048, 2048)
                assert view["northUp"]
                if view["type"] != "map":
                    assert len(view["legend"]["stops"]) == 5
                    assert view["range"][0] <= view["sampledRange"][0] <= view["sampledRange"][1] <= view["range"][1]
            count += 1
    if args.game:
        sources = {**data["generatorSourcesSha256"],
                   "crates/voxelgame-core/src/world/generator.rs": data["generatorSha256"]}
        for name, expected_hash in sources.items():
            actual = hashlib.sha256((args.game / name).read_bytes()).hexdigest()
            assert actual == expected_hash, ("stale generator", name)
    print(f"Validated six generation-9 islands, {count} unique images and physical layer legends.")


if __name__ == "__main__":
    main()
