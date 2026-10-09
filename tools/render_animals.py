# SPDX-License-Identifier: GPL-3.0-only
"""Run with Blender --background --python tools/render_animals.py -- [options].

Uses Voxelgame's production-mesh gallery renderer; never opens a game window.
Export meshes with the sibling game's export_creature_gallery example first.
"""
import argparse
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game', type=Path, default=ROOT.parent / 'Voxelgame')
parser.add_argument('--input', type=Path, default=ROOT / '.cache/animal-refresh/meshes')
parser.add_argument('--output', type=Path, default=ROOT / '.cache/animal-refresh/renders')
parser.add_argument('--species', nargs='*', default=[])
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
spec = importlib.util.spec_from_file_location('creature_gallery', args.game / 'tools/render_creature_gallery.py')
gallery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gallery)
camera, floor = gallery.configure_scene(512, 16)
# The website supplies accessible captions outside each image.
gallery.add_label = lambda *args: None
original_frame = gallery.frame_camera

def frame_portrait(camera, corners, direction):
    """Frame and light each animal proportionally to its production bounds."""
    Vector = gallery.Vector
    minimum = Vector(tuple(min(c[i] for c in corners) for i in range(3)))
    maximum = Vector(tuple(max(c[i] for c in corners) for i in range(3)))
    center = (minimum + maximum) * 0.5
    # A world-sized rig leaves a whale outside the light pool. Scaling distance,
    # emitter size and power together preserves illumination across body sizes.
    scale = max(max(maximum - minimum) / 2.0, 0.001)
    for name, location, energy, size in [
        ('QA Key', (-4.5, -5.0, 8.0), 930.0, 5.0),
        ('QA Fill', (5.0, -1.5, 4.0), 520.0, 4.0),
        ('QA Rim', (0.5, 6.0, 6.0), 680.0, 3.5),
    ]:
        light = gallery.bpy.data.objects[name]
        light.location = center + Vector(location) * scale
        light.rotation_euler = (center - light.location).to_track_quat('-Z', 'Y').to_euler()
        light.data.energy = energy * scale * scale
        light.data.size = size * scale
    floor.location = (center.x, center.y, -0.025 * scale)
    floor.scale = (max(1.0, scale),) * 3
    if max(maximum - minimum) >= 0.12:
        original_frame(camera, corners, direction)
        return
    # The QA camera's fixed 1 cm upward bias can dwarf a millimetre-scale ant.
    center = (minimum + maximum) * 0.5
    camera.location = center + direction.normalized() * 4.0
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    gallery.bpy.context.view_layer.update()
    rotation = camera.matrix_world.to_quaternion()
    right, up = rotation @ Vector((1, 0, 0)), rotation @ Vector((0, 1, 0))
    horizontal = max(abs((c - center).dot(right)) for c in corners) * 2
    vertical = max(abs((c - center).dot(up)) for c in corners) * 2
    camera.data.ortho_scale = max(horizontal, vertical, 0.0001) / 0.78

gallery.frame_camera = frame_portrait
slugs = gallery.discover_species(args.input, args.species)
gallery.render_species(args.input, args.output, camera, slugs, 512)
print(f'Atlas: rendered {len(slugs)} animals, four views each.', flush=True)
