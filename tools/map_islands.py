#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Draw north-up terrain maps and physical debug layers from island grid exports."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

RECORD = np.dtype([("ground", "<f4"), ("water", "<f4"),
                   ("material", "u1"), ("biome", "u1"),
                   ("water_material", "u1"), ("padding", "u1")])

# Fixed ranges make different island cards comparable. These are the actual
# generator fields, not estimates reverse-engineered from the biome label.
RAMPS = {
    "temperature": ["#334d9a", "#48a6bc", "#ecedb8", "#ecaa60", "#a63239"],
    "moisture": ["#ad7849", "#d9bf87", "#94c09d", "#43aeb2", "#35639f"],
    "ruggedness": ["#343759", "#665683", "#b98092", "#e7b986", "#faf0b1"],
    "elevation": ["#244665", "#43878b", "#789e6a", "#b8bb89", "#faf0d9"],
}


def color_ramp(values, stops, minimum, maximum):
    colors = np.array([[int(color[i:i + 2], 16) for i in (1, 3, 5)] for color in stops])
    normalized = np.clip((values - minimum) / (maximum - minimum), 0, 1)
    return np.uint8(np.stack([np.interp(normalized, np.linspace(0, 1, len(colors)),
                                      colors[:, channel]) for channel in range(3)], axis=-1))


