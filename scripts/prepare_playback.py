"""Create one self-contained model+clip GLB for every converted model scene."""

from collections import defaultdict
import json
from pathlib import Path

from convert_phyre import ROOT
from glb_tools import merge_animations, read_glb, write_glb


def main():
    records = json.loads((ROOT / "manifests/conversion.json").read_text(encoding="utf-8"))
    groups = defaultdict(list)
    channel_audit = []
    for record in records:
        if record["status"] != "converted":
            raise RuntimeError(f"Unconverted input: {record['source']}")
        groups[str(Path(record["output"]).parent)].append(record)
        document, _ = read_glb(ROOT / record["output"])
        expected = sum(record["classes"].get(name, 0) for name in ("PAnimationChannel", "PAnimationConstantChannel"))
        exported = sum(len(animation["channels"]) for animation in document.get("animations", []))
        channel_audit.append({"source": record["source"], "source_channels": expected, "gltf_channels": exported})
    assets = []
    for directory, items in sorted(groups.items()):
        models = [item for item in items if item.get("meshes", 0)]
        if len(models) > 1:
            raise RuntimeError(f"Ambiguous multi-model group: {directory}")
        clips = [ROOT / item["output"] for item in items if item.get("animations", 0) and not item.get("meshes", 0)]
        relative_directory = Path(directory).relative_to("converted/assets")
        if models:
            model = models[0]
            source = ROOT / model["output"]
            output = ROOT / "playable/glb" / relative_directory / (source.stem + "_all_animations.glb")
            merges = merge_animations(source, clips, output)
            document, binary = read_glb(output)
            for index, animation in enumerate(document.get("animations", [])):
                animation.setdefault("name", f"{source.stem}_{index}")
            write_glb(output, document, binary)
            assets.append({
                "kind": "model", "source": model["source"],
                "glb": output.relative_to(ROOT).as_posix(),
                "blend": (Path("playable/blend") / relative_directory / (source.stem + ".blend")).as_posix(),
                "animation_count": len(document.get("animations", [])),
                "mesh_count": len(document.get("meshes", [])),
                "joint_count": sum(len(skin["joints"]) for skin in document.get("skins", [])),
                "vertices": model["vertices"],
                "primitives": model["primitives"],
                "merge_details": merges,
            })
        else:
            for item in items:
                source = ROOT / item["output"]
                output = ROOT / "playable/auxiliary" / relative_directory / source.name
                document, binary = read_glb(source)
                for index, animation in enumerate(document.get("animations", [])):
                    animation.setdefault("name", source.stem + (f"_{index}" if index else ""))
                # Animation-only outputs have no material-bearing geometry. Keep transforms
                # and clips while removing irrelevant texture imports and dummy skins.
                for key in ("materials", "textures", "images", "samplers", "skins"):
                    document.pop(key, None)
                for node in document.get("nodes", []):
                    node.pop("skin", None)
                write_glb(output, document, binary)
                assets.append({
                    "kind": "auxiliary", "source": item["source"],
                    "glb": output.relative_to(ROOT).as_posix(),
                    "blend": (Path("playable/blend-auxiliary") / relative_directory / (source.stem + ".blend")).as_posix(),
                    "animation_count": len(document.get("animations", [])),
                    "mesh_count": 0, "joint_count": 0, "vertices": 0, "primitives": 0,
                    "merge_details": [],
                })
        if models:
            # Resolve the model GLB's existing PNG URIs relative to its new directory.
            import shutil
            for image in document.get("images", []):
                if "uri" in image and not image["uri"].startswith("data:"):
                    image_source = ROOT / directory / image["uri"]
                    image_destination = output.parent / image["uri"]
                    image_destination.parent.mkdir(parents=True, exist_ok=True)
                    if not image_source.is_file():
                        raise FileNotFoundError(image_source)
                    shutil.copyfile(image_source, image_destination)
    (ROOT / "manifests/playable-assets.json").write_text(json.dumps(assets, indent=2), encoding="utf-8")
    (ROOT / "manifests/channel-audit.json").write_text(json.dumps(channel_audit, indent=2), encoding="utf-8")
    mismatches = [item for item in channel_audit if item["source_channels"] != item["gltf_channels"]]
    print(json.dumps({
        "model_assets": sum(item["kind"] == "model" for item in assets),
        "auxiliary_assets": sum(item["kind"] == "auxiliary" for item in assets),
        "animations": sum(item["animation_count"] for item in assets),
        "channel_count_mismatches": len(mismatches),
        "mismatch_examples": mismatches[:10],
    }, indent=2))


if __name__ == "__main__":
    main()
