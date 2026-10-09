#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build original naturalistic procedural illustrations without source imagery.

Requires NumPy and Pillow. Geography, clouds and surface features are invented;
these are illustrative materials, not observations or actual game captures.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "images/scale"
EDGE = 2048
BODIES = ("sun", "mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune")


def coordinates():
    """Return pixel-centred coordinates with an exact two-unit diameter."""
    axis = (np.arange(EDGE, dtype=np.float32) + 0.5) * (2 / EDGE) - 1
    return np.meshgrid(axis, -axis)


def noise(u, v, frequency, seed):
    """Smooth seeded value noise; no downloaded inputs or texture dependencies."""
    grid = np.random.default_rng(seed).uniform(-1, 1, (256, 256)).astype(np.float32)
    x, y = u * frequency + 100, v * frequency + 100
    ix, iy = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32)
    a, b = x - ix.astype(np.float32), y - iy.astype(np.float32)
    a, b = a * a * (3 - 2 * a), b * b * (3 - 2 * b)
    return ((grid[iy % 256, ix % 256] * (1 - a) + grid[iy % 256, (ix + 1) % 256] * a) * (1 - b)
            + (grid[(iy + 1) % 256, ix % 256] * (1 - a) + grid[(iy + 1) % 256, (ix + 1) % 256] * a) * b).astype(np.float32)


def terrain(u, v, seed, frequency=3, octaves=7):
    """Fractal detail across continental, regional and fine material scales."""
    result = np.zeros_like(u)
    weight = 1.0
    for octave in range(octaves):
        result += weight * noise(u, v, frequency * 2 ** octave, seed + octave * 17)
        weight *= 0.49
    return result


def mix(a, b, amount):
    """Blend RGB colours or images by a scalar field."""
    t = np.clip(amount, 0, 1)[..., None]
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


def land_and_sea(u, v, seed, island=False):
    """Invented coastlines, shoals, forests, deserts and snowy highlands."""
    warp = terrain(u, v, seed + 501, 2.8, 3)
    height = terrain(u + warp * 0.12, v + warp * 0.08, seed, 3.4 if island else 2.0)
    # Ridged mountain chains follow broad geology, with fine branching valleys.
    ridge = 1 - np.abs(terrain(u, v, seed + 611, 8, 5))
    mountain = np.clip((height - 0.22) * 1.3, 0, 0.45)
    height += mountain * ridge * 0.27
    shore = 0.03 if island else -0.12
    depth = np.clip((shore - height) * 2.5, 0, 1)
    sea = mix([37, 132, 148] if island else [36, 103, 147],
              [6, 38, 66] if island else [9, 35, 78], depth)
    moisture = terrain(u + 4, v, seed + 91, 2, 4)
    land = mix([42, 79, 48], [126, 128, 72], moisture + 0.45)
    desert = np.clip((noise(u, v, 2.5, seed + 88) - 0.05) * 2, 0, 0.9)
    land = mix(land, [183, 155, 100], desert)
    land = mix(land, [151, 143, 125], np.clip((height - 0.43) * 2, 0, 1))
    land = mix(land, [225, 231, 226], np.clip((height - 0.73) * 4, 0, 1))
    beach = np.exp(-((height - shore - 0.018) / 0.025) ** 2) * 0.65
    land = mix(land, [195, 182, 130], beach)
    # Fine, irregular tributary-like ribbons within lowland terrain.
    drainage = np.abs(terrain(u + warp * 0.08, v, seed + 771, 5, 5))
    rivers = np.clip((0.007 - drainage) * 110, 0, 0.55)
    rivers *= np.clip((height - shore - 0.04) * 15, 0, 1) * np.clip((0.5 - height) * 5, 0, 1)
    land = mix(land, [37, 99, 107], rivers)
    rgb = mix(sea, land, (height - shore) * 130)
    dy, dx = np.gradient(height)
    relief = np.clip(1 + (dx - dy) * 32, 0.66, 1.2)
    rgb *= np.where(height > shore, relief, 1)[..., None]
    return rgb