def debug_layers(path, meta, grid):
    values = grid["ground"]
    # Include the full sampled relief, rounded to 100 m intervals.
    maximum = max(100, float(np.ceil(values.max() / 100) * 100))
    minimum = min(0, float(np.floor(values.min() / 100) * 100))
    yield "elevation", values, minimum, maximum, {
        "title": "Ground elevation · metres", "note": "Actual ground top-face height, including the sea floor. Water level is separate.",
        "stops": [{"color": color, "label": f"{value:g} m"} for color, value in
                  zip(RAMPS["elevation"], np.linspace(minimum, maximum, 5))]}, None
    slug = "twin-lobed" if meta["id"] == "TwinLobed" else meta["id"].lower()
    climate_path = path.parent / f"{slug}-climate.json"
    if not climate_path.exists():
        raise ValueError(f"missing physical climate grid {climate_path}")
    climate = json.loads(climate_path.read_text())
    for key in ["id", "seed", "generatorVersion", "resolution", "bounds"]:
        if climate[key] != meta[key]:
            raise ValueError(f"terrain/climate mismatch: {path}: {key}")
    binary = climate_path.parent / climate["dataFile"]
    fields = np.fromfile(binary, dtype="<f4")
    n = meta["resolution"]
    if climate["recordBytes"] != 24 or fields.size != n * n * 6 or not np.isfinite(fields).all():
        raise ValueError(f"invalid climate grid {climate_path}")
    fields = fields.reshape(n, n, 6)
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    for field in climate["fields"]:
        kind = field["id"]
        if kind not in RAMPS:
            continue
        minimum, maximum = field["displayRange"]
        labels = {"temperature": ["0 · cold", "0.25", "0.5", "0.75", "1 · warm"],
                  "moisture": ["0 · dry", "0.25", "0.5", "0.75", "1 · wet"],
                  "ruggedness": ["0 · low", "0.25", "0.5", "0.75", "1 · high"]}[kind]
        legend = {"title": f"{field['label']} · normalized", "note": field["description"],
                  "stops": [{"color": color, "label": label} for color, label in zip(RAMPS[kind], labels)]}
        yield kind, fields[..., field["byteOffset"] // 4], minimum, maximum, legend, digest


def load(path):
    meta = json.loads(path.read_text())
    records = np.fromfile(path.parent / meta["dataFile"], dtype=RECORD)
    n = meta["resolution"]
    if meta["recordBytes"] != RECORD.itemsize or records.size != n * n:
        raise ValueError(f"invalid terrain grid {path}")
    return meta, records.reshape(n, n)


def shade(heights, spacing):
    north, east = np.gradient(heights, spacing)
    normal = np.stack((-east, north, np.ones_like(heights)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    light = np.array([-0.45, 0.55, 0.70])
    light /= np.linalg.norm(light)
    return np.clip(0.62 + (normal @ light) * 0.50, 0.44, 1.10)


def map_colors(meta, grid):
    palette = np.ones((256, 4))
    for key, value in meta["palette"].items():
        palette[int(key)] = value
    colors = palette[grid["material"]][..., :3]
    # Material colors are the game's linear-light base palette.
    colors = np.clip(colors, 0, 1) ** (1 / 2.2)
    colors *= shade(grid["ground"], meta["spacingMetres"])[..., None]
    wet = np.isfinite(grid["water"])
    depth = np.maximum(np.where(wet, grid["water"] - grid["ground"], 0), 0)
    blend = np.clip(depth / 38, 0, 1)[..., None]
    shallow = np.array([0.29, 0.64, 0.64])
    deep = np.array([0.09, 0.24, 0.33])
    water = shallow * (1 - blend) + deep * blend
    colors[wet] = water[wet]
    return np.uint8(np.clip(colors * 255, 0, 255))


def mark_shores(image, grid):
    """Locate a debug field in the world without changing its color scale."""
    wet = np.isfinite(grid["water"])
    shore = np.zeros(wet.shape, dtype=bool)
    shore[:-1, :] |= wet[:-1, :] != wet[1:, :]
    shore[:, :-1] |= wet[:, :-1] != wet[:, 1:]
    mask = Image.fromarray(np.uint8(shore) * 255).resize(image.size, Image.Resampling.NEAREST)
    image.paste((245, 245, 232), (0, 0), mask)
    return image


def annotate(image, meta):
    image = image.convert("RGB")
    draw = ImageDraw.Draw(image)
    edge = image.width
    font_file = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_file, max(18, edge // 65))
    small = ImageFont.truetype(font_file, max(14, edge // 88))
    margin = edge // 30
    ink = (243, 242, 224)
    dark = (15, 36, 45)
    center = edge - margin * 1.5
    draw.rounded_rectangle((edge - margin * 3, margin / 2, edge - margin / 2, margin * 4),
                           radius=12, fill=dark)
    draw.text((center, margin * 0.8), "N", font=font, fill=ink, anchor="mt")
    draw.polygon([(center, margin * 1.6), (center - margin * 0.30, margin * 3.1),
                  (center, margin * 2.65), (center + margin * 0.30, margin * 3.1)], fill=ink)
    span = meta["bounds"][2] - meta["bounds"][0]
    choices = [100, 200, 500, 1000, 2000, 5000, 10000, 20000]
    length = max(value for value in choices if value <= span * 0.24)
    pixels = length / span * edge
    bottom = edge - margin
    draw.rounded_rectangle((margin / 2, bottom - margin * 1.65,
                            margin + pixels + margin / 2, bottom + margin / 2),
                           radius=10, fill=dark)
    draw.line((margin, bottom, margin + pixels, bottom), fill=ink, width=max(3, edge // 400))
    for x in (margin, margin + pixels):
        draw.line((x, bottom - 12, x, bottom + 6), fill=ink, width=max(3, edge // 400))
    label = f"{length / 1000:g} km" if length >= 1000 else f"{length} m"
    draw.text((margin, bottom - margin * 1.25), label, font=font, fill=ink)
    draw.text((edge - margin, edge - margin), "NORTH UP", font=small, fill=ink,
              anchor="rs", stroke_width=2, stroke_fill=dark)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--terrain-only", action="store_true", help="Preview a terrain grid before physical fields have been exported")
    args = parser.parse_args()
    if not 256 <= args.size <= 4096:
        parser.error("map size must be 256..4096")
    args.output.mkdir(parents=True, exist_ok=True)
    for path in sorted(args.input.glob("*.json")):
        raw = json.loads(path.read_text())
        if raw.get("recordBytes") != 12:
            continue
        meta, grid = load(path)
        slug = "twin-lobed" if meta["id"] == "TwinLobed" else meta["id"].lower()
        rgb = map_colors(meta, grid)
        image = Image.fromarray(rgb).resize((args.size, args.size), Image.Resampling.LANCZOS)
        image = annotate(image, meta)
        output = args.output / f"{slug}--map.png"
        image.save(output)
        record = {"id": meta["id"], "file": output.name, "width": args.size,
                  "height": args.size, "generatorVersion": meta["generatorVersion"],
                  "seed": meta["seed"], "bounds": meta["bounds"], "northUp": True,
                  "spacingMetres": meta["spacingMetres"],
                  "terrainGridSha256": hashlib.sha256((path.parent / meta["dataFile"]).read_bytes()).hexdigest(),
                  "imageSha256": hashlib.sha256(output.read_bytes()).hexdigest()}
        (args.output / f"{slug}--map.json").write_text(json.dumps(record, indent=2) + "\n")
        if not args.terrain_only:
            for kind, values, minimum, maximum, legend, digest in debug_layers(path, meta, grid):
                rgb = color_ramp(values, RAMPS[kind], minimum, maximum)
                layer = Image.fromarray(rgb).resize((args.size, args.size), Image.Resampling.BILINEAR)
                layer = annotate(mark_shores(layer, grid), meta)
                legend["note"] += " Pale lines mark sampled water margins."
                output = args.output / f"{slug}--{kind}.png"
                layer.save(output)
                details = {**record, "file": output.name, "kind": kind, "legend": legend,
                           "range": [minimum, maximum], "sampledRange": [float(values.min()), float(values.max())],
                           "imageSha256": hashlib.sha256(output.read_bytes()).hexdigest()}
                if digest:
                    details["climateGridSha256"] = digest
                (args.output / f"{slug}--{kind}.json").write_text(json.dumps(details, indent=2) + "\n")
        print(f"Mapped {meta['id']}: {args.size} × {args.size}")


if __name__ == "__main__":
    main()
