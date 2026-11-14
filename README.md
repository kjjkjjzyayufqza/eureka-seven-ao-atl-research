# Eureka Seven AO: Attack the Legend - File Research

Research scripts and English documentation for the PS3 build `BLJS93011`, application 01.00. This project studies CRI CPK containers, Phyre scenes, model/animation conversion and the unit roster. Each researcher supplies their own original game files as read-only inputs.

## Repository contents

- `scripts/`: extraction orchestration, format adapters, Blender playback checks and roster research tools.
- `docs/`: formats, commands, findings, validation limits and tool attribution.
- `third_party/`: two minimal pinned parser source snapshots with original licenses.
- `dependencies.lock.json`: authors, URLs, commits, licenses and exact file hashes.
- `AGENTS.md`, `.gitignore` and `.githooks/pre-commit`: English documentation and source-only publication rules.

Game archives, executables, ELF files, models, textures, animations, audio, video, IDA databases, decompiled functions and raw data exports are excluded. The local directories `analysis/`, `extracted/`, `converted/`, `playable/`, `previews/` and `manifests/` are not distributed. Paths in the reports describe local inputs or generated outputs, not downloadable assets.

## Recorded findings

The local study covered 528 CPK containers, 4,376 extracted entries and 1,301 identified Collada-origin Phyre clusters. It produced 495 model scenes and 72 auxiliary scenes containing 1,229 source clips. All 567 saved scenes were reopened with **Blender 5.1.2**. Clips include loops, reactions, transitions, camera/UI animation and duplicates; these counts do not represent unique attacks or playable units.

The roster audit found 18 unit definitions: eight selectable configurations representing seven named player types, plus ten non-player definitions. No additional complete unit definition was found in the audited build. This is static delivered-build evidence, not exhaustive runtime proof.

Original transform timestamps and supplemental native parameter curves are preserved in local conversion outputs. Game-side attack sequencing, hit detection, effects, original shaders and lip-sync behavior are not reconstructed. See the reports for evidence and limits.

## Start a local study

Use Python 3.11 and Blender **5.1**. Install the Python dependencies from `requirements.txt`; separately install the PyCriCodecs/CriCodecs build described in the attribution report. Optional executable research requires separately installed tools and user-provided inputs.

```powershell
git config core.hooksPath .githooks
python -m pip install -r requirements.txt
$gameArchive = Join-Path $env:EUREKA_AO_USRDIR 'EurekaAODataR.cpk'
python scripts/extract_archives.py $gameArchive
```

Follow [reproduction and playback](docs/reproduce-and-play.md) for the conversion sequence. Set `EUREKA_AO_USRDIR` locally to your original game's USRDIR directory. Input paths are supplied explicitly; do not commit their machine-specific values. A clean clone contains no game input or generated output.

The local pre-commit hook checks the complete Git index, including forced additions. Run `python scripts/check_public_tree.py --staged` to check a prepared index without committing. See the [repository policy](docs/repository-policy.md) for file boundaries and clean-clone checks.

## Documentation

- [Reproduction and playback](docs/reproduce-and-play.md)
- [File formats and conversion](docs/file-formats.md)
- [Tools, authors and pinned sources](docs/tools-and-attribution.md)
- [Unit models and animation inventory](docs/unit-models-and-animations.md)
- [Playable and non-player roster](docs/playable-and-npc-roster.md)
- [EBOOT and delivered-data roster audit](docs/eboot-roster-data-mining.md)
- [Research chronology](docs/research-log.md)
- [Validation and limitations](docs/validation.md)
- [Publication privacy audit](docs/security-audit.md)

## Attribution and licensing

The Phyre parser is Julian Uy's `ed8pkg2glb` under MIT. The CSVB parser comes from the `kimjh-eclipse` repository, with commit author June, under Apache-2.0. Original licenses are included. Project-local adapters extend these parsers for this title. See [tools and attribution](docs/tools-and-attribution.md) and `NOTICE` for all tool authors and provenance limits.

No project-wide license has yet been selected for original code or documentation. Third-party licenses apply to their own files. This repository grants no rights to game content.
