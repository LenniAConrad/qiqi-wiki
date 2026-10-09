#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Capture Jade Willow through the disposable production game renderer.

No player saves or visible windows are opened. Preserve native PNGs, replay
evidence and the exact executable in .cache; publish complete-frame WebPs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SEED = "1786640127379949800"
PACK = "chinese_village:pack"

# Feet coordinates in the inspection village, anchored at (0,15.5,0).
VIEWS = [
    ("overview", "Along the crooked lanes", "Staggered homes, branching lanes and small garden courts form an open settlement around the central square.", "Village", [-43, 61, -40], [46, -34], 0.38),
    ("courtyard", "A sheltered courtyard", "White plaster fire walls frame a two-wing household, a tiled veranda and a flowering tree.", "Homes", [-11, 21, 4], [-42, -8], 0.38),
    ("tea-gallery", "The tea-house gallery", "A timber street gallery and an external stair connect the two floors of the tea house.", "Homes", [6, 21, 8], [38, -5], 0.38),
    ("cottage-lane", "At the cottage door", "Paper lattice windows, brick plinths and timber thresholds open onto a narrow paved lane.", "Homes", [-31, 16.6, 5.8], [-19, 0], 0.38),
    ("pond-bridge", "Across the lotus pond", "A stepped stone footbridge crosses the curved basin beside willows, bamboo and the irrigation channel.", "Water", [25, 18, 18], [35, -5], 0.43),
    ("water-quarter", "The waterside quarter", "The pond and planted edges interrupt the village outline; gardens and working yards sit between the houses.", "Water", [54, 76, 54], [-135, -42], 0.40),
    ("tea-interior", "Inside the tea room", "Low tea tables and stools furnish the upper room beside timber-framed paper screens.", "Homes", [16, 20.5, 21], [90, -8], 0.43),
    ("granary", "Steps to the granary", "Half-metre timber steps and side rails lead into the raised grain store.", "Village", [31.5, 17, -15], [180, 4], 0.38),
    ("lantern-court", "When the lanterns glow", "Warm hanging lanterns light the well square and the three-tier pavilion as the sky turns to evening.", "Evening", [-10, 18, -3], [72, 5], 0.76),
]

