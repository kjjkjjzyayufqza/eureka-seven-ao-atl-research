"""Validate and save all asset scenes in isolated Blender 5.1 background shards."""

import argparse
import json
from pathlib import Path
import sys
import traceback

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import blender_verify


def main():
    if bpy.app.version[:2] != (5, 1):
        raise RuntimeError("Blender 5.1 is required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--repair", action="store_true", help="Only parameter sidecars and previous failed scenes")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    assets = json.loads((ROOT / "manifests/playable-assets.json").read_text())
    previous = {}
    for path in (ROOT / "manifests").glob("blender-shard-*.json"):
        previous.update({item["glb"]: item for item in json.loads(path.read_text())})
    jobs = [asset for index, asset in enumerate(assets) if index % args.shards == args.shard
            and (not args.repair or Path(str(ROOT / asset["glb"]) + ".parameters.json").is_file()
                 or previous.get(asset["glb"], {}).get("status") != "passed")]
    results = []
    for index, asset in enumerate(jobs):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        report_path = ROOT / "manifests/blender-scenes" / (asset["blend"] + ".json")
        parameters = [
            "blender_verify.py", "--", str(ROOT / asset["glb"]),
            "--blend", str(ROOT / asset["blend"]), "--report", str(report_path),
        ]
        if asset["kind"] == "auxiliary":
            parameters.append("--allow-no-mesh")
        if any(f"/Unit/{name}/{name}/" in asset["glb"] for name in ("enao", "enze", "ente")):
            parameters.extend(["--render", str(ROOT / "previews" / (Path(asset["blend"]).stem + "-blender51.png"))])
        result = {"glb": asset["glb"], "blend": asset["blend"]}
        try:
            sys.argv = parameters
            blender_verify.main()
            evidence = json.loads(report_path.read_text())
            if len(evidence["tracks"]) != asset["animation_count"]:
                raise RuntimeError(f"Animation count mismatch: {len(evidence['tracks'])} != {asset['animation_count']}")
            result.update({
                "status": "passed", "report": report_path.relative_to(ROOT).as_posix(),
                "clips": len(evidence["clips"]), "meshes": evidence["meshes"],
                "moving_clips": sum(clip["geometry_moves"] for clip in evidence["clips"]),
            })
        except Exception as error:
            result.update({"status": "failed", "error": str(error), "traceback": traceback.format_exc()})
            print("ASSET_FAILURE", json.dumps(result), flush=True)
        results.append(result)
        previous[result["glb"]] = result
        shard_results = [previous[asset["glb"]] for index, asset in enumerate(assets)
                         if index % args.shards == args.shard and asset["glb"] in previous]
        (ROOT / f"manifests/blender-shard-{args.shard}.json").write_text(json.dumps(shard_results, indent=2))
        print(f"SHARD_PROGRESS {args.shard}: {index + 1}/{len(jobs)}", flush=True)
    print("SHARD_COMPLETE", args.shard, len(results), sum(item["status"] == "failed" for item in results), flush=True)


if __name__ == "__main__":
    main()