def material(name, u, v):
    """Different natural materials, with invented surface features."""
    seed = 101 + BODIES.index(name) * 173
    broad = terrain(u, v, seed, 2.7, 6)
    fine = noise(u, v, 180, seed + 33)
    if name == "sun":
        granules = terrain(u, v, seed + 12, 95, 3)
        rgb = mix([231, 88, 9], [255, 214, 89], granules * 0.55 + 0.58)
        rgb = mix(rgb, [255, 237, 142], np.clip(broad * 0.3, 0, 0.22))
        # Sparse irregular spot groups, surrounded by a softer penumbra.
        rng = np.random.default_rng(4201)
        for _ in range(9):
            cx, cy = rng.uniform(-1.1, 1.1), rng.choice([-1, 1]) * rng.uniform(0.12, 0.55)
            radius = rng.uniform(0.013, 0.035)
            r = ((u - cx) / radius) ** 2 + ((v - cy) / (radius * 0.64)) ** 2
            r *= 1 + fine * 0.15
            rgb = mix(rgb, [180, 98, 33], np.exp(-r * 0.35) * 0.55)
            rgb = mix(rgb, [63, 32, 13], np.exp(-r * 1.7) * 0.92)
        return rgb
    if name == "earth":
        rgb = land_and_sea(u, v, seed)
        ice = np.clip((np.abs(v) - 1.17 + broad * 0.05) * 7, 0, 1)
        rgb = mix(rgb, [216, 231, 233], ice)
        # Rotational advection makes a coherent cloud system with finer wisps.
        dx, dy = u + 0.42, (v - 0.22) * 1.3
        radius = np.sqrt(dx * dx + dy * dy)
        twist = 1.7 * np.exp(-radius * radius / 0.32)
        cloud_u = -0.42 + dx * np.cos(twist) - dy * np.sin(twist)
        cloud_v = 0.22 + (dx * np.sin(twist) + dy * np.cos(twist)) / 1.3
        clouds = terrain(cloud_u + broad * 0.1, cloud_v, seed + 10, 5.5, 7)
        cover = np.clip((clouds - 0.16) * 2.5, 0, 0.96)
        shadow = np.roll(cover, (5, 6), axis=(0, 1)) * 0.12
        rgb *= (1 - shadow[..., None])
        return mix(rgb, [244, 248, 248], cover)
    if name in ("mercury", "mars"):
        a, b = ([65, 61, 59], [172, 160, 146]) if name == "mercury" else ([101, 49, 32], [210, 136, 87])
        rgb = mix(a, b, broad * 0.5 + 0.52)
        rgb *= (1 + fine * 0.09)[..., None]
        return rgb
    # Advected latitude bands with finer turbulent streaks.
    warp = terrain(u, v * 1.8, seed + 31, 4, 5)
    latitude = v + 0.055 * warp
    bands = (0.72 * np.sin(latitude * (39 if name == "jupiter" else 28))
             + 0.22 * np.sin(latitude * 63 + 1.2) + 0.12 * np.sin(latitude * 101))
    streak = terrain(u * 0.7, v * 4, seed + 49, 12, 5)
    if name == "venus":
        return mix([166, 124, 65], [245, 222, 165], 0.65 + broad * 0.28 + streak * 0.08)
    if name == "jupiter":
        rgb = mix([151, 102, 73], [226, 214, 190], bands * 0.32 + 0.52 + streak * 0.22)
        # Original illustrative oval storm, with turbulent concentric filaments.
        radius = np.sqrt(((u - 0.3) / 0.32) ** 2 + ((v + 0.25) / 0.12) ** 2)
        storm = np.clip((1 - radius + warp * 0.08) * 4, 0, 1)
        colour = mix([153, 80, 49], [217, 155, 105], 0.5 + 0.2 * np.sin(radius * 24) + streak * 0.3)
        return mix(rgb, colour, storm * 0.85)
    if name == "saturn":
        return mix([172, 151, 108], [239, 222, 174], 0.57 + bands * 0.15 + streak * 0.08)
    if name == "uranus":
        return mix([91, 163, 176], [158, 207, 208], 0.65 + bands * 0.025 + streak * 0.025)
    rgb = mix([24, 61, 132], [62, 120, 189], 0.5 + bands * 0.15 + streak * 0.12)
    clouds = np.clip((streak - 0.55) * 0.9, 0, 0.4)
    return mix(rgb, [186, 211, 231], clouds)