# Walking-height views audit every authored building after individual review.
VIEWS.extend([
    ("courtyard-house", "The courtyard house", "Two plaster wings frame a sheltered household court, with timber trim and a flowering tree.", "Homes", [-19, 16.3, 0], [0, -3], 0.38),
    ("tea-house", "The tea house", "A two-storey tea room opens onto its timber gallery and the lane below.", "Homes", [15, 16.5, 6], [0, -5], 0.38),
    ("elder-residence", "The elder residence", "Unequal house wings and a covered porch make a sheltered entrance for the village elder.", "Homes", [-4, 17.5, 19], [0, -4], 0.38),
    ("weaver-house", "The weaver's house", "A compact plaster home shares its work court with a timber loom and hanging cloth.", "Homes", [-22, 16.5, 0], [180, -7], 0.38),
    ("herbalist-cottage", "The herbalist's cottage", "A low gabled cottage keeps herb planters and a small drying shed beside the door.", "Homes", [-11, 16.5, -6], [180, -7], 0.38),
    ("lane-gable", "Lane house · gabled", "A stepped plaster gable and brick threshold mark one of the village's smaller homes.", "Homes", [-28, 16.3, 6], [-90, -4], 0.38),
    ("lane-tall-east", "Lane house · tall east", "The taller east-lane house keeps a narrow doorway beneath layered blue roof tiles.", "Homes", [-27, 18, 15], [-90, -5], 0.38),
    ("lane-hearth-east", "Lane house · east hearth", "A home hearth opens onto the east lane beside planted stone troughs.", "Homes", [-28, 16.5, 24], [-90, -5], 0.38),
    ("lane-awning-north", "Lane house · north awning", "A timber awning shades the north approach while leaving the passage open.", "Homes", [-36, 16.3, 42], [180, -5], 0.38),
    ("lane-tall-west", "Lane house · tall west", "A narrow west-lane frontage rises behind a half-metre tiled eave.", "Homes", [-36, 18, 29], [90, -5], 0.38),
    ("lane-awning-east", "Lane house · east awning", "The east awning shelters a tight turn where two crooked lanes meet.", "Homes", [-27, 16.3, -10], [-90, -5], 0.38),
    ("lane-hearth-west", "Lane house · west hearth", "A plaster hearth wall and raised brick base face the western lane.", "Homes", [-34, 16.5, -27], [54, -3], 0.38),
    ("lane-tall-south", "Lane house · tall south", "A tall southern façade balances a narrow doorway with a broad tiled roof.", "Homes", [0, 18, -37], [0, -5], 0.38),
    ("lane-awning-south", "Lane house · south awning", "Timber side posts hold a low awning over the southern lane entrance.", "Homes", [10, 16.3, -35], [0, -5], 0.38),
    ("lane-hearth-west2", "Lane house · west hearth II", "A second hearth-front cottage shows the varied roof and porch rhythm along the lanes.", "Homes", [21, 16.5, -11], [90, -5], 0.38),
    ("kiln-yard", "The kiln workyard", "The brick kiln and covered work bay sit behind an open yard for making and firing pots.", "Workyards", [-35, 16.5, -13], [180, -5], 0.38),
    ("raised-granary", "The raised granary", "A raised store keeps grain above ground level behind a sheltered loading entrance.", "Workyards", [31.5, 19, -31], [180, -4], 0.38),
    ("livestock-shelter", "The livestock shelter", "An open timber shelter stands inside the village paddock beside its red gate rails.", "Workyards", [37.5, 16.5, 20], [180, -5], 0.38),
    ("market-cloth", "Cloth stall", "A shaded market counter displays folded cloth beneath a tiled canopy.", "Market", [14, 16.3, 2], [180, -4], 0.38),
    ("market-produce", "Produce stall", "Fresh greens and baskets fill a small produce counter along the central market lane.", "Market", [19, 16.3, 2], [180, -4], 0.38),
    ("market-pottery", "Pottery stall", "Clay vessels and a low counter give the pottery stall its own market frontage.", "Market", [24, 16.3, 2], [180, -4], 0.38),
    ("market-tea", "Tea stall", "A compact tea counter faces the market's meeting of stone-paved paths.", "Market", [27, 16.3, 2], [180, -4], 0.38),
    ("village-well", "The covered village well", "A timber well canopy and shared seating anchor the paved village square.", "Civic", [0, 17.3, -8], [0, -8], 0.38),
    ("pagoda", "The three-tier pagoda", "Three compact tiled roofs rise above the domestic houses as a village landmark.", "Civic", [0, 22, 0], [0, 11], 0.38),
    ("ancestral-pavilion", "The ancestral pavilion", "An open timber pavilion shelters a modest altar and seats beside the square.", "Civic", [8, 16.5, -16], [90, -4], 0.38),
    ("opera-stage", "The opera stage", "An open-front timber stage faces the square beneath a broad hipped roof.", "Civic", [6, 16.5, 7], [90, -4], 0.38),
    ("moon-gate", "The moon gate", "A rounded stone opening joins the lane to the gardens without enclosing another square.", "Civic", [23, 16.5, 1], [90, -3], 0.38),
    ("entrance-gate", "The entrance gate", "Lacquer-red timber frames the village entrance and the planted path beyond.", "Civic", [-57, 16.3, 0], [90, -2], 0.38),
])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def warm(game):
    frames = 0
    for _ in range(28):
        state = game.call("step", {"frames": 120, "render": True})
        frames += 120
        renderer = state["renderer"]
        if (frames >= 480 and renderer["detail_clip_radius_metres"] >= 40
                and renderer["detail_clip_radius_metres"] + 0.01 >= renderer["detail_clip_target_metres"]):
            return state, frames
    raise RuntimeError(f"Detailed scenery did not finish loading: {renderer}")


def store_capture(game, shot, evidence, frames):
    game.call("configure", {"time": shot["time"]})
    result = game.call("capture_frame", {"name": shot["id"] + ".png"})
    state = result["state"]
    assert state["save_writes"] is False and state["world"]["edited_voxels"] == 0
    assert state["generator_version"] == 9
    assert not state["player"]["crawling"], "A photograph's camera clipped a building"
    source = Path(result["path"])
    output = ROOT / "images/villages" / (shot["id"] + ".webp")
    with Image.open(source) as image:
        assert image.size == (960, 540)
        image.save(output, "WEBP", quality=94, method=6)
    shot.update({
        "image": str(output.relative_to(ROOT)), "width": 960, "height": 540,
        "imageSha256": digest(output), "originalImageSha256": digest(source),
        "originalPng": str(source.relative_to(ROOT)),
        "camera": {"positionMetres": state["player"]["position_metres"],
                   "lookDegrees": state["player"]["look_degrees"]},
        "warmupFrames": frames, "renderer": state["renderer"],
        "evidence": str(evidence.relative_to(ROOT)),
    })
    print(f"Captured {shot['id']} ({output.stat().st_size // 1024} KiB)", flush=True)
    return shot


