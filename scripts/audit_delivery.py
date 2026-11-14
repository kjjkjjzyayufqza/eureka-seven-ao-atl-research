"""Final semantic delivery audit, run once inside Blender 5.1.

Checks provenance, every saved scene, packed texture bytes, NLA clip coverage,
and reloaded native parameter playback against source keys.
"""

from collections import Counter, defaultdict
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from blender_verify import select_clip
from glb_tools import read_glb
from vendor_integrity import verify_dependencies


def read(name):
    return json.loads((ROOT / "manifests" / name).read_text(encoding="utf-8"))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    if bpy.app.version[:2] != (5, 1):
        raise RuntimeError("Final audit requires Blender 5.1")
    archives = read("archives.json")
    entries = [entry for archive in archives for entry in archive["entries"]]
    for entry in entries:
        path = ROOT / entry["output"]
        if path.stat().st_size != entry["size"] or sha256(path) != entry["sha256"]:
            raise ValueError("Extracted entry changed: " + entry["output"])
    source = Path(archives[0]["source"])
    if sha256(source) != archives[0]["source_sha256"]:
        raise ValueError("Original source archive changed")
    conversions = read("conversion.json")
    if any(item["status"] != "converted" for item in conversions):
        raise ValueError("Unconverted source scene")
    assets = read("playable-assets.json")
    shard_results = [item for index in range(3) for item in read(f"blender-shard-{index}.json")]
    if {item["glb"] for item in shard_results} != {item["glb"] for item in assets}:
        raise ValueError("Incomplete Blender shard coverage")
    if any(item["status"] != "passed" for item in shard_results):
        raise ValueError("A Blender scene failed")
    reports = [json.loads((ROOT / item["report"]).read_text()) for item in shard_results]
    if any(not item["blender"].startswith("5.1.") for item in reports):
        raise ValueError("Non-5.1 playback evidence")
    native = read("native-parameters.json")
    extra_by_source = Counter()
    for item in native["assets"]:
        data = json.loads((ROOT / item["sidecar"]).read_text())
        for clip in data["clips"]:
            extra_by_source[clip["source"]] += len(clip["channels"])
    audit = read("channel-audit.json")
    for item in audit:
        if item["source_channels"] != item["gltf_channels"] + extra_by_source[item["source"]]:
            raise ValueError("Unaccounted native channels: " + item["source"])
    textures = read("textures.json")
    if any(item["status"] != "decoded" for item in textures):
        raise ValueError("Undecoded texture")
    packed_images = 0
    native_samples = 0
    native_max_error = 0.0
    final_scenes = []
    for index, asset in enumerate(assets):
        path = ROOT / asset["blend"]
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        tracks = {track.name for obj in scene.objects if obj.animation_data for track in obj.animation_data.nla_tracks}
        if len(tracks) != asset["animation_count"]:
            raise ValueError("Reloaded clip count mismatch: " + asset["blend"])
        image_count = 0
        for image in bpy.data.images:
            if image.source != "FILE":
                continue
            expected = (ROOT / asset["glb"]).parent / Path(image.filepath).name
            if image.packed_file is None or hashlib.sha256(bytes(image.packed_file.data)).hexdigest() != sha256(expected):
                raise ValueError(f"Stale/missing packed texture: {asset['blend']}, {image.name}")
            image_count += 1
        packed_images += image_count
        sidecar = ROOT / (asset["glb"] + ".parameters.json")
        if sidecar.is_file():
            data = json.loads(sidecar.read_text())
            if json.loads(bpy.data.texts["Native_Parameters.json"].as_string()) != data:
                raise ValueError("Embedded native parameters differ")
            owners = [obj for obj in scene.objects if "native_source" in obj]
            for clip in data["clips"]:
                select_clip(clip["name"])
                for channel in clip["channels"]:
                    name = "NativeParameters::" + (channel["target_name"] or str(channel["target_location"]))
                    candidates = [obj for obj in owners if obj["native_source"] == clip["source"] and obj.name == name]
                    if len(candidates) != 1:
                        raise ValueError("Ambiguous native parameter target: " + name)
                    owner = candidates[0]
                    points = list(zip(channel["times_seconds"], channel["values"]))
                    for sample in sorted({0, len(points) // 2, len(points) - 1}):
                        time, expected = points[sample]
                        frame = time * scene.render.fps
                        scene.frame_set(math.floor(frame), subframe=frame % 1)
                        value = owner[channel["property"]]
                        actual = [value] if len(expected) == 1 else list(value)
                        error = max(abs(a - b) for a, b in zip(actual, expected))
                        if not math.isfinite(error) or error > 0.002:
                            raise ValueError(f"Reloaded NLA native curve mismatch: {asset['blend']}, {clip['name']}, {channel['property']}: {error}")
                        native_max_error = max(native_max_error, error)
                        native_samples += 1
        final_scenes.append({"blend": asset["blend"], "clips": len(tracks), "packed_images": image_count, "status": "passed"})
        if index % 100 == 0:
            print("DELIVERY_AUDIT_PROGRESS", index + 1, len(assets), flush=True)
    revision = verify_dependencies()["ed8pkg2glb"]
    if revision != "c076d638e3f978afe2bb4de0a6f911f03b2afdfd":
        raise ValueError("Pinned upstream source differs")
    summary = {
        "status": "passed", "blender": bpy.app.version_string, "blender_build_hash": bpy.app.build_hash.decode(),
        "source": str(source), "source_sha256": archives[0]["source_sha256"], "source_hash_unchanged": True,
        "archives": len(archives), "extracted_entries_hash_verified": len(entries),
        "converted_clusters": len(conversions), "model_scenes": sum(item["kind"] == "model" for item in assets),
        "auxiliary_scenes": sum(item["kind"] == "auxiliary" for item in assets),
        "saved_scenes_reopened": len(final_scenes), "clips": sum(item["animation_count"] for item in assets),
        "clips_with_sampled_mesh_movement": sum(item["moving_clips"] for item in shard_results),
        "source_channels": sum(item["source_channels"] for item in audit),
        "gltf_trs_channels": sum(item["gltf_channels"] for item in audit),
        "native_parameter_channels": sum(extra_by_source.values()),
        "native_parameters_checked_after_reload": native_samples, "max_reloaded_native_key_error": native_max_error,
        "decoded_2d_textures": len(textures), "packed_images_hash_verified": packed_images,
        "upstream_revision": revision, "upstream_unmodified": True,
        "git": subprocess.check_output(["git", "--version"], text=True).strip(),
        "local_script_sha256": {path.name: sha256(path) for path in sorted((ROOT / "scripts").glob("*.py"))},
        "scenes": final_scenes,
    }
    (ROOT / "manifests/delivery-audit.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("DELIVERY_AUDIT_PASSED", json.dumps({key: value for key, value in summary.items() if key not in ("scenes", "local_script_sha256")}), flush=True)


if __name__ == "__main__":
    main()
