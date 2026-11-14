"""Preserve non-TRS animation through Julian Uy's existing Phyre schema parser."""

from collections import Counter, defaultdict
import json
from pathlib import Path

from convert_phyre import ROOT, LooseClusterMedia, phyre
from glb_tools import read_glb


def main():
    # No mesh/texture export is required for this supplemental pass.
    phyre.render_mesh = lambda *args: None
    phyre.cluster_classes_to_handle.extend(["PCameraPerspective", "PCamera", "PCameraBase"])
    records = json.loads((ROOT / "manifests/conversion.json").read_text())
    audit = json.loads((ROOT / "manifests/channel-audit.json").read_text())
    affected = {item["source"] for item in audit if item["source_channels"] != item["gltf_channels"]}
    groups = defaultdict(list)
    for record in records:
        groups[str(Path(record["output"]).parent)].append(record)
    assets = json.loads((ROOT / "manifests/playable-assets.json").read_text())
    by_source = {record["source"]: record for record in records}
    extracted = {}
    counts = Counter()
    for index, source_name in enumerate(sorted(affected)):
        source = ROOT / source_name
        media = LooseClusterMedia(source.parent, ROOT / "converted/parameter-probe")
        parsed = phyre.parse_cluster(media.logical_name(source.name), None, media)
        clips = []
        for clip_index, clip in enumerate(parsed.data_instances_by_class.get("PAnimationClip", [])):
            channels = []
            for constant, channel_list in ((False, clip["m_channels"]["m_els"]), (True, clip["m_constantChannels"]["m_els"])):
                for channel in channel_list:
                    kind = channel["m_keyType"]
                    if kind in ("Translation", "Rotation", "Scale"):
                        continue
                    dimensions = 4 if kind.endswith("F4") else 1
                    if constant:
                        values = list(memoryview(bytes(channel["m_value"])).cast("f"))[:dimensions]
                        times = [clip["m_constantChannelStartTime"], clip["m_constantChannelEndTime"]]
                        values = [values, values]
                    else:
                        count = channel["m_keyCount"]
                        times = list(channel["m_times"]["m_timeKeys"]["m_els"][:count])
                        raw = list(channel["m_valueKeys"]["m_els"][:count * dimensions])
                        values = [raw[i:i + dimensions] for i in range(0, len(raw), dimensions)]
                    if len(values) != len(times) or any(len(v) != dimensions for v in values):
                        raise ValueError(f"Invalid native curve dimensions: {source_name}, {kind}")
                    target = channel.get("m_instanceObject") or {}
                    camera = {key: target[key] for key in ("m_FOV", "m_aspect", "m_nearPlane", "m_farPlane") if key in target}
                    channels.append({
                        "key_type": kind, "property": channel["m_name"]["m_buffer"],
                        "target_class": channel["m_instanceObjectType"], "target_name": target.get("mu_name"),
                        "target_location": target.get("mu_memberLoc"), "constant": constant,
                        "interpolation_code": channel["m_interp"], "times_seconds": times,
                        "values": values, "camera": camera,
                    })
                    counts[kind] += 1
            clips.append({"clip_index": clip_index, "native_name": clip["m_name"]["m_buffer"], "channels": channels})
        extracted[source_name] = clips
        if index % 50 == 0:
            print("PARAMETER_PROGRESS", index + 1, len(affected), flush=True)
    outputs = []
    for asset in assets:
        record = by_source[asset["source"]]
        items = groups[str(Path(record["output"]).parent)] if asset["kind"] == "model" else [record]
        document, _ = read_glb(ROOT / asset["glb"])
        clips = []
        for item in items:
            for clip in extracted.get(item["source"], []):
                if not clip["channels"]:
                    continue
                if item["source"] == asset["source"]:
                    name = document["animations"][clip["clip_index"]]["name"]
                else:
                    name = Path(item["output"]).stem
                clips.append({**clip, "name": name, "source": item["source"]})
        if clips:
            path = ROOT / (asset["glb"] + ".parameters.json")
            path.write_text(json.dumps({"schema": 1, "clips": clips}, indent=2, allow_nan=False), encoding="utf-8")
            outputs.append({"glb": asset["glb"], "sidecar": path.relative_to(ROOT).as_posix(), "clips": len(clips), "channels": sum(len(clip["channels"]) for clip in clips)})
    summary = {"source_files": len(affected), "asset_sidecars": len(outputs), "channel_types": dict(counts), "channels": sum(counts.values()), "assets": outputs}
    (ROOT / "manifests/native-parameters.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "assets"}, indent=2))


if __name__ == "__main__":
    main()
