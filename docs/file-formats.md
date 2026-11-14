# File Formats and Read/Conversion Procedure

## CPK containers

The original archive is a standard CRIWARE CPK. Nested `.cpk` files are recursively expanded only when their first four bytes are `CPK `.

Root archive properties from the existing PyCriCodecs parser:

| Field | Value |
| --- | --- |
| Source size | 625,807,672 bytes |
| SHA-256 | `05a38cef8f3cf9c3036d51d1ea8d624c36e38886e9ead8d237faea886afd7683` |
| Header entry count | 687 |
| TOC offset | `0x800` / 2,048 |
| Content offset | `0xA800` / 43,008 |
| Alignment | 2,048 |
| Mode | 3 |
| Tool version string | `CPKMC2.30.07, DLL3.00.07` |

For named TOC entries, the absolute payload offset is `min(TocOffset, ContentOffset) + FileOffset`. `FileSize` is the packed byte count; `ExtractSize` is the uncompressed byte count. Compressed payloads are passed to the existing `CriCodecs.CriLaylaDecompress` implementation. Every emitted entry is size-checked and SHA-256 hashed.

The complete extraction produced 528 CPK containers including the root, 4,376 file entries, and 1,357,272,801 bytes of extracted payload. Parent and nested payload totals overlap conceptually because nested archives are retained alongside their expanded contents.

`manifests/archives.json` records each entry's archive, internal path, output path, absolute offset, packed size, extracted size, header bytes and hash.

## PhyreEngine GCM clusters

The `.GCM` files are PhyreEngine serialized clusters for the PS3 GCM platform, not text Collada documents. For example, `enao_model.dae.GCM` is compiled Collada-origin mesh data, while `ATKF10N.dae.GCM` is an animation scene. Renaming a compiled file to `.dae` does not turn it into XML.

The parser recognizes the `PHYR` marker and uses big-endian scalar reads for these PS3 files. The fixed-header size in the observed files is `0x58` / 88 bytes. The namespace and class/member descriptors describe serialized object layouts, so a new hardcoded model layout is unnecessary.

Selected fixed-header fields, as read by the pinned upstream parser:

| Offset | Meaning |
| --- | --- |
| `0x00` | Marker `PHYR` |
| `0x04` | Fixed-header size |
| `0x08` | Packed namespace size |
| `0x0C` | Platform ID, bytes `GCM\0` |
| `0x10` | Instance-list count |
| `0x14` / `0x18` | Array-fixup bytes / count |
| `0x1C` / `0x20` | Pointer-fixup bytes / count |
| `0x24` / `0x28` | Pointer-array-fixup bytes / count |
| `0x2C` | Pointers-in-arrays count |
| `0x30` / `0x34` | User-fixup count / payload bytes |
| `0x38` | Total serialized object-data bytes |
| `0x3C` / `0x40` | Header-class instance / child counts |

The namespace contains type IDs, class descriptors, member descriptors, strings and default data. Instance lists describe object batches. Compressed fixup streams reconstruct array and pointer relationships. Platform-specific GPU buffers follow the fixup area. The implementation remains upstream `parse_cluster`; see `docs/tools-and-attribution.md` for the exact source revision.

### Mesh and rig objects

- `PMesh`, `PMeshSegment`: geometry and material segmentation.
- `PDataBlockGCM`, `PVertexStream`: vertex/index streams and their formats.
- `PNode`, `PMatrix4`, `PWorldMatrix`: scene hierarchy and transforms.
- `PSkinBoneRemap`, `PSkeletonJointBounds`, `PMeshInstance`: joint mappings, skin data and instances.
- `PMaterial`, `PParameterBuffer`, `PAssetReferenceImport`: materials, shader parameters and external textures.

The first inspected `enao_model` exports one glTF mesh with 21 primitives, 90 skin joints, 30,469 primitive-summed vertices and 12,497 triangles. These are exported primitive counts, not welded-vertex counts and not a claim about other titles.

### Animation objects

- `PAnimationSet` references animation clips.
- `PAnimationClip` stores clip bounds and channel arrays.
- `PAnimationChannel` stores typed transform values and also native scalar/vector parameters such as camera FOV and shader properties.
- `PAnimationChannelTimes` stores sample times.
- `PAnimationConstantChannel` stores constant transform channels.

The existing exporter writes these as glTF animation samplers and channels. Separate animation-only GLBs are merged with the model using **exact node names**, not guessed bone indices. Additional animation control nodes absent from the mesh skeleton are retained and listed in the merge manifest. Retaining a helper node does not imply that it deforms the skin.

`enao/ATKF10N.dae.GCM` contains 13 variable channels and 179 constant channels. Its standalone GLB contains 192 transform channels. Six additional board helper nodes are not mesh-skin joints; the merge preserves those nodes rather than silently dropping their channels.

### Textures

`.dds.GCM` files are compiled Phyre texture containers, not ordinary DDS files. The existing Phyre parser reads dimensions, format, mip count and GPU data location. Converted PNGs are emitted beside the GLBs. The supplemental inventory contains 1,087 2D textures in scene-bearing packs: 567 DXT5, 296 ARGB8, 217 DXT1, three RGB565, two DXT3 and two ARGB1555. Counts refer to resource files, including duplicates across packs.

