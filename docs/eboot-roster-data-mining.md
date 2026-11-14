# EBOOT and Complete Delivered-Data Roster Audit

Research date: 2026-11-14. Target: local PS3 BLJS93011, application 01.00. This supersedes the earlier uncertainty about whether `ena2` is selectable. It does not claim that every possible runtime state or another game build has been examined.

## Results

- **18 unit definitions**, IDs 0–17, with no gaps.
- **Eight selectable player configurations**, IDs 0–7. The two AO Nirvash configurations occupy the same navigation position and can be switched under an unlock condition. Merging those into one named machine gives **seven named playable types**.
- **Ten non-player definitions**, IDs 8–17, all present in delivered stage presets. They use eight unique main-model archives.
- **16 unique main-unit model archives** across all 18 definitions. `ems2` shares `ems1.cpk`; `esc2` shares `esc1.cpk`.
- **32 Unit-category model resources** including weapons/projectiles. The two model archives not referenced by the parsed typed-table paths or named ELF paths are `ems1_gun` and `enze_knife`. Both are accessory models, not additional complete units. This scoped lack of references is not proof they can never be loaded by a constructed filename.
- No complete nineteenth unit definition was found in the delivered executable/configuration/resource cross-check.

Final machine-readable evidence: `analysis/roster-mining-audit.json`. The semantic cross-check passed. Original EBOOT bytes remain unchanged.

## Executable preparation and addressing

The original `EBOOT.BIN` is a SELF container, 7,039,976 bytes. Searching that container directly for unit names returned no useful results. An offline copy was placed under `analysis/`; the existing scetool 0.2.9 decrypted it to a 7,037,544-byte ELF. No emulator or game process was operated, no original was patched, and no output was published.

| Artifact | SHA-256 |
| --- | --- |
| Original/copied EBOOT.BIN | `dffa06336a8b879c12c36705ad711f19d9d797ef6f1a836988d9745d10fc360c` |
| Decrypted EBOOT.elf | `9f7974491e1544f68973da9e5c834bcb186d09b04fca12f652e2f78b320a281d` |

The ELF is big-endian `EM_PPC64`. Despite its ELF64 container, this build uses **32-bit pointers and eight-byte PPU function descriptors**. The entry descriptor is at `0x67AA08`, the entry code is `0x10230`, and the shared TOC base is `0x69B1D0`. Interpreting the descriptor as three 64-bit words gives incorrect addresses.

IDA 9.1 initially identified 13,723 functions. Ordinary string xrefs were missing for the relevant TOC loads. The investigation therefore resolved four-byte pointers in the TOC and disassembled actual `r2`-relative loads with Capstone. This produced 38 targeted instruction references from 91 filtered ELF strings. Examples:

| String | String address | TOC slot | Referencing instruction |
| --- | --- | --- | --- |
| `SelectCharaOpen` | `0x54D348` | `0x695348` | `0x1F3084` |
| `OutGame/Select.cpk` | `0x54D5D8` | `0x6953FC` | `0x1F4C70` |
| `CharResource.prm` | `0x54DDB0` | `0x6958B4` | `0x227FC0` |
| `UnitResource.prm` | `0x54DE08` | `0x6958C8` | `0x227250` |

All addresses here are ELF virtual addresses, not guessed file offsets. `scripts/mine_elf_roster.py` records the ELF mapping and the TOC evidence. The source ELF lacks useful section names, so executable sections are selected by flags rather than assumed `.text` labels.

## Evidence that AO's second resource is selectable

The earlier report only knew `ena2` was a separate resource. Executable analysis now shows more:

1. The UI binding initializer `sub_1F2D50` registers `PilotIconENAO` and `PilotIconENA2` separately, at binding indices 76/77. It also registers the other six player-configuration icons, with no NPC icon in this player set. Merely having an icon would not by itself establish selectability.
2. `sub_202538` implements pilot navigation. Its recognized choice range is IDs **0–7**. It routes the ordinary sequence through AO, Alleluia, Kyrie, TV ZERO, Devilfish, theEND and film ZERO, retaining the selected AO alternative when returning to that position.
3. `sub_1F4058` checks the appropriate mode/unlock conditions and toggles the current choice at object offset `0x118` between **0 and 1**. The unlock bit is read through `sub_1D4BA8(..., 1)`.
4. Actual menu input handlers `sub_202A30` and `sub_202DD0` call that toggle on input-mask bit `0x10`. This report does not assign a physical controller-button name without tracing the input translation.
5. The confirmation handler `sub_202DD0` copies the current choice into the primary selection (`a1[68] = a1[70]`). `sub_202A30` similarly commits the ally selection and explicitly rejects pairing AO ID 0 with AO ID 1 as two separate teammates.

