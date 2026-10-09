#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Render sampled, unedited island terrain in Blender without a game window.

blender --background --python tools/render_islands.py -- --input DIR --output DIR

The exporter supplies real generated heights, water and material colors.
This is a terrain overview: vegetation, caves and half-metre surface detail are
not reconstructed. Horizontal and vertical units share the same scale.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

RECORD = np.dtype([("ground", "<f4"), ("water", "<f4"),
                   ("material", "u1"), ("biome", "u1"),
                   ("water_material", "u1"), ("padding", "u1")])


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ids", nargs="*")
    parser.add_argument("--width", type=int, default=3840)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--overwrite", action="store_true")
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(tail)
    if not 640 <= args.width <= 7680 or not 1 <= args.samples <= 128:
        parser.error("width must be 640..7680; samples must be 1..128")
    return args


def reset_scene(width, samples):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                       bpy.data.lights):
        for item in list(collection):
            if item.users == 0:
                collection.remove(item)
    scene = bpy.context.scene
    engines = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.render.resolution_x = width
    scene.render.resolution_y = width * 9 // 16
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 25
    scene.render.film_transparent = False
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = samples
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = -0.25
    if bpy.app.version < (5, 0, 0):
        scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.22, 0.31, 0.42, 1.0)
    background.inputs["Strength"].default_value = 0.65
    sun_data = bpy.data.lights.new("Late afternoon sun", "SUN")
    sun_data.energy = 3.0
    sun_data.angle = math.radians(3)
    sun = bpy.data.objects.new("Late afternoon sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(48), math.radians(-18), math.radians(-35))
    return scene


def colored_material(name, water=False):
    material = bpy.data.materials.new(name)
    if bpy.app.version < (5, 0, 0):
        material.use_nodes = True
    nodes = material.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    color = nodes.new("ShaderNodeVertexColor")
    color.layer_name = "SurfaceColor"
    material.node_tree.links.new(color.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.30 if water else 0.92
    shader.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.35 if water else 0.12
    return material


def create_mesh(name, coordinates, faces, colors, water=False):
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(coordinates))
    mesh.vertices.foreach_set("co", coordinates.astype(np.float32).ravel())
    mesh.loops.add(faces.size)
    mesh.loops.foreach_set("vertex_index", faces.astype(np.int32).ravel())
    mesh.polygons.add(len(faces))
    mesh.polygons.foreach_set("loop_start", np.arange(len(faces), dtype=np.int32) * 4)
    mesh.polygons.foreach_set("loop_total", np.full(len(faces), 4, dtype=np.int32))
    mesh.update()
    attribute = mesh.color_attributes.new(name="SurfaceColor", type="FLOAT_COLOR", domain="POINT")
    attribute.data.foreach_set("color", colors.astype(np.float32).ravel())
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(colored_material(name, water))
    return obj


def load_grid(path):
    meta = json.loads(path.read_text())
    n = meta["resolution"]
    if meta["recordBytes"] != 12 or not 65 <= n <= 2049:
        raise ValueError(f"unsupported terrain grid: {path}")
    records = np.fromfile(path.parent / meta["dataFile"], dtype=RECORD)
    if records.size != n * n or not np.isfinite(records["ground"]).all():
        raise ValueError(f"invalid terrain samples: {path}")
    return meta, records.reshape(n, n)


def make_terrain(meta, grid):
    n = len(grid)
    minimum_x, minimum_z, maximum_x, maximum_z = meta["bounds"]
    span = max(maximum_x - minimum_x, maximum_z - minimum_z) / 1000.0
    # One Blender unit = one kilometre on ALL three axes. North is +Y.
    x, north = np.meshgrid(np.linspace(-(maximum_x - minimum_x) / 2000,
                                      (maximum_x - minimum_x) / 2000, n),
                           np.linspace((maximum_z - minimum_z) / 2000,
                                       -(maximum_z - minimum_z) / 2000, n))
    coordinates = np.column_stack((x.ravel(), north.ravel(), grid["ground"].ravel() / 1000))
    cell = np.arange(n * n, dtype=np.int32).reshape(n, n)[:-1, :-1].ravel()
    faces = np.column_stack((cell, cell + n, cell + n + 1, cell + 1))
    palette = np.ones((256, 4), dtype=np.float32)
    for key, value in meta["palette"].items():
        palette[int(key)] = value
    colors = palette[grid["material"].ravel()].copy()
    create_mesh("Generated terrain", coordinates, faces, colors)

    wet = np.isfinite(grid["water"])
    levels = grid["water"][wet]
    if not levels.size:
        raise ValueError("an island overview must contain surrounding water")
    sea = float(np.median(levels))
    water_heights = np.where(wet, grid["water"], sea)
    coordinates[:, 2] = (water_heights.ravel() + 0.03) / 1000
    # Only sampled wet cells receive a surface. Dry corners stay below land.
    wet_faces = (wet[:-1, :-1] | wet[1:, :-1] | wet[1:, 1:] | wet[:-1, 1:]).ravel()
    depth = np.maximum(water_heights - grid["ground"], 0).ravel()
    blend = np.clip(depth / 16.0, 0, 1)[:, None]
    shallow = np.array([0.10, 0.40, 0.39])
    deep = np.array([0.022, 0.12, 0.22])
    water_colors = np.column_stack((shallow * (1 - blend) + deep * blend,
                                    np.ones(n * n)))
    create_mesh("Generated water levels", coordinates, faces[wet_faces], water_colors, True)
    # The far ocean continues beyond the bounded data tile; its level comes
    # from the actual surrounding sea samples, and it sits below inland water.
    bpy.ops.mesh.primitive_plane_add(size=span * 16, location=(0, 0, sea / 1000 - 0.0002))
    ocean = bpy.context.active_object
    ocean.name = "Surrounding ocean"
    material = bpy.data.materials.new("Deep sea continuation")
    if bpy.app.version < (5, 0, 0):
        material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*deep, 1)
    shader.inputs["Roughness"].default_value = 0.30
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.35
    ocean.data.materials.append(material)
    return span, sea, float(grid["ground"].max())


