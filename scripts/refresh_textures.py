"""Re-decode scene-pack textures after the RSX Morton compatibility repair."""

from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import json
from pathlib import Path
import shutil

from convert_phyre import ROOT, LooseClusterMedia, phyre


def process(job):
    source_directory, output = map(Path, job[:2])
    filenames = job[2] if len(job) > 2 else None
    def render_textures(stream, cluster, header):
        for texture in cluster.data_instances_by_class.get("PTexture2D", []):
            phyre.create_texture(stream, texture, cluster, header, False)
        for texture in cluster.data_instances_by_class.get("PTextureCubeMap", []):
            phyre.create_texture(stream, texture, cluster, header, True)
    phyre.render_mesh = render_textures
    records = []
    media = LooseClusterMedia(source_directory, output)
    for source in source_directory.glob("*.dds.GCM"):
        if filenames is not None and source.name not in filenames:
            continue
        try:
            parsed = phyre.parse_cluster(media.logical_name(source.name), None, media)
        except Exception as error:
            records.append({"source": source.relative_to(ROOT).as_posix(), "status": "failed", "error": str(error)})
            continue
        for texture in parsed.data_instances_by_class.get("PTexture2D", []):
            state = texture.get("m_samplerState", {}).get("m_buffers", {}).get("m_u", [])
            fmt = state[0].get("m_gcmTextureBlock", {}).get("format") if state else None
            records.append({"source": source.relative_to(ROOT).as_posix(), "status": "decoded", "output": (output / (source.name.split('.')[0] + '.png')).relative_to(ROOT).as_posix(), "format": texture["m_format"], "width": texture["m_width"], "height": texture["m_height"], "rsx_format": fmt, "linear": bool(fmt & 0x20) if fmt is not None else None})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--rsx-only", action="store_true", help="Refresh only uncompressed swizzled textures")
    parser.add_argument("--format", help="Restrict a corrective refresh to one existing texture format")
    args = parser.parse_args()
    records = json.loads((ROOT / "manifests/conversion.json").read_text())
    groups = {(str((ROOT / item["source"]).parent), str((ROOT / item["output"]).parent)) for item in records}
    textures = []
    if args.retry_failed or args.rsx_only or args.format:
        previous = json.loads((ROOT / "manifests/textures.json").read_text())
        def selected(item):
            if args.format:
                return item.get("format") == args.format
            return item.get("status") == "failed" if args.retry_failed else item.get("format") in ("ARGB8", "ARGB1555", "RGB565") and not item.get("linear")
        failed = [item for item in previous if selected(item)]
        textures = [item for item in previous if not selected(item)]
        groups = [(source, output, [Path(item["source"]).name for item in failed if (ROOT / item["source"]).parent == Path(source)])
                  for source, output in groups if any((ROOT / item["source"]).parent == Path(source) for item in failed)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(process, job) for job in sorted(groups)]
        for index, future in enumerate(as_completed(futures)):
            textures.extend(future.result())
            if index % 50 == 0:
                print("TEXTURE_PROGRESS", index + 1, len(groups), flush=True)
    assets = json.loads((ROOT / "manifests/playable-assets.json").read_text())
    by_source = {item["source"]: item for item in records}
    for asset in assets:
        if asset["kind"] != "model":
            continue
        original = ROOT / by_source[asset["source"]]["output"]
        destination = (ROOT / asset["glb"]).parent
        for png in original.parent.glob("*.png"):
            shutil.copyfile(png, destination / png.name)
    (ROOT / "manifests/textures.json").write_text(json.dumps(textures, indent=2), encoding="utf-8")
    print("TEXTURE_COMPLETE", len(textures), flush=True)
    failures = [item for item in textures if item["status"] == "failed"]
    if failures:
        raise RuntimeError(json.dumps(failures, indent=2))


if __name__ == "__main__":
    main()
