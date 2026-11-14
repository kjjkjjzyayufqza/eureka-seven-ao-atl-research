# Playable Units, Variants and Non-player Resources

Research date: 2026-11-14. Source build: PS3 BLJS93011, application 01.00. Follow-up executable/data mining is documented in [eboot-roster-data-mining.md](eboot-roster-data-mining.md); that report supersedes the original uncertainty about the AO alternate's selectability.

## Counting convention

The roster supports **seven named playable unit types / eight selectable configurations**. The local unit-resource table contains **18 definitions**: eight player definitions including a second AO Nirvash configuration, followed by ten non-player definitions. Follow-up EBOOT analysis confirms an unlock-gated 0/1 AO toggle and selection confirmation. The AO alternatives share a navigation position; eight configurations should not be advertised as eight unrelated mecha.

The ten non-player definitions resolve to eight unique main-model archives. Across all 18 definitions there are 16 unique main-model archives. Weapon/projectile models and special cameras are not additional units. The previously reported 32 Unit-category model resources include those weapons/projectiles.

## Playable roster

| Named unit type | Resource | Pilot / source | Notes |
| --- | --- | --- | --- |
| RA272 Nirvash | `enao`, additional `ena2` | Ao / Eureka Seven AO | Two selectable configurations under an unlock condition, one named unit type. The exact official variant subtitle remains unconfirmed. It is not evidence of type ZERO spec2. |
| RA164 Alleluia | `eall` | Fleur / Eureka Seven AO | Player-associated resource |
| RA301 Kyrie | `ekyr` | Elena / Eureka Seven AO | Player-associated resource |
| Nirvash type ZERO, TV version | `enze` | Eureka and Renton / TV series | Separate from the film resource |
| Nirvash type theEND | `ente` | Anemone / TV series | Unlockable; the trophy guide explicitly reports unlocking Anemone after all eight Single Missions |
| Terminus type B303 Devilfish | `eter` | Holland / TV series | Do not label this resource R909 merely from the `ter` abbreviation |
| Nirvash type ZERO, film version | `enza` | Renton / Pocketful of Rainbows | Association follows the public film roster and corresponding character-resource order |

The official site lists the principal units and explains that clearing missions unlocks additional units. It does not give a definitive numerical total or prove every internal definition is a menu entry. The seven-type total is a roster reconciliation, not a quoted official numeric claim.

## Non-player-associated definitions

| Definition(s) | Count | Interpretation / evidence |
| --- | ---: | --- |
| `etes` | 1 | Devilfish S boss resource; the published film-situation mission list names Devilfish S as the final enemy |
| `ems1`, `ems2` | 2 | Monsuno MS10 / MS20 definitions; both explicitly reference `Unit/ems1.cpk`, with different weapon attachments |
| `eko1`, `eko2`, `eko3`, `eko4` | 4 | Antibody Coralian resource family; four separately animated main models |
| `esc1`, `esc2`, `esc3` | 3 | Secret-related resource family. `esc2` explicitly references `Unit/esc1.cpk`. `esc3` has its own unskinned main model and is an enemy-slot entry in the three AO story finales and Tag Mission 3; its exact official subtype name remains unconfirmed. |
| Total | **10** | Eight unique main-model archives because two definitions share models |

Non-player classification now also has EBOOT selection-range and complete stage-preset evidence. All ten non-player IDs occur in delivered stage presets. No emulator session was operated to test unlock progression, debug selection or every procedural spawn. A mod that forces a unit to be controllable would not make it officially playable.

## Local primary evidence

`extracted/nested/root/LevelDesign/ActCommon.cpk.unpacked/UnitResource.prm` has signature `CSVBv4.3`. The observed single-table header stores 18 rows at `0x34`, row stride `0x154` at `0x38`, row-data start `0x48`, and string-pool offset `0x199C` from header word `0x10`. In each row, uint32 words 58, 59 and 60 hold string-pool-relative references to the unit code, main-model archive and action-command file. Values are big-endian. The header's 91 entries at `0x3C` describe field metadata, not 91 playable units.

The bounded inspection is recorded in `manifests/unit-resource-rows.json`. It reads only these observed fields; no generic CSVB decoder or executable analysis was implemented. The local Python inspection code uses Python's standard `struct` and `json` modules. No external CSVB parser code was copied.

`CharResource.prm` contains eight rows, stride `0x5C`, data start `0x48`, string-pool offset `0x384`. Its voice resources are, in order, `CAO1`, `CAO2`, `CFLR`, `CELN`, `CEUR`, `CANM`, `CHLD`, `CRTN`. The first eight UnitResource entries are `enao`, `ena2`, `eall`, `ekyr`, `enze`, `ente`, `eter`, `enza`. EBOOT `sub_1F4058` and its input-handler callers establish the AO alternate's actual selection path. The first 58 uint32 words of the `enao` and `ena2` unit rows are identical; their named model/action resources differ.

`esc3` was additionally rendered in Blender 5.1.2 to inspect its standalone static geometry (`previews/esc3-roster-blender51.png`). Appearance alone was not used to assign an unverified official name or to call it the Scub Coral protection target.

## Sources and conflicting claims

- [Bandai Namco official game page](https://www.bandainamcoent.co.jp/cs/list/eurekaao/sp/sp_game.html): primary unit descriptions and unlock-based mission mode. The search index exposes its text; direct page opening returned HTTP 403 during this research.
- [4Gamer's reproduced publisher announcement](https://www.4gamer.net/games/171/G017134/20120703009/): situation mission opponents include Monsuno MS10/MS20, Antibody Coralians, Secret/Option and Devilfish S. This is publisher-supplied promotional information, not a complete internal roster.
- [PlayStationTrophies guide](https://www.playstationtrophies.org/game/eureka-seven-ao-attack-of-the-legend/guide/), including the [all Single Missions trophy entry](https://www.playstationtrophies.org/game/eureka-seven-ao-attack-of-the-legend/trophy/52793-.html): firsthand gameplay guidance explicitly states that clearing all eight Single Missions unlocks Anemone. Direct full-guide opening returned HTTP 403; indexed guide/trophy text was available.
- A player blog search result complained that theEND could not be used. That conflicts with the explicit unlock guide and was not treated as proof that theEND is enemy-only. The distinction between locked and permanently unplayable matters here.

Public descriptions, static data and executable selection code support the seven-type/eight-configuration roster above. The AO variant's official subtitle, detailed labels of all four Coralian models and the exact official name/all runtime behavior of `esc3` remain unresolved. See the follow-up report for the 106-file/44-stage audit and code addresses.