Together these establish an implemented **selectable alternate configuration**, rather than an inference from a filename. They do not establish the official subtitle of that variant. The files still must not be renamed to type ZERO spec2 based on `ena2` alone. `enao` and `ena2` have identical first 232 bytes of UnitResource parameters but separate model/action paths and color-texture resources.

The native player-selection code supports **eight configurations / seven named machine types**, with AO's alternatives sharing one navigation position. Calling these eight entirely different mecha would overstate the data.

## theEND and mode-dependent availability

ID 5 is theEND. The navigation routine skips that ID in the story-mode branch, while the mission-mode branch admits IDs according to their unlock bits. This explains why a report based only on story availability can differ from a complete unlocked roster. The previously cited trophy guide's statement that all eight Single Missions unlock Anemone is consistent with a dedicated mission unlock, but the exact complete unlock-setting logic was not independently reconstructed here.

ID 5 is also the first enemy in Single Mission 6 and appears in story/tag presets. Being an enemy in those presets does not make it permanently unplayable.

## Full data mining and table consistency

Every one of the **4,376 extracted entry paths** was examined by signature. All **106 CSVB files** parsed successfully: 32 `.prm`, 53 `.csc`, and 21 `.fcmd` files. The existing Apache-2.0 parser by `kimjh-eclipse` / June was reused for headers, table directories and column widths. This game's string-reference column kinds 7/9 were handled in a local read-only adapter, alongside the parser's existing 0x1B text kind.

The following independent parameter families each have **18 unit-ordered tables/definitions**:

- `UnitResource`: 18 rows in `UNT_RES`.
- `BulletParam`, `ForceParam`, `FrameEvent`, `NodeParam`, `ThinkParam`: 18 tables each, in corresponding unit order.

The NodeParam labels contain mistakes such as `ND_KEO4` and a repeated `ND_KESC2`. Those labels were not treated as new unit IDs or collapsed into a dictionary. The parser preserves ordered table lists, so the repeated name does not erase the final table.

`ActionParam` has 71 rows, but those describe action settings rather than 71 units. Weapon resources, special cameras, table rows, named forms and distinct geometry are counted separately.

Full typed/raw table records are under `analysis/tables/`; `analysis/data-mining-inventory.json` records their provenance and reference counts. Raw values remain available beside interpreted strings/floats. Type-5 two-byte fields preserve `0xFFFF` sentinels instead of being mistaken for a unit number.

## All stage presets and NPC usage

`StageResource` contains **44 rows**: 18 story stages, eight Single Missions, 16 Tag Missions and two Challenge stages. The unit fields at typed columns 2/4/6 contain player/ally presets; columns 8/10/12/14 contain enemy presets. A paired flag is retained separately, without assigning every bit an unverified meaning.

The union of preset unit IDs is **0 and 2–17**. ID 1, the selectable AO alternate, is not a fixed stage preset. Every ID in the non-player range **8–17** occurs in at least one delivered stage row. Thus none of these ten is merely an otherwise unused name in UnitResource.

| ID | Code | Main archive | Role and supporting use |
| ---: | --- | --- | --- |
| 8 | `etes` | `etes.cpk` | Devilfish S; film story finale and Single Mission 8 |
| 9 | `ems2` | `ems1.cpk` | MS20 configuration; film story stage 2 / Tag Mission 14 |
| 10 | `ems1` | `ems1.cpk` | MS10 configuration; TV/film enemy presets |
| 11–14 | `eko1`–`eko4` | Four separate archives | Coralian family; TV/film and Challenge enemy groups |
| 15 | `esc1` | `esc1.cpk` | Secret encounter in the first AO story stages |
| 16 | `esc2` | `esc1.cpk` | Option-related configuration; AO wave/escort groups and Challenge 1 |
| 17 | `esc3` | `esc3.cpk` | Enemy-slot entry in all three AO story finales and Tag Mission 3 |

### `esc3` is not safely dismissed as scenery

The prior report left this resource's gameplay role unresolved because its main model has no skin or skeletal clip. The stage data puts ID 17 into the first enemy slot in rows 2, 5, 8 and 28. Its action-command file contains `DMG50QN`, `DMG80QN`, `DMG99QN` and `ev_Cam14N`; it also has bullet, force, frame-event and AI parameter entries. These are evidence of an active encounter resource with damage/event behavior. The exact official monster label and all command semantics remain unconfirmed.

Lack of a skeletal animation in its `.blend` therefore does **not** prove absence of motion or behavior in the game. Actor transforms, damage events, cameras and effects can be driven by code/scripts. Those runtime commands were retained and mined, not converted into a fabricated skeletal Action.

## Unreferenced and missing paths

