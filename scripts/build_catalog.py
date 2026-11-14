"""Document exported unit clips and original key timing without resampling."""

from collections import Counter
import json
from pathlib import Path
import statistics
import struct

from convert_phyre import ROOT
from glb_tools import read_glb


def timestamps(document, binary, index):
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    if accessor["componentType"] != 5126 or accessor["type"] != "SCALAR":
        raise ValueError("Animation time accessor must be float32 SCALAR")
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    return struct.unpack_from("<" + "f" * accessor["count"], binary, offset)


def main():
    assets = json.loads((ROOT / "manifests/playable-assets.json").read_text())
    catalog = []
    for asset in assets:
        if asset["kind"] != "model" or "/Unit/" not in asset["glb"]:
            continue
        document, binary = read_glb(ROOT / asset["glb"])
        clips = []
        for animation in document.get("animations", []):
            times = []
            gaps = []
            seen = set()
            for sampler in animation["samplers"]:
                index = sampler["input"]
                if index in seen:
                    continue
                seen.add(index)
                values = timestamps(document, binary, index)
                times.extend(values)
                if len(values) > 2:
                    gaps.extend(right - left for left, right in zip(values, values[1:]) if right - left > 1e-6)
            clips.append({
                "name": animation["name"], "channels": len(animation["channels"]),
                "start_seconds": min(times) if times else None,
                "end_seconds": max(times) if times else None,
                "duration_seconds": max(times) - min(times) if times else None,
                "median_variable_key_gap_seconds": statistics.median(gaps) if gaps else None,
                "common_variable_key_gaps_seconds": Counter(round(gap, 5) for gap in gaps).most_common(4),
            })
        catalog.append({**asset, "resource_code": Path(asset["glb"]).parts[3], "clips": clips})
    (ROOT / "manifests/unit-animation-catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    lines = [
        "# Unit Models and Animation Inventory", "",
        "Counts below come from the exported source data. Resource codes are stable identifiers; they are not all verified official character/form names. No comparison with ACE3 or another game's polygon counts has been performed in this extraction task.", "",
        "Vertices are summed across glTF material primitives and can include duplicated boundary vertices. Primitives are material/geometry segments, not separately named Blender Mesh objects. Animation counts include loops, reactions, transitions and duplicate resources; they do not directly measure the number of unique attacks.", "",
        "| Resource code | Vertices | Primitives | Skin joints | Clips | Local generated Blender file |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in catalog:
        lines.append(f"| `{item['resource_code']}` | {item['vertices']:,} | {item['primitives']} | {item['joint_count']} | {item['animation_count']} | `{item['blend']}` |")
    lines.extend(["", "These paths describe local generated outputs. The repository does not include Blender files or other game assets.", "", "## Nirvash resources", "", "`enao` is the AO Nirvash mesh observed in the Blender preview. `ena2` has the same exported geometry counts but remains separately exported; do not rename it to 'spec2' based only on its code. `enze` and `enza` are the related ZERO resources, and `ente` is the theEND resource. Official variant labels for `ena2` and `enza` remain unconfirmed.", "", "The AO `enao` mesh has 12,497 exported triangles. It has 21 primitives in one glTF mesh and 90 skin joints. Blender may split the glTF primitives into multiple Mesh objects; neither that count nor primitive-summed vertices should be compared to a welded topology count without normalization.", "", "## AO Nirvash clip timing", "", "Source times are preserved in seconds. Key gaps describe the authored curve, not the rendered game frame rate. No motion smoothing or resampling was applied. The complete per-unit and per-clip timing data are in `manifests/unit-animation-catalog.json`.", "", "| Clip | Duration, seconds | TRS channels | Median variable-key gap, seconds |", "| --- | ---: | ---: | ---: |"])
    enao = next(item for item in catalog if item["resource_code"] == "enao")
    for clip in enao["clips"]:
        duration = f"{clip['duration_seconds']:.6f}" if clip['duration_seconds'] is not None else "—"
        gap = f"{clip['median_variable_key_gap_seconds']:.6f}" if clip['median_variable_key_gap_seconds'] is not None else "constant / none"
        lines.append(f"| `{clip['name']}` | {duration} | {clip['channels']} | {gap} |")
    lines.extend(["", "## Playback and naming limits", "", "The filename prefixes suggest attack (`ATK`), movement (`MOV`), dash (`DSH`), damage/reaction (`DM`) and special (`SPF`) groups, but these are filename interpretations rather than a decoded command/state system. Short fragments may need game-side sequencing to reproduce a complete move. Animation-only camera packs are retained under `playable/blend-auxiliary/`. All remaining model scenes, including maps and 2D UI geometry, are indexed in `manifests/playable-assets.json`.", ""])
    (ROOT / "docs/unit-models-and-animations.md").write_text("\n".join(lines), encoding="utf-8")
    print("CATALOG", len(catalog), sum(len(item["clips"]) for item in catalog))


if __name__ == "__main__":
    main()
