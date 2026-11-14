# Tools, Authors, Versions, and Local Changes

## Actual production dependencies

| Component | Author / project | Exact version / revision | Role |
| --- | --- | --- | --- |
| PyCriCodecs | Youjose / CriCodecs; local legacy PyCriCodecs distribution | 0.4.11 | CPK UTF tables and archive parsing |
| CriCodecs native module | Youjose / CriCodecs and credited upstream codec contributors | Installed CPython 3.11 Windows x64 build, SHA-256 below | CRILAYLA decompression |
| ed8pkg2glb | Julian Uy (`uyjulian`) | `c076d638e3f978afe2bb4de0a6f911f03b2afdfd` | Phyre cluster schema, fixups, mesh streams, skins, transforms, animation and texture export |
| Python | Python Software Foundation and contributors | CPython 3.11.4, MSC v.1934 64 bit | Local orchestration and format adapters |
| Pillow | Pillow contributors / python-pillow | 12.3.0 | Existing packed ARGB1555/BGRA pixel decoders for UI texture compatibility |
| Blender | Blender Foundation and contributors | **5.1.2**, build `ec6e62d40fa9`; user requires 5.1 | Final import, action playback, deformation evaluation, packed `.blend` files |
| Blender glTF importer | Blender glTF-Blender-IO contributors | Importer bundled with the selected Blender 5.1 installation | glTF 2.0 scene, mesh, armature and action import |
| Git | Git project and contributors | 2.56.1.windows.1 | Read-only clone and revision identification |

Blender 4.2.1 LTS was used for an early experiment before the user requested Blender 5.1. Its probe reports are historical evidence only and do not substitute for final Blender 5.1 validation.

## Primary upstream links

- CriCodecs: <https://github.com/Youjose/CriCodecs>
- Historical PyCriCodecs fork: <https://github.com/t-wy/PyCriCodecs>
- ed8pkg2glb: <https://github.com/uyjulian/ed8pkg2glb>
- Pinned parser source: <https://github.com/uyjulian/ed8pkg2glb/blob/c076d638e3f978afe2bb4de0a6f911f03b2afdfd/src/ed8pkg2glb.py>
- Blender glTF importer: <https://github.com/KhronosGroup/glTF-Blender-IO>
- Pillow: <https://github.com/python-pillow/Pillow>

## Attribution and provenance limits

`third_party/ed8pkg2glb` contains an unmodified minimal source snapshot of Julian Uy's repository at the pinned commit. Only the required source module and original license are included; their hashes are in `dependencies.lock.json`. The full upstream checkout is preserved in a separate local cache. Its MIT license and original notices are retained in `third_party/ed8pkg2glb/LICENSE`. The substantial Phyre parser and export implementation is Julian Uy's work, not a newly reverse-engineered parser written for this session.

The locally installed PyCriCodecs package does not expose an upstream commit ID. Its installed `cpk.py` is byte-identical to the separately installed local `PyCriCodecs/cpk.py` source. Its provenance is therefore recorded by distribution version and file hashes; no unverified Git commit is assigned to it.

The installed PyCriCodecs distribution also has no populated `Author` or `License` metadata field. Attribution to Youjose is based on the upstream project identity, not that absent metadata. No license is inferred for this unidentified installed build, and its binaries are not copied into this research package. Julian Uy's vendored parser has its verified MIT license retained. Blender/glTF importer, Pillow and Python retain their respective upstream project licenses; their installed programs are used as dependencies rather than redistributed here.

Installed files:

- `PyCriCodecs/cpk.py` SHA-256: `aabb21de537af7980c21633e886b16334b06bf41050f93e852bf49dd6ec43eab`
- `PyCriCodecs/__init__.py` SHA-256: `046e41fc52d41e3ac155940f48375acab6814551f262828479a6b11882f36ccd`
- `CriCodecs.cp311-win_amd64.pyd` SHA-256: `6b56592a829b77f110010645efdb3ca32f0ab5ab31e79950fd691614bd4d7813`

## Session-local code

