"""Combine existing Phyre-exported glTF animation streams with their named rig."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import struct


def read_glb(path: Path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<III", data)
    if (magic, version, length) != (0x46546C67, 2, len(data)):
        raise ValueError(f"Invalid GLB header: {path}")
    document = None
    binary = b""
    offset = 12
    while offset < len(data):
        size, kind = struct.unpack_from("<II", data, offset)
        block = data[offset + 8:offset + 8 + size]
        if kind == 0x4E4F534A:
            document = json.loads(block)
        elif kind == 0x004E4942:
            binary = block
        offset += 8 + size
    if document is None:
        raise ValueError(f"GLB JSON missing: {path}")
    return document, binary


def write_glb(path: Path, document: dict, binary: bytes):
    document["buffers"] = [{"byteLength": len(binary)}]
    text = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode()
    text += b" " * (-len(text) % 4)
    binary += b"\x00" * (-len(binary) % 4)
    data = struct.pack("<III", 0x46546C67, 2, 28 + len(text) + len(binary))
    data += struct.pack("<II", len(text), 0x4E4F534A) + text
    data += struct.pack("<II", len(binary), 0x004E4942) + binary
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def merge_animations(model: Path, clips: list[Path], output: Path):
    document, binary = read_glb(model)
    document = copy.deepcopy(document)
    nodes = document.setdefault("nodes", [])
    name_map = {}
    for index, node in enumerate(nodes):
        name = node.get("name")
        if name in name_map:
            raise ValueError(f"Ambiguous model node: {name}")
        name_map[name] = index
    original_names = set(name_map)
    report = []
    for clip in clips:
        animation_document, animation_binary = read_glb(clip)
        animations = animation_document.get("animations", [])
        if not animations:
            continue
        if animation_document.get("meshes"):
            raise ValueError(f"Animation-only merge received a model: {clip}")
        animation_nodes = animation_document.get("nodes", [])
        mapping = {}
        added = set()
        for index, node in enumerate(animation_nodes):
            name = node.get("name")
            if name is None:
                raise ValueError(f"Unnamed animation node: {clip}:{index}")
            if name not in name_map:
                name_map[name] = len(nodes)
                added.add(index)
                nodes.append({
                    key: copy.deepcopy(value) for key, value in node.items()
                    if key in ("name", "matrix", "translation", "rotation", "scale", "extras")
                })
            mapping[index] = name_map[name]
        parents = {}
        for parent, node in enumerate(animation_nodes):
            for child in node.get("children", []):
                parents[child] = parent
        for index in added:
            destination = mapping[index]
            if index in parents:
                parent = nodes[mapping[parents[index]]]
                if destination not in parent.setdefault("children", []):
                    parent["children"].append(destination)
            else:
                scene = document["scenes"][document.get("scene", 0)]
                scene.setdefault("nodes", []).append(destination)
        binary += b"\x00" * (-len(binary) % 4)
        byte_base = len(binary)
        view_base = len(document.setdefault("bufferViews", []))
        accessor_base = len(document.setdefault("accessors", []))
        for view in animation_document.get("bufferViews", []):
            view = copy.deepcopy(view)
            if view.get("buffer", 0) != 0:
                raise ValueError("Multiple animation buffers are unsupported")
            view["buffer"] = 0
            view["byteOffset"] = view.get("byteOffset", 0) + byte_base
            document["bufferViews"].append(view)
        for accessor in animation_document.get("accessors", []):
            accessor = copy.deepcopy(accessor)
            if "sparse" in accessor:
                raise ValueError("Sparse animation accessors require explicit remapping")
            if "bufferView" in accessor:
                accessor["bufferView"] += view_base
            document["accessors"].append(accessor)
        binary += animation_binary
        preserved_extra_targets = set()
        for number, animation in enumerate(animations):
            animation = copy.deepcopy(animation)
            animation["name"] = clip.stem + (f"_{number}" if number else "")
            for sampler in animation["samplers"]:
                sampler["input"] += accessor_base
                sampler["output"] += accessor_base
            for channel in animation["channels"]:
                target = channel["target"]
                old_index = target["node"]
                target["node"] = mapping[old_index]
                name = animation_nodes[old_index]["name"]
                if name not in original_names:
                    preserved_extra_targets.add(name)
            document.setdefault("animations", []).append(animation)
        report.append({
            "clip": str(clip),
            "animation_count": len(animations),
            "preserved_extra_targets": sorted(preserved_extra_targets),
        })
    write_glb(output, document, binary)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("clips", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(merge_animations(args.model, args.clips, args.output), indent=2))