The actual Unit model inventory includes `ems1_gun` and `enze_knife` with no matching archive path in the parsed typed-table fields or the ELF's named paths. These are small accessory resources, not an additional mech skeleton/moveset. Constructed path loading has not been ruled out, so the report calls them **unreferenced by this audit**, not proven dead assets.

Ten paths mentioned in the parameter data have no corresponding delivered root entry. Nine are weapon `.fcmd` names, while the remaining path is `Unit/mvar_e_cam.cpk`. The latter is a camera-path reference; its name alone is not evidence of an extra Valkyrie or other hidden unit. No missing **main unit-model archive** was found for any of the 18 unit definitions.

## Tools, authors and source attribution

| Tool / code | Author / origin | Used revision / version | Use |
| --- | --- | --- | --- |
| scetool | naehrwert; NP license support credited to flatz | Installed public build 0.2.9 | Offline SELF-to-ELF extraction |
| IDA Pro / Hex-Rays | Hex-Rays | IDA 9.1, decompiler 9.1.0.250226 | PPC function analysis and targeted pseudocode |
| IDA MCP bridge | Existing local multi-instance installation | API tool inventory retained; exact modified-bridge commit not exposed | Requests routed only to the newly opened EBOOT instance |
| `csvb.py` | `kimjh-eclipse` repository; commit author June | `d1e54c7b41b1165970f841c3de3fd7d86cc93bdc`, Apache-2.0 | Existing CSVB parsing implementation, unmodified |
| pyelftools | Eli Bendersky and contributors | 0.33; installed metadata identifies Public domain | ELF segment/header mapping |
| Capstone | Nguyen Anh Quynh and contributors | 5.0.7 | Existing PPC disassembler for TOC-reference recovery |
| Local scripts | Project-local research code | Source retained under `scripts/` | Read-only orchestration, evidence mining and cross-checking |

Primary tool sources: [scetool](https://github.com/naehrwert/scetool), [CSVB parser at the pinned commit](https://github.com/kimjh-eclipse/srw-og-infinite-battle-korean/blob/d1e54c7b41b1165970f841c3de3fd7d86cc93bdc/tools/csvb.py), [pyelftools](https://github.com/eliben/pyelftools), [Capstone](https://github.com/capstone-engine/capstone), and [Hex-Rays command-line documentation](https://docs.hex-rays.com/8.4/user-guide/configuration/command-line-switches).

The installed scetool executable has SHA-256 `bd9b55bb8a622bf254021598e9a04108330e94f375b411b6fb4a106b4980777c`. No unknown installed-tool commit is invented. The CSVB parser source hash is `bf78326fc8ae7cb886a7d864280ce03f1f694163bd4bfb04247beb9027d3ddd7`. Its upstream license and original files are retained. `analysis/tool-provenance.json` records installed-package metadata.

IDA's existing unrelated instance was left untouched. A separate research database was built, with its own MCP instance. The bridge truncates very long pseudocode responses, so requested functions were additionally exported locally from an isolated copy of the research IDB with IDAPython. This was a bounded export of investigated functions, not a whole-game decompilation. Original bytes were never patched.

## Reproduction

```powershell
# Run from the repository root.
$python = 'python'
$originalEboot = Join-Path $env:EUREKA_AO_USRDIR 'EBOOT.BIN'
& $python scripts\mine_roster_data.py
& $python scripts\mine_elf_roster.py
& $python scripts\audit_roster_mining.py --source-eboot $originalEboot
```

Set `EUREKA_AO_USRDIR` privately to the original game directory. The explicit `--source-eboot` input lets the audit compare the preserved research copy with the original read-only executable. The ELF must first exist. It was produced with the existing local scetool executable using `--decrypt analysis/EBOOT.BIN analysis/EBOOT.elf`, with absolute paths and the installed tool directory as its working directory. Existing local tool data was used; no key material is included in this report or copied into this research package.

IDA was run as a separate hidden background process with `-A`, a task-local `-L` log, and `-S` pointing at `scripts/ida_roster_triage.py`. A separate copied IDB was used by `scripts/ida_export_requested.py`, driven by `analysis/ida-export-request.json`. MCP query responses and targeted pseudocode are local under `analysis/ida/` and `analysis/decompiled/`; the audit reads these concrete records rather than relying on memory of a decompiler screen.

## What this audit does not prove

This is a strong static audit of the **delivered local build**, not a guarantee about every runtime detail. It does not exercise save-unlock progression, trace every procedural spawn, measure hidden debug-menu behavior, prove availability of an absent DLC/patch/build, or identify every effect-system mesh as a combat unit. Exact `ena2` variant naming and some NPC visual subtype names remain unresolved. No emulator session was started to fill those gaps.

The supported negative conclusion is: **no additional complete unit definition or unaccounted main-unit model was found beyond the 18 delivered definitions**. It is not an assertion that every byte or every possible game state has been understood.