def craters(rgb, seed, amount):
    """Add relief to small local crater patches, not full-image temporary arrays."""
    rng = np.random.default_rng(seed)
    for _ in range(amount):
        cx, cy = rng.uniform(-0.85, 0.85, 2)
        if cx * cx + cy * cy > 0.8:
            continue
        radius = rng.uniform(0.006, 0.06)
        px, py = int((cx + 1) * EDGE / 2), int((1 - cy) * EDGE / 2)
        size = max(4, int(radius * EDGE))
        x0, x1 = max(0, px - size), min(EDGE, px + size)
        y0, y1 = max(0, py - size), min(EDGE, py + size)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        dx, dy = (xx - px) / size, (yy - py) / size
        # Foreshorten along the radial direction near the spherical limb.
        radial = max(0.001, np.hypot(cx, cy))
        along = (dx * cx - dy * cy) / radial
        across = (dx * cy + dy * cx) / radial
        r = np.sqrt((along / max(0.35, np.sqrt(1 - radial * radial))) ** 2 + across * across)
        irregular = 0.014 * np.sin(np.arctan2(dy, dx) * 11 + radius * 500)
        r += irregular
        ring = np.exp(-((r - 0.61) / 0.06) ** 2)
        basin = np.exp(-(r / 0.50) ** 6)
        interior = np.exp(-((r - 0.43) / 0.12) ** 2)
        relief = 1 - basin * 0.11 + ring * (-dx - dy) * 0.28 + interior * (dx + dy) * 0.2
        rgb[y0:y1, x0:x1] *= relief[..., None]


def globe(name):
    """Natural materials and directional illumination inside the exact disk."""
    x, y = coordinates()
    d = x * x + y * y
    z = np.sqrt(np.maximum(0, 1 - d))
    u, v = np.arctan2(x, z), np.arcsin(np.clip(y, -1, 1))
    rgb = material(name, u, v)
    if name in ("mercury", "mars"):
        craters(rgb, 527 if name == "mercury" else 927, 220 if name == "mercury" else 65)
    if name == "sun":
        light = 0.69 + 0.31 * z
    else:
        light = 0.16 + 0.84 * np.maximum(0, -0.3 * x + 0.35 * y + 0.89 * z)
    rgb *= light[..., None]
    if name in ("earth", "venus", "uranus", "neptune"):
        sunlight = np.clip(-0.3 * x + 0.35 * y + 0.89 * z, 0, 1)
        haze = (1 - z) ** 3 * (0.12 + 0.3 * sunlight)
        rgb = mix(rgb, [92, 158, 220] if name != "venus" else [222, 194, 147], haze)
        if name == "earth":
            # Restrained reflected light on blue ocean pixels only.
            ocean = np.clip((rgb[..., 2] - rgb[..., 1]) / 35, 0, 1)
            glint = np.exp(-((x + 0.18) ** 2 + (y - 0.22) ** 2) / 0.016) * ocean * 0.19
            rgb = mix(rgb, [212, 235, 245], glint)
    alpha = (np.clip((1 - np.sqrt(d)) * EDGE / 2 + 0.5, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(np.dstack((np.clip(rgb, 0, 255).astype(np.uint8), alpha))).save(
        OUTPUT / (name + ".webp"), quality=92, method=6)


def game_map(name):
    """Distinct original terrain maps; never imported game artwork."""
    x, y = coordinates()
    if name == "voxelgame":
        rgb = land_and_sea(x, y, 812, island=True)
    else:
        # Chunkier, broad continental terrain with a warmer palette.
        u, v = np.floor(x * 192) / 192, np.floor(y * 192) / 192
        rgb = land_and_sea(u, v, 31415, island=False)
        rgb *= np.array([1.1, 1.03, 0.86])
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(
        OUTPUT / (name + ".webp"), quality=92, method=6)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name in BODIES:
        globe(name)
        print("Rendered", name, flush=True)
    for name in ("voxelgame", "minecraft"):
        game_map(name)
        print("Rendered", name, flush=True)
    output = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUTPUT.glob("*.webp"))}
    (OUTPUT / "manifest.json").write_text(json.dumps({
        "style": "original naturalistic procedural illustrations; invented geography",
        "sourceImages": [], "globeEdge": EDGE, "mapEdge": EDGE, "outputs": output,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