The native `m_samplerState.m_buffers.m_u[0].m_gcmTextureBlock.format` carries the RSX linear flag (`0x20`). Swizzled uncompressed textures need whole-image Morton ordering with X in the low interleaved bit. Upstream's function named `imageUntileMorton` actually applies an identity 8x8 tile layout; using it produced striped textures. Upstream's separate `DecodeMorton2X/Y` bit decoders are reused with a local RSX axis/layout adapter. The 128x4 UI texture must not be rounded to an 8-pixel height. ARGB1555 uses Pillow's `BGRA;15` decoder; other pixel/block decoding remains upstream. This correction was visually checked against the AO, ZERO and theEND meshes and their UV-aligned details. RSX bit ordering was cross-checked against the [RPCS3 image utilities](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Emu/RSX/Utils/image_utils.hpp); RPCS3 code was not copied into this pipeline.

Eureka uses `TextureSampler` for color textures and `NormalMapSampler` for normal textures. Color textures are mapped to glTF base color. The original custom Phyre shaders, reflections, HDR and game-specific effects are not reproduced exactly by a standard Blender material.

### Native parameter animation beyond glTF TRS

The source-channel audit found 459 files containing channels omitted by the upstream TRS-only glTF target map. All 1,468 omitted channels are now separately extracted using the same existing Phyre schema parser: 1,277 `ShaderParameterF1`, 116 `ShaderParameterF4`, 23 `UserAttributeFloat`, and 52 `CameraFov`. All body/weapon unit transform channels were already covered; the Unit-category mismatches belonged to camera packs.

`export_parameters.py` enables the existing schema reader for `PCameraPerspective`, `PCamera` and `PCameraBase`, without defining a new binary layout. For a variable channel, only `m_keyCount` times and `m_keyCount * dimension` values are retained: serialized arrays can include padding. Constant-channel vectors come from `m_value`, with clip constant bounds retained. The sidecar stores source path, native clip name, property name, target class/name/location, original interpolation code, times and values. A `ShaderParameterF4` has four values per key; other observed native types are scalar.

`blender_parameters.py` adds these curves as custom-property animation on named Empty objects. Every sidecar is embedded as `Native_Parameters.json`. Camera FOV is treated as a vertical angle in radians and drives a perspective camera through `lens = sensor_height / (2*tan(FOV/2))`. That vertical-axis interpretation is a preview convention, not a verified Phyre camera projection reconstruction. `Transparency` multiplies preview alpha and `MaterialColour` multiplies preview base color. Exact shader semantics, color space and compositing remain game-specific. Other properties retain fully inspectable animated values without an invented gameplay/rendering effect.

The standard `.glb` carries transform animation; its adjacent `.parameters.json` and the supplied importer are required for native parameter playback. The saved `.blend` includes both. Changing an NLA clip must select matching tracks on all objects.

## Other extracted formats

The extraction inventory also retains `.csc`, `.fcmd`, `.mtb`, `.prm`, `.pdt`, `.ptc`, CRI audio/movie assets, and 17 `Lip/*.pkg` files. The latter begin with `PKG\0` and have a big-endian count-like word; their lip-sync records have not been decoded or converted to facial actions. They are not claimed as supported Phyre skeletal clips. The resource script/move graph, UI compositing logic, effects runtime and audio synchronization are not recreated in Blender. A later explicitly requested roster investigation parsed the CSVB configuration/script data and analyzed a research ELF; see [eboot-roster-data-mining.md](eboot-roster-data-mining.md).

### CSVB configuration and command containers

All 32 `.prm`, 53 `.csc` and 21 `.fcmd` files use `CSVBv4.3` in this build. The pinned existing `csvb.py` parser reads the big-endian header, table directories, column metadata, row spans and string pool. A table directory occupies 0x28 bytes and includes a 16-byte name, row count, row size, column count, column-metadata offset and absolute row-data offset. This title also uses string-reference kinds 7 and 9; the local adapter resolves their pool-relative pointers while retaining raw values. Kind 3 fields are read as float32, and two-byte kind-5 fields retain their raw values, including `0xFFFF` sentinels.

In the observed `.csc` command tables, each eight-byte row stores an argument offset followed by an opcode, and trailing data holds argument words. The mining output preserves these words without claiming every opcode's semantics. Some `.fcmd`/event records can drive transforms, effects or damage behavior even when a model has no skeletal Action. Native actor behavior and extracted Phyre skeleton animation remain distinct evidence.

## Output formats

- Raw extracted assets: original CPK entry bytes, unchanged by conversion.
- `.glb`: glTF 2.0 binary scenes, meshes, skins and animation tracks.
- `.png`: decoded referenced textures.
- `.blend`: Blender **5.1** scenes with packed resources and playback controls.
- `.json`: entry provenance, conversion coverage, merge details and playback measurements.

Playback reports distinguish successful import from actual evaluated mesh movement. Blender's scene FPS is a playback setting; it is not evidence that the source animation was sampled at that rate.