The scripts under `scripts/` provide project-local orchestration and narrowly scoped compatibility code. They must not be represented as upstream Julian Uy / Youjose code.

| Script | Local responsibility |
| --- | --- |
| `extract_archives.py` | Wrap existing CPK and CRILAYLA implementations; validate paths, offsets and sizes; recursively extract nested CPK files; record hashes and provenance |
| `convert_phyre.py` | Adapt loose `.GCM` filenames to the upstream `.phyre` interface; route outputs; cache decoded PNGs; alias Eureka's `TextureSampler` to the existing diffuse-texture slot; provide Pillow fallbacks for two UI pixel cases |
| `convert_all.py` | Batch upstream parsing over every Collada-origin cluster; retain successes and explicit failures in manifests |
| `glb_tools.py` | Combine exported animation streams with model nodes by exact node name; preserve additional control nodes and report them |
| `prepare_playback.py` | Group model/clip outputs, assemble playback scenes, copy external PNGs and audit source/export channel counts |
| `export_parameters.py` | Reuse upstream schema parsing to preserve all observed non-TRS camera/shader/user curves in JSON |
| `blender_parameters.py` | Create Blender custom-property Actions and preview bindings for preserved native curves |
| `blender_verify.py` | Import the resulting GLB, select corresponding NLA tracks, sample evaluated mesh vertices, save packed Blender scenes and write playback evidence |
| `blender_batch.py` | Run the scene verifier in deterministic local shards, enforce Blender 5.1 and compare imported clip counts |
| `refresh_textures.py` | Decode scene-pack textures with corrected RSX layout selection and refresh assembled PNGs |
| `blender_refresh_textures.py` | Reload corrected textures into existing Blender 5.1 scenes, pack images and refresh selected previews |
| `build_catalog.py` | Generate unit geometry/clip inventory and timing documentation from exported data |
| `audit_delivery.py` | Final coverage, source-hash, channel-accounting and delivery evidence check |
| `repair_native_nla.py` | Correct fractional native-parameter NLA bounds in previously saved scenes; retain the exact correction log |

`diagnose_parameter.py` is a local diagnostic probe retained for the research record. It investigated dependency-graph refresh after adding animated custom properties; it is not a production conversion dependency. Historical console logs were moved outside the repository during cleanup. Corrected outcomes remain documented here and in local JSON evidence.

## Available but not used in the extraction/conversion implementation

- QuickBMS, by Luigi Auriemma: present locally; not needed because PyCriCodecs successfully parsed the CPK files.
- Noesis, by Rich Whitehouse: present locally; not needed for the successful Phyre-to-glTF route.
- IDA Pro / ida-pro-mcp was unnecessary for model extraction. It was subsequently used for the explicitly requested EBOOT/unit-roster investigation; details and versions are recorded below and in [eboot-roster-data-mining.md](eboot-roster-data-mining.md).
- Live Blender MCP: initial connection attempt failed. Local background Blender provides reproducible validation without depending on the live GUI session.

## Observed compatibility repairs

1. Loose files use `.dae.GCM` and `.dds.GCM`; upstream archive discovery expects `.dae.phyre` and `.dds.phyre`. A storage adapter changes logical names only.
2. Eureka materials use `TextureSampler` for color textures. Upstream expects `DiffuseMapSampler`; the adapter aliases the already parsed shader parameter before export.
3. Two UI clusters reference ARGB1555 textures, unsupported by the upstream PNG conversion dispatch. Pillow's existing `BGRA;15` decoder is used with corrected RSX Morton handling.
4. A 128 x 4 ARGB8 UI texture stores exactly width x height x 4 bytes. The Morton adapter retains the actual height instead of forcing eight rows.
5. Visual inspection found upstream's nominal Morton routine used an identity 8x8 tile layout. The local RSX adapter reuses Julian Uy's `DecodeMorton2X/Y` functions with the RSX X-first axis convention and native linear-format flag. The resulting atlas alignment was checked on three mecha. RPCS3's [image_utils.hpp](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Emu/RSX/Utils/image_utils.hpp) was consulted as primary reference for RSX interleaved bit order; its implementation was not copied or linked.
6. Upstream glTF exports only TRS animation targets. The local supplemental path preserves native FOV, shader and user-property curves without replacing the upstream binary parser.
7. Blender 5.1 requires a dependency-graph update after adding new animated custom properties; the importer refreshes the owning object before comparing evaluated values with source keys. New Actions use the Blender 5.1 slotted-action/NLA API.
8. NLA strip creation accepts an integer start, while imported keys can start just below an integer due to source float32 representation. The importer explicitly restores the Action's fractional bounds. The final reopen audit found and the repair script corrected 12 previously saved scenes; final key checks showed zero error.

