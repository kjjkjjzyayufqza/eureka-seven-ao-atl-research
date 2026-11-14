"""Correct only saved native-parameter NLA strips with rounded start bounds."""

import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]


def main():
    if bpy.app.version[:2] != (5, 1):
        raise RuntimeError("Blender 5.1 is required")
    assets = json.loads((ROOT / "manifests/playable-assets.json").read_text())
    changes = []
    checked = 0
    for asset in assets:
        if not (ROOT / (asset["glb"] + ".parameters.json")).is_file():
            continue
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / asset["blend"]))
        repairs = []
        for owner in bpy.context.scene.objects:
            if "native_source" not in owner or not owner.animation_data:
                continue
            for track in owner.animation_data.nla_tracks:
                for strip in track.strips:
                    checked += 1
                    start, end = map(float, strip.action.frame_range)
                    if abs(strip.frame_start - start) < 1e-6 and abs(strip.frame_end - end) < 1e-6:
                        continue
                    repairs.append({"object": owner.name, "track": track.name, "previous": [strip.frame_start, strip.frame_end], "corrected": [start, end]})
                    strip.frame_start = start
                    strip.frame_end = end
                    strip.scale = 1.0
        if repairs:
            bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / asset["blend"]))
            changes.append({"blend": asset["blend"], "repairs": repairs})
    report = {"blender": bpy.app.version_string, "checked_strips": checked, "changed_scenes": len(changes), "changes": changes}
    (ROOT / "manifests/native-nla-timing-repair.json").write_text(json.dumps(report, indent=2))
    print("NATIVE_NLA_TIMING_REPAIRED", checked, len(changes), flush=True)


if __name__ == "__main__":
    main()
