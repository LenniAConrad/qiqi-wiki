#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate the portable village gallery, genuine captures and provenance."""

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SHA256 = re.compile(r"[0-9a-f]{64}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def vector(value, length):
    return isinstance(value, list) and len(value) == length and all(map(number, value))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, help="Also verify the exact frozen capture executable")
    args = parser.parse_args()
    data = json.loads((ROOT / "data/villages.json").read_text())
    javascript = (ROOT / "data/villages.js").read_text()
    assignment = "window.VILLAGE_GALLERY = "
    require(javascript.count(assignment) == 1, "Missing or repeated offline gallery assignment")
    encoded = javascript.split(assignment, 1)[1].strip().removesuffix(";")
    require(json.loads(encoded) == data, "Offline script differs from villages.json")
    for key in ("title", "description"):
        require(text(data[key]), f"Missing gallery {key}")
    require(data["packId"] == "chinese_village:pack", "Incorrect village pack ID")
    require(data["packVersion"] == "1.4.0", "Gallery must identify the photographed 1.4.0 pack")
    require(isinstance(data["seed"], str) and re.fullmatch(r"0|[1-9][0-9]*", data["seed"])
            and 0 <= int(data["seed"]) < 2 ** 64, "Seed must be an exact decimal-string u64")
    require(type(data["generatorVersion"]) is int and data["generatorVersion"] > 0,
            "Invalid generator version")
    captured = datetime.fromisoformat(data["capturedAt"].replace("Z", "+00:00"))
    require(captured.utcoffset() is not None and captured.utcoffset().total_seconds() == 0,
            "Capture timestamp must include UTC")
    provenance = data["provenance"]
    for key in ("binarySha256", "captureToolSha256"):
        require(isinstance(provenance[key], str) and SHA256.fullmatch(provenance[key]),
                f"Invalid provenance {key}")
    if args.binary:
        require(digest(args.binary) == provenance["binarySha256"], "Capture binary hash mismatch")

    shots = data["shots"]
    require(isinstance(shots, list) and len(shots) >= 10, "Expected at least ten village views")
    ids, paths, hashes, originals = set(), set(), set(), set()
    scenes = {"inspection": 0, "generated": 0}
    checked_originals = 0
    for shot in shots:
        label = shot["id"]
        require(isinstance(label, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", label),
                f"Invalid shot ID: {label!r}")
        require(label not in ids, f"Duplicate shot ID: {label}")
        ids.add(label)
        for key in ("title", "description", "category", "image", "evidence", "originalPng"):
            require(text(shot[key]), f"{label}: missing {key}")
        require(not Path(shot["evidence"]).is_absolute(), f"{label}: evidence path must be relative")
        require(shot["scene"] in scenes, f"{label}: unknown scene")
        scenes[shot["scene"]] += 1
        for key in ("seed", "generatorVersion", "packId", "packVersion"):
            if key in shot:
                require(shot[key] == data[key], f"{label}: inconsistent {key}")
        require(vector(shot["camera"]["positionMetres"], 3), f"{label}: invalid camera position")
        require(vector(shot["camera"]["lookDegrees"], 2), f"{label}: invalid camera direction")
        require(-90 <= shot["camera"]["lookDegrees"][1] <= 90, f"{label}: invalid camera pitch")
        require(vector(shot["anchorMetres"], 3), f"{label}: invalid village anchor")
        require(number(shot["time"]) and 0 <= shot["time"] <= 1, f"{label}: invalid day fraction")
        require(type(shot["warmupFrames"]) is int and shot["warmupFrames"] >= 120,
                f"{label}: missing renderer warm-up")
        renderer = shot["renderer"]
        require(isinstance(renderer, dict) and renderer.get("viewport") == [960, 540],
                f"{label}: renderer viewport differs from the native capture")
        radius, target = renderer.get("detail_clip_radius_metres"), renderer.get("detail_clip_target_metres")
        if radius is not None or target is not None:
            require(number(radius) and number(target) and radius + 0.01 >= target,
                    f"{label}: terrain was still streaming")
        require((shot["width"], shot["height"]) == (960, 540), f"{label}: incorrect dimensions")
        path = ROOT / shot["image"]
        require(not Path(shot["image"]).is_absolute()
                and path.resolve().is_relative_to((ROOT / "images/villages").resolve()),
                f"{label}: image must stay inside images/villages")
        require(path.resolve() not in paths, f"{label}: repeated image path")
        paths.add(path.resolve())
        for key in ("imageSha256", "originalImageSha256"):
            require(isinstance(shot[key], str) and SHA256.fullmatch(shot[key]), f"{label}: invalid {key}")
        image_hash = digest(path)
        require(image_hash == shot["imageSha256"], f"{label}: image hash mismatch")
        require(image_hash not in hashes, f"{label}: duplicate encoded photograph")
        hashes.add(image_hash)
        require(shot["originalImageSha256"] not in originals, f"{label}: duplicate original photograph")
        originals.add(shot["originalImageSha256"])
        with Image.open(path) as image:
            require(image.format == "WEBP" and image.size == (960, 540), f"{label}: invalid WebP")
            image.verify()
        with Image.open(path) as image:
            extrema = image.convert("RGB").getextrema()
            require(max(high - low for low, high in extrema) > 50, f"{label}: photograph is blank")
        original = ROOT / shot["originalPng"]
        require(not Path(shot["originalPng"]).is_absolute(), f"{label}: original path must be relative")
        if original.is_file():
            require(digest(original) == shot["originalImageSha256"], f"{label}: original PNG hash mismatch")
            with Image.open(original) as image:
                require(image.format == "PNG" and image.size == (960, 540), f"{label}: invalid original PNG")
                image.verify()
            checked_originals += 1
    require(scenes["inspection"] >= 8 and scenes["generated"] >= 2,
            "Gallery needs both inspection details and at least two generated-terrain views")
    print(f"PASS: {len(shots)} unique 960×540 village captures, offline mirror, metadata and provenance; "
          f"{checked_originals} available originals verified.")


if __name__ == "__main__":
    main()
