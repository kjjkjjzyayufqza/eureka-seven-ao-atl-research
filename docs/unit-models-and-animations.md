# Unit Models and Animation Inventory

Counts below come from the exported source data. Resource codes are stable identifiers; they are not all verified official character/form names. No comparison with ACE3 or another game's polygon counts has been performed in this extraction task.

Vertices are summed across glTF material primitives and can include duplicated boundary vertices. Primitives are material/geometry segments, not separately named Blender Mesh objects. Animation counts include loops, reactions, transitions and duplicate resources; they do not directly measure the number of unique attacks.

| Resource code | Vertices | Primitives | Skin joints | Clips | Local generated Blender file |
| --- | ---: | ---: | ---: | ---: | --- |
| `eall` | 39,422 | 22 | 131 | 40 | `playable/blend/Unit/eall/eall/eall_model.blend` |
| `eko1` | 3,506 | 2 | 6 | 38 | `playable/blend/Unit/eko1/eko1/eko1_model.blend` |
| `eko2` | 3,900 | 2 | 6 | 38 | `playable/blend/Unit/eko2/eko2/eko2_model.blend` |
| `eko3` | 7,258 | 1 | 7 | 38 | `playable/blend/Unit/eko3/eko3/eko3_model.blend` |
| `eko4` | 5,462 | 1 | 9 | 37 | `playable/blend/Unit/eko4/eko4/eko4_model.blend` |
| `ekyr` | 32,178 | 13 | 47 | 43 | `playable/blend/Unit/ekyr/ekyr/ekyr_model.blend` |
| `ekyr_missile` | 1,504 | 1 | 3 | 10 | `playable/blend/Unit/ekyr_missile/ekyr_missile/ekyr_missile_model.blend` |
| `ems1` | 23,838 | 18 | 63 | 42 | `playable/blend/Unit/ems1/ems1/ems1_model.blend` |
| `ems1_gun` | 1,436 | 1 | 1 | 0 | `playable/blend/Unit/ems1_gun/ems1_gun/ems1_gun_model.blend` |
| `ems1_missile_a` | 1,300 | 1 | 3 | 4 | `playable/blend/Unit/ems1_missile_a/ems1_missile_a/ems1_missile_a_model.blend` |
| `ems1_missile_b` | 1,300 | 1 | 3 | 4 | `playable/blend/Unit/ems1_missile_b/ems1_missile_b/ems1_missile_b_model.blend` |
| `ems2_laser` | 1,116 | 1 | 1 | 0 | `playable/blend/Unit/ems2_laser/ems2_laser/ems2_laser_model.blend` |
| `ena2` | 30,469 | 21 | 90 | 45 | `playable/blend/Unit/ena2/ena2/ena2_model.blend` |
| `enao` | 30,469 | 21 | 90 | 45 | `playable/blend/Unit/enao/enao/enao_model.blend` |
| `enao_gun` | 1,102 | 1 | 6 | 0 | `playable/blend/Unit/enao_gun/enao_gun/enao_gun_model.blend` |
| `ente` | 27,242 | 18 | 87 | 49 | `playable/blend/Unit/ente/ente/ente_model.blend` |
| `ente_laser_a` | 178 | 1 | 1 | 0 | `playable/blend/Unit/ente_laser_a/ente_laser_a/ente_laser_a_model.blend` |
| `ente_laser_b` | 178 | 1 | 1 | 0 | `playable/blend/Unit/ente_laser_b/ente_laser_b/ente_laser_b_model.blend` |
| `ente_sword` | 288 | 1 | 1 | 11 | `playable/blend/Unit/ente_sword/ente_sword/ente_sword_model.blend` |
| `enza` | 28,460 | 19 | 68 | 45 | `playable/blend/Unit/enza/enza/enza_model.blend` |
| `enza_knife_a` | 530 | 1 | 6 | 12 | `playable/blend/Unit/enza_knife_a/enza_knife_a/enza_knife_a_model.blend` |
| `enza_knife_b` | 530 | 1 | 6 | 12 | `playable/blend/Unit/enza_knife_b/enza_knife_b/enza_knife_b_model.blend` |
| `enze` | 28,460 | 19 | 68 | 45 | `playable/blend/Unit/enze/enze/enze_model.blend` |
| `enze_knife` | 152 | 1 | 1 | 0 | `playable/blend/Unit/enze_knife/enze_knife/enze_knife_model.blend` |
| `enze_knife_a` | 152 | 1 | 1 | 13 | `playable/blend/Unit/enze_knife_a/enze_knife_a/enze_knife_a_model.blend` |
| `enze_knife_b` | 152 | 1 | 1 | 12 | `playable/blend/Unit/enze_knife_b/enze_knife_b/enze_knife_b_model.blend` |
| `esc1` | 10,995 | 8 | 9 | 42 | `playable/blend/Unit/esc1/esc1/esc1_model.blend` |
| `esc3` | 12,358 | 3 | 0 | 0 | `playable/blend/Unit/esc3/esc3/esc3_model.blend` |
| `eter` | 34,582 | 28 | 69 | 50 | `playable/blend/Unit/eter/eter/eter_model.blend` |
| `etes` | 44,345 | 26 | 27 | 46 | `playable/blend/Unit/etes/etes/etes_model.blend` |
| `etes_missile_a` | 368 | 1 | 4 | 7 | `playable/blend/Unit/etes_missile_a/etes_missile_a/etes_missile_a_model.blend` |
| `etes_missile_b` | 368 | 1 | 4 | 6 | `playable/blend/Unit/etes_missile_b/etes_missile_b/etes_missile_b_model.blend` |