def make_camera(span, sea, maximum):
    data = bpy.data.cameras.new("Whole island camera")
    data.type = "ORTHO"
    data.ortho_scale = span * 1.15
    data.clip_start = 0.01
    data.clip_end = span * 30
    camera = bpy.data.objects.new("Whole island camera", data)
    bpy.context.collection.objects.link(camera)
    target = Vector((0, 0, (sea + (maximum - sea) * 0.22) / 1000))
    direction = Vector((0.12, -1.0, 0.92)).normalized()
    camera.location = target + direction * span * 2
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = camera
    return camera


def main():
    args = arguments()
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted(args.input.glob("*.json")):
        raw = json.loads(path.read_text())
        if raw.get("recordBytes") != 12 or (args.ids and raw["id"] not in args.ids):
            continue
        meta, grid = load_grid(path)
        slug = "twin-lobed" if meta["id"] == "TwinLobed" else meta["id"].lower()
        output = args.output / f"{slug}--panorama.png"
        if output.exists() and not args.overwrite:
            continue
        started = time.monotonic()
        scene = reset_scene(args.width, args.samples)
        span, sea, maximum = make_terrain(meta, grid)
        camera = make_camera(span, sea, maximum)
        scene.render.filepath = str(output.resolve())
        bpy.ops.render.render(write_still=True)
        record = {"id": meta["id"], "file": output.name, "width": args.width,
                  "height": args.width * 9 // 16, "generatorVersion": meta["generatorVersion"],
                  "seed": meta["seed"], "bounds": meta["bounds"],
                  "spacingMetres": meta["spacingMetres"], "verticalScale": 1,
                  "renderedSpanMetres": span * 1000,
                  "cameraPositionKilometres": list(camera.location),
                  "cameraClipMetres": camera.data.clip_end * 1000,
                  "renderer": f"Blender {bpy.app.version_string} / {scene.render.engine}",
                  "terrainGridSha256": hashlib.sha256((path.parent / meta["dataFile"]).read_bytes()).hexdigest(),
                  "imageSha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                  "seconds": round(time.monotonic() - started, 2)}
        (args.output / f"{slug}--panorama.json").write_text(json.dumps(record, indent=2) + "\n")
        records.append(record)
        print(f"Rendered {meta['id']}: {record['seconds']} seconds", flush=True)
    if not records:
        print("No unfinished matching island grids.", flush=True)


if __name__ == "__main__":
    main()
