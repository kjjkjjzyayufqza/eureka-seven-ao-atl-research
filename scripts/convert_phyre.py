"""Adapt Eureka's loose .GCM clusters to Julian Uy's ed8pkg2glb parser.

The upstream parser and MIT license are retained in third_party/ed8pkg2glb.
Only file naming and output routing are adapted here.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "third_party" / "ed8pkg2glb" / "src" / "ed8pkg2glb.py"
spec = importlib.util.spec_from_file_location("ed8pkg2glb", UPSTREAM)
phyre = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = phyre
spec.loader.exec_module(phyre)

_upstream_load_texture = phyre.load_texture


def load_texture_once(dict_data, cluster_mesh_info):
    """Reuse PNGs already decoded for another cluster in the same asset pack."""
    media = cluster_mesh_info.storage_media
    basename = Path(dict_data["m_id"]["m_buffer"].replace("\\", "/")).name
    png = media.output / (basename.rsplit(".", 1)[0] + ".png")
    if not png.is_file():
        _upstream_load_texture(dict_data, cluster_mesh_info)


phyre.load_texture = load_texture_once

_upstream_load_shader_parameters = phyre.load_shader_parameters


def load_eureka_shader_parameters(stream, parameter_buffer, header):
    _upstream_load_shader_parameters(stream, parameter_buffer, header)
    parameters = parameter_buffer["mu_shaderParameters"]
    if "DiffuseMapSampler" not in parameters and isinstance(parameters.get("TextureSampler"), str):
        parameters["DiffuseMapSampler"] = parameters["TextureSampler"]


phyre.load_shader_parameters = load_eureka_shader_parameters
_upstream_create_texture = phyre.create_texture


def untile_rsx_morton(data, width, height, bpb, pitch=0):
    """Reuse upstream Morton bit decoders with RSX X-first addressing.

    Address formulas and DecodeMorton2X/Y are Julian Uy's MIT implementation.
    RSX uses X in the low interleaved bit, unlike upstream's Vita orientation.
    Omit the Vita function's 8px padding for the observed 128x4 texture.
    """
    output = bytearray(len(data))
    minimum = min(width, height)
    bits = minimum.bit_length() - 1
    for position in range(width * height):
        x = phyre.DecodeMorton2X(position) & (minimum - 1)
        y = phyre.DecodeMorton2Y(position) & (minimum - 1)
        tile = position >> (2 * bits)
        if height < width:
            out_x, out_y = tile * minimum + x, y
        else:
            out_x, out_y = x, tile * minimum + y
        destination = (out_y * width + out_x) * bpb
        output[destination:destination + bpb] = data[position * bpb:(position + 1) * bpb]
    return output


def create_eureka_texture(stream, texture, cluster, header, is_cube):
    """Select existing Morton decoding using the native RSX linear-format bit."""
    width, height = texture.get("m_width"), texture.get("m_height")
    fmt = texture.get("m_format")
    packed_1555 = fmt == "ARGB1555" and not is_cube
    short_linear = fmt == "ARGB8" and not is_cube and min(width, height) < 8
    state = texture.get("m_samplerState", {}).get("m_buffers", {}).get("m_u", [])
    rsx_format = state[0].get("m_gcmTextureBlock", {}).get("format") if state else None
    linear = bool(rsx_format & 0x20) if rsx_format is not None else short_linear
    old_morton = phyre.imageUntileMorton
    # Upstream's function named imageUntileMorton uses an identity 8x8 tile.
    # Reuse upstream's Morton bit decoders with RSX axis order.
    morton = untile_rsx_morton
    phyre.imageUntileMorton = (lambda data, *args: data) if linear else morton
    if not (packed_1555 or fmt == "RGB565"):
        try:
            return _upstream_create_texture(stream, texture, cluster, header, is_cube)
        finally:
            phyre.imageUntileMorton = old_morton
    from PIL import Image
    stream.seek(cluster.vram_model_data_offset)
    size = width * height * 2
    data = stream.read(size)
    if len(data) != size:
        raise ValueError(f"Incomplete packed UI texture: {cluster.filename}")
    if not linear:
        data = phyre.Unswizzle(data, width, height, fmt, morton)
    phyre.imageUntileMorton = old_morton
    if packed_1555:
        image = Image.frombytes("RGBA", (width, height), bytes(data), "raw", "BGRA;15")
    else:
        rgba = phyre.decode_rgb565_into_abgr8(io.BytesIO(data), width, height, None)
        image = Image.frombytes("RGBA", (width, height), rgba)
    name = cluster.filename.rsplit(".", maxsplit=2)[0] + ".png"
    with cluster.storage_media.open(name, "wb") as output:
        image.save(output, format="PNG")


phyre.create_texture = create_eureka_texture


class LooseClusterMedia(phyre.IStorageMedia):
    def __init__(self, source: Path, output: Path):
        self.source = source.resolve()
        self.output = output.resolve()
        self.output.relative_to(ROOT)
        self.output.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def logical_name(name: str) -> str:
        return name[:-4] + ".phyre" if name.lower().endswith(".gcm") else name

    def normalize_path_name(self, name):
        return str(name).replace("\\", "/")

    def resolve_read(self, name):
        name = self.normalize_path_name(name)
        if name.lower().endswith(".phyre"):
            name = name[:-6] + ".GCM"
        path = (self.source / name).resolve()
        path.relative_to(self.source)
        return path

    def check_existent_storage(self, name):
        return self.resolve_read(name).is_file()

    def open(self, name, flags="rb", **kwargs):
        if "w" in flags:
            path = (self.output / self.normalize_path_name(name)).resolve()
            path.relative_to(self.output)
            path.parent.mkdir(parents=True, exist_ok=True)
            return path.open(flags, **kwargs)
        return self.resolve_read(name).open(flags, **kwargs)

    def get_list_at(self, name, list_callback):
        for path in sorted(self.source.iterdir()):
            if path.is_file() and list_callback(self.logical_name(path.name)):
                break


def convert(source: Path, output: Path, verbose=True):
    media = LooseClusterMedia(source.parent, output)
    logical_name = media.logical_name(source.name)
    result = phyre.parse_cluster(logical_name, None, media)
    counts = {
        key: len(value)
        for key, value in result.data_instances_by_class.items()
        if isinstance(key, str)
    }
    if verbose:
        print(json.dumps({"source": str(source), "classes": counts}, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "converted" / "probe")
    args = parser.parse_args()
    convert(args.source.resolve(), args.output)


if __name__ == "__main__":
    main()