The original source resources remain the authority for any future refinement of shader fidelity, UI blending, helper-node interpretation, or texture layout.

## Follow-up executable / roster investigation

The user subsequently requested deeper EBOOT and data-mining evidence. This extended the research beyond the original archive/mesh conversion. Additional actual dependencies were:

| Component | Author / source | Version / revision | Role |
| --- | --- | --- | --- |
| scetool | naehrwert; NP support credited to flatz | Installed public build 0.2.9 | Offline SELF-to-ELF extraction into the research directory |
| IDA Pro and Hex-Rays | Hex-Rays | IDA 9.1; decompiler 9.1.0.250226 | PPC executable analysis and targeted pseudocode |
| IDA MCP bridge | Existing local multi-instance installation | Modified bridge revision/author not fully exposed by API; tool inventory retained | Routes requests only to the research EBOOT instance |
| `csvb.py` | `kimjh-eclipse` repository; commit author June | `d1e54c7b41b1165970f841c3de3fd7d86cc93bdc`, Apache-2.0 | Existing CSVB directory/header/column-width parser |
| pyelftools | Eli Bendersky and contributors | 0.33 | ELF segments, section flags and virtual/file mapping |
| Capstone | Nguyen Anh Quynh and contributors | 5.0.7 | Existing PowerPC disassembler for TOC references |

The unmodified `tools/csvb.py` module and original Apache-2.0 license are retained as a minimal pinned snapshot at `third_party/srw-og-infinite-battle-korean/`. The full upstream checkout is preserved outside the project. It was found through public source search before implementing a table decoder. The local adapter adds read-only handling of this title's type-7/type-9 string references and preserves raw fields. No upstream rebuilding or translation operation was used.

Project-local scripts added for this extension:

- `mine_roster_data.py`: enumerate all extracted signatures and parse 106 CSVB files through the existing parser; export typed/raw evidence and references.
- `mine_elf_roster.py`: reuse pyelftools/Capstone to locate ELF strings, resolve 32-bit TOC pointers and recover instruction references.
- `ida_roster_triage.py`: isolated IDAPython analysis and selected string/xref export.
- `ida_export_requested.py`: export only requested functions from a separate research-IDB copy when MCP truncates a long function response.
- `audit_roster_mining.py`: one semantic cross-check across all 18 unit IDs, the parameter families, all 44 stage rows, native selection evidence and source integrity.

Actual tool/file hashes and installed-package author metadata are in `analysis/tool-provenance.json`. No key material or original executable was modified or published. See [the complete follow-up report](eboot-roster-data-mining.md) for commands, code addresses, evidence, findings and remaining uncertainty.

## Repository preparation tools

The project-local `publication_privacy.py` checks publishable text for local identity markers, private paths, unreviewed contact details and credential patterns. Identity markers are read into memory from local account/Git metadata and are never stored in public files. The project-local `vendor_integrity.py` verifies minimal source/license snapshots using `dependencies.lock.json`. Both existing research audits now use pinned file hashes instead of expecting nested Git repositories. `check_public_tree.py` reads actual staged or committed Git blobs and checks source-only paths, text content, syntax, Markdown rules and dependency hashes. The local pre-commit hook invokes it with Git and Python's standard library, without importing Blender, IDA or game data. See [repository policy](repository-policy.md) for the file boundary and cleanup record.