These paths describe local generated outputs. The repository does not include Blender files or other game assets.

## Nirvash resources

`enao` is the AO Nirvash mesh observed in the Blender preview. `ena2` has the same exported geometry counts but remains separately exported; do not rename it to 'spec2' based only on its code. `enze` and `enza` are the related ZERO resources, and `ente` is the theEND resource. Official variant labels for `ena2` and `enza` remain unconfirmed.

The AO `enao` mesh has 12,497 exported triangles. It has 21 primitives in one glTF mesh and 90 skin joints. Blender may split the glTF primitives into multiple Mesh objects; neither that count nor primitive-summed vertices should be compared to a welded topology count without normalization.

## AO Nirvash clip timing

Source times are preserved in seconds. Key gaps describe the authored curve, not the rendered game frame rate. No motion smoothing or resampling was applied. The complete per-unit and per-clip timing data are in `manifests/unit-animation-catalog.json`.

| Clip | Duration, seconds | TRS channels | Median variable-key gap, seconds |
| --- | ---: | ---: | ---: |
| `ATKF10N` | 0.133331 | 192 | 0.066666 |
| `ATKF11N` | 0.266663 | 192 | 0.066666 |
| `ATKF30N` | 0.133331 | 192 | 0.066666 |
| `ATKF31N` | 0.266663 | 192 | 0.066666 |
| `ATKL20N` | 0.133331 | 192 | 0.066666 |
| `ATKL21N` | 0.266663 | 192 | 0.066666 |
| `ATKR20N` | 0.133331 | 192 | 0.066666 |
| `ATKR21N` | 0.266663 | 192 | 0.066666 |
| `DMBB00N` | 1.133316 | 180 | 0.066666 |
| `DMBB01L` | 1.333328 | 180 | 0.033333 |
| `DMBB02N` | 1.133316 | 180 | 0.066666 |
| `DMBB03N` | 0.933319 | 180 | 0.066666 |
| `DMBB04N` | 1.333313 | 180 | 0.066666 |
| `DMBF00N` | 0.933319 | 180 | 0.066666 |
| `DMBF01L` | 1.333328 | 180 | 0.033333 |
| `DMBF02N` | 1.133316 | 180 | 0.066666 |
| `DMBF03N` | 0.933319 | 180 | 0.066666 |
| `DMBF04N` | 1.333313 | 180 | 0.066666 |
| `DMMB00N` | 0.933319 | 180 | 0.066666 |
| `DMMB01L` | 0.833328 | 180 | 0.033333 |
| `DMMB02N` | 1.133316 | 180 | 0.066666 |
| `DMMF00N` | 0.933319 | 180 | 0.066666 |
| `DMMF01L` | 0.833332 | 180 | 0.033333 |
| `DMMF02N` | 1.133316 | 180 | 0.066666 |
| `DMSB00N` | 0.933319 | 180 | 0.066666 |
| `DMSF00N` | 0.933319 | 180 | 0.066666 |
| `DSHF00L` | 2.000027 | 192 | 0.066668 |
| `DSHL00L` | 1.333351 | 192 | 0.066668 |
| `DSHL01L` | 1.000010 | 192 | 0.066668 |
| `DSHR00L` | 1.333313 | 192 | 0.066666 |
| `DSHR01L` | 0.999985 | 192 | 0.066666 |
| `MOVF00L` | 2.000000 | 180 | 0.066667 |
| `MOVL00L` | 1.333332 | 192 | 0.066667 |
| `MOVL01L` | 0.999999 | 192 | 0.066667 |
| `MOVR00L` | 1.333332 | 192 | 0.066667 |
| `MOVR01L` | 0.999999 | 192 | 0.066667 |
| `MSMF01L` | 0.133331 | 192 | 0.066666 |
| `POSE000N` | 0.066667 | 289 | constant / none |
| `QTN000N` | 0.866653 | 180 | 0.066666 |
| `SPF000N` | 5.999995 | 180 | 0.066667 |
| `SPF001N` | 3.333330 | 180 | 0.066667 |
| `TRKD00N` | 0.799988 | 192 | 0.066666 |
| `TRKL00N` | 0.799988 | 192 | 0.066666 |
| `TRKR00N` | 0.799988 | 192 | 0.066666 |
| `TRKU00N` | 0.799988 | 192 | 0.066666 |

## Playback and naming limits

The filename prefixes suggest attack (`ATK`), movement (`MOV`), dash (`DSH`), damage/reaction (`DM`) and special (`SPF`) groups, but these are filename interpretations rather than a decoded command/state system. Short fragments may need game-side sequencing to reproduce a complete move. Animation-only camera packs are retained under `playable/blend-auxiliary/`. All remaining model scenes, including maps and 2D UI geometry, are indexed in `manifests/playable-assets.json`.
