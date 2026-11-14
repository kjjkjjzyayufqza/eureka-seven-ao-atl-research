"""Batch-convert all extracted Collada-origin Phyre clusters using upstream code."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import traceback

from convert_phyre import ROOT, convert
from glb_tools import read_glb


def process_group(job):
    source_directory, output, files = job
    records = []
    for filename in files:
        source = Path(source_directory) / filename
        record = {"source": source.relative_to(ROOT).as_posix()}
        try:
            result = convert(source, Path(output), verbose=False)
            classes = {
                key: len(value) for key, value in result.data_instances_by_class.items()
                if isinstance(key, str)
            }
            glb = Path(output) / (source.name.split(".", 1)[0] + ".glb")
            record["classes"] = classes
            record["material_adapter"] = "eureka-texture-sampler-v1"
            record["status"] = "converted" if glb.exists() else "no_scene_nodes"
            if glb.exists():
                document, _ = read_glb(glb)
                record.update({
                    "output": glb.relative_to(ROOT).as_posix(),
                    "meshes": len(document.get("meshes", [])),
                    "nodes": len(document.get("nodes", [])),
                    "skins": len(document.get("skins", [])),
                    "animations": len(document.get("animations", [])),
                    "primitives": sum(len(m["primitives"]) for m in document.get("meshes", [])),
                    "vertices": sum(
                        document["accessors"][primitive["attributes"]["POSITION"]]["count"]
                        for mesh in document.get("meshes", []) for primitive in mesh["primitives"]
                    ),
                })
        except Exception as error:
            record.update({"status": "failed", "error": str(error), "traceback": traceback.format_exc()})
        records.append(record)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--category", choices=("Unit", "Map", "UI", "OutGame"))
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--refresh-models", action="store_true")
    args = parser.parse_args()
    archives = json.loads((ROOT / "manifests/archives.json").read_text(encoding="utf-8"))
    previous_path = ROOT / "manifests/conversion.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else []
    previous_map = {item["source"]: item for item in previous}
    groups = defaultdict(list)
    outputs = {}
    for archive in archives:
        source_archive = Path(archive["source"])
        if source_archive == Path(archives[0]["source"]):
            continue
        archive_key = source_archive.relative_to(ROOT / "extracted/root").with_suffix("")
        category = archive_key.parts[0]
        if args.category and category != args.category:
            continue
        for entry in archive["entries"]:
            if not entry["output"].lower().endswith(".dae.gcm"):
                continue
            prior = previous_map.get(entry["output"])
            refresh = args.refresh_models and prior and prior.get("meshes", 0) > 0
            if prior and prior["status"] != "failed" and not refresh:
                continue
            if args.retry_failed and not (prior and prior["status"] == "failed"):
                continue
            source = ROOT / entry["output"]
            output = ROOT / "converted/assets" / archive_key / source.relative_to(Path(archive["destination"])).parent
            key = (str(source.parent), str(output))
            groups[key].append(source.name)
            outputs[key] = output
    jobs = [(source, output, sorted(files)) for (source, output), files in groups.items()]
    print(f"Queued {sum(len(job[2]) for job in jobs)} clusters in {len(jobs)} groups", flush=True)
    count = 0
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_group, job): job for job in jobs}
        for future in as_completed(futures):
            records = future.result()
            for record in records:
                previous_map[record["source"]] = record
            count += 1
            if count % 20 == 0 or count == len(jobs):
                print(f"Completed groups {count}/{len(jobs)}", flush=True)
            previous_path.write_text(json.dumps(list(previous_map.values()), indent=2), encoding="utf-8")
    records = list(previous_map.values())
    summary = {
        "clusters": len(records),
        "status": dict(Counter(item["status"] for item in records)),
        "model_clusters": sum(item.get("meshes", 0) > 0 for item in records),
        "animation_clusters": sum(item.get("animations", 0) > 0 for item in records),
    }
    (ROOT / "manifests/conversion-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
