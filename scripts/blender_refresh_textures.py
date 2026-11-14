"""Reload corrected PNGs into existing Blender 5.1 scenes, preserving actions."""

import argparse
import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]


def main():
    if bpy.app.version[:2] != (5, 1):
        raise RuntimeError("Blender 5.1 is required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--unit")
    parser.add_argument("--rsx-only", action="store_true")
    parser.add_argument("--format")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    assets = json.loads((ROOT / "manifests/playable-assets.json").read_text())
    jobs = [asset for index, asset in enumerate(assets) if index % args.shards == args.shard and asset["kind"] == "model"]
    if args.unit:
        jobs = [asset for asset in jobs if f"/Unit/{args.unit}/{args.unit}/" in asset["glb"]]
    if args.rsx_only or args.format:
        textures = json.loads((ROOT / "manifests/textures.json").read_text())
        folders = {Path(item["output"]).relative_to("converted/assets").parent.as_posix() for item in textures
                   if (item["format"] == args.format if args.format else item["format"] in ("ARGB8", "ARGB1555", "RGB565") and not item["linear"])}
        jobs = [asset for asset in jobs if Path(asset["glb"]).relative_to("playable/glb").parent.as_posix() in folders]
    suffix = "-" + args.unit if args.unit else ""
    report_path = ROOT / f"manifests/texture-pack-shard-{args.shard}{suffix}.json"
    results = {item["blend"]: item for item in json.loads(report_path.read_text())} if report_path.exists() else {}
    for index, asset in enumerate(jobs):
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / asset["blend"]))
        refreshed = []
        for image in bpy.data.images:
            if image.source != "FILE":
                continue
            path = (ROOT / asset["glb"]).parent / Path(image.filepath).name
            if not path.is_file():
                raise FileNotFoundError(path)
            # Free the old packed pixels before loading the corrected source.
            if image.packed_file:
                image.unpack(method="REMOVE")
            image.filepath = str(path)
            image.reload()
            image.pack()
            refreshed.append(str(path.relative_to(ROOT)))
        if any(f"/Unit/{name}/{name}/" in asset["glb"] for name in ("enao", "enze", "ente")):
            bpy.context.scene.render.filepath = str(ROOT / "previews" / (Path(asset["blend"]).stem + "-blender51.png"))
            bpy.ops.render.render(write_still=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / asset["blend"]))
        results[asset["blend"]] = {"blend": asset["blend"], "blender": bpy.app.version_string, "images": refreshed, "status": "passed"}
        print("PACK_PROGRESS", args.shard, index + 1, len(jobs), flush=True)
        report_path.write_text(json.dumps(list(results.values()), indent=2))


if __name__ == "__main__":
    main()