def resident_camera(game, resident):
    x, y, z = resident["position_metres"]
    yaw = resident["yaw_radians"]
    for turn in [0.0, 0.5, -0.5, 1.0, -1.0, math.pi]:
        angle = yaw + turn
        camera = [x + math.sin(angle) * 4.2, y + 0.15, z + math.cos(angle) * 4.2]
        minimum = [math.floor((camera[0] - 0.35) * 2), math.floor((camera[1] + 0.05) * 2), math.floor((camera[2] - 0.35) * 2)]
        region = game.call("inspect_region", {"minimum": minimum, "size": [3, 4, 3]})
        if any(cell["solid"] for cell in region["blocks"]):
            continue
        dx, dz = x - camera[0], z - camera[2]
        return camera, [math.degrees(math.atan2(dx, dz)), math.degrees(math.atan2(y + 1.0 - camera[1] - 1.62, math.hypot(dx, dz)))]
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=ROOT.parent / "Voxelgame")
    parser.add_argument("--binary", type=Path, default=ROOT.parent / "Voxelgame/.cache/jade-review/voxelgame-polish-final")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    capture_root = ROOT / ".cache" / ("village-captures-" + stamp)
    capture_root.mkdir(parents=True)
    (ROOT / "images/villages").mkdir(parents=True, exist_ok=True)
    binary = capture_root / "voxelgame"
    shutil.copy2(args.binary.resolve(), binary)
    sys.path.insert(0, str(args.game.resolve() / "tools"))
    from game_debug import DebugGame

    shots = []
    evidence = capture_root / "inspection"
    game = DebugGame(binary, evidence, 180)
    try:
        game.call("reset", {"scene": "inspection", "seed": SEED, "generator": "current", "mods": [PACK]})
        asset = game.call("inspect_asset", {"id": "chinese_village:structure/village"})
        placed = game.call("spawn_asset", {"id": "chinese_village:structure/village", "position": [0, 0, 0]})
        game.call("frame_subject", {"subject": placed["subject"], "azimuth": 225, "elevation": 32, "distance": 70})
        for identifier, title, description, category, camera, look, time in VIEWS:
            game.call("configure", {"position": camera, "look": look, "flying": True, "mode": "creative", "time": time, "weather": "clear", "shader": "fast", "view_distance": 32})
            _, frames = warm(game)
            shots.append(store_capture(game, {"id": identifier, "title": title, "description": description, "category": category, "scene": "inspection", "time": time, "anchorMetres": [0, 15.5, 0]}, evidence, frames))
    finally:
        game.close()

    evidence = capture_root / "generated"
    game = DebugGame(binary, evidence, 180)
    try:
        game.call("reset", {"seed": SEED, "generator": "current", "mods": [PACK]})
        game.call("configure", {"position": [-4, 79, 338], "look": [45, -30], "flying": True, "time": 0.38, "weather": "clear", "shader": "fast", "view_distance": 32})
        game.call("step", {"frames": 1, "keys": ["F1"]})
        _, frames = warm(game)
        shots.insert(0, store_capture(game, {"id": "generated-village", "title": "A village in the autumn woods", "description": "The nearest naturally placed Jade Willow village on the reference seed, surrounded by autumn woodland. Visit X 36, Z 380 with the pack enabled.", "category": "Village", "scene": "generated", "time": 0.38, "anchorMetres": [36, 37.5, 380]}, evidence, frames))
        game.call("configure", {"position": [38.5, 39, 374], "look": [0, 0], "flying": True, "time": 0.43})
        state, frames = warm(game)
        residents = sorted(state["mobile_entities"], key=lambda entity: (entity["position_metres"][0] - 36) ** 2 + (entity["position_metres"][2] - 380) ** 2)
        for resident in residents[:6]:
            view = resident_camera(game, resident)
            if view is None:
                continue
            camera, look = view
            game.call("configure", {"position": camera, "look": look, "flying": True})
            game.call("render", {"frames": 30})
            shots.append(store_capture(game, {"id": "residents", "title": "Meet the village residents", "description": "One of twelve original resident designs in the living village. Each generated settlement receives a different seeded group of six neutral wandering residents.", "category": "Residents", "scene": "generated", "time": 0.43, "anchorMetres": [36, 37.5, 380]}, evidence, frames))
            break
        else:
            raise RuntimeError("No unobstructed resident portrait position")
    finally:
        game.close()

    data = {
        "title": "Jade Willow Village", "packId": PACK, "packVersion": "1.4.0",
        "capturedAt": datetime.now(timezone.utc).isoformat(), "seed": SEED,
        "generatorVersion": 9,
        "description": "Whitewashed homes, crooked lanes and waterside gardens in an original southern-Chinese-inspired village pack.",
        "provenance": {"binarySha256": digest(binary), "captureToolSha256": digest(Path(__file__)), "binary": str(binary.relative_to(ROOT)), "renderer": "Voxelgame production offscreen renderer", "encoding": {"format": "WebP", "quality": 94, "method": 6}, "sourceNote": "Captured from the reviewed Jade Willow 1.4 devtools executable. The binary and full native replay evidence are frozen in the local cache; unrelated source edits after its build are not attributed to these pictures."},
        "structure": asset, "shots": shots,
    }
    (ROOT / "data/villages.json").write_text(json.dumps(data, indent=2) + "\n")
    (ROOT / "data/villages.js").write_text("// SPDX-License-Identifier: GPL-3.0-only\nwindow.VILLAGE_GALLERY = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"Published {len(shots)} screenshots; evidence {capture_root}", flush=True)


if __name__ == "__main__":
    main()
