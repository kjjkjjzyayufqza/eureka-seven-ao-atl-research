# Final Validation and Known Limits

Final asset-audit result: **passed**, using **Blender 5.1.2**, build `ec6e62d40fa9`. The authoritative machine-readable result is `manifests/delivery-audit.json`; the original console record `delivery-audit.log` is now archived outside the project. Generated evidence and asset outputs are local and excluded from Git.

## Coverage

| Check | Result |
| --- | ---: |
| CPK containers including the root | 528 |
| Extracted entries rechecked against original extraction SHA-256 | 4,376 |
| Collada-origin Phyre scene clusters converted | 1,301 / 1,301 |
| Mesh-bearing model scenes | 495 |
| Unit/weapon model resources within those scenes | 32 |
| Separate auxiliary animation scenes | 72 |
| Final Blender scenes reopened successfully | 567 / 567 |
| Source animation clips represented in saved scenes | 1,229 |
| Clips with measured mesh movement in the sampling pass | 873 |
| Source variable plus constant animation channels | 74,860 |
| Standard glTF transform channels | 73,392 |
| Supplemental native parameter channels | 1,468 |
| Native parameter values checked after reopening/NLA selection | 4,324 |
| Maximum error in those reloaded native-key checks | 0.0 |
| Decoded scene-pack 2D texture resources | 1,087 |
| Packed Blender image byte streams checked against corrected PNGs | 1,077 |

`73,392 + 1,468 = 74,860`: no identified source animation channel is left unaccounted for. The audit checks this equality **per source file**, not just as a global total. It also verifies that the pinned Julian Uy upstream source remains unmodified.

The 495 scenes include map and UI geometry, not 495 playable mecha. The 1,229 clips include UI, cameras, transitions, reactions and duplicated resources, not 1,229 distinct attacks. Static resources and parameter-only clips legitimately show no mesh movement. The image counts use different populations: decoded texture resource files versus image instances packed into model scenes.

## What was actually exercised

The initial Blender batch imported every assembled GLB, selected each unique NLA clip across all objects, and sampled up to nine evenly spaced integer frames. It evaluated the dependency graph and actual mesh vertices, checked finite values, and measured world-space movement and local deformation. Approximately 128 vertices per mesh were sampled for this playback measurement; it is not an exhaustive numerical comparison of every vertex at every instant. Reports are in `manifests/blender-scenes/` and `manifests/blender-shard-{0,1,2}.json`.

Native parameter import compared every authored key against the evaluated Blender property before saving. Final delivery auditing then reopened all 567 saved scenes, checked clip counts, embedded native JSON and packed texture bytes, and compared first/middle/last source keys through the saved NLA tracks. The final scene audit thus checks saved-file behavior, not just transient importer state.

Final previews of AO Nirvash, ZERO and theEND were visually inspected after the RSX texture correction. Armor panel edges, face details, accent colors and board markings align with the mesh. These are Blender preview materials, not screenshots of the original renderer.

## Corrective evidence

The chronology and local JSON reports retain these corrected first-pass issues; historical console logs are archived outside the repository:

- Three UI cluster failures were resolved by packed-pixel decoding and the small texture layout repair.
- A first Blender pass reported 231 missing actions for clips containing only native parameters. Supplemental camera/material/user-property actions resolved them.
- Three preview attempts needed an explicit World in factory-empty scenes.
- Visual inspection caught texture corruption that successful mesh import could not detect. Final texture layouts use the native RSX linear bit and X-first Morton order. A separate RGB565 correction covers three map textures.
- Final reopen testing caught integer truncation when native NLA strips were created from float32 source times. `repair_native_nla.py` inspected 964 parameter strips and corrected bounds in 12 scenes. The importer now restores fractional strip bounds immediately. The final reopened-key audit passed with zero measured error.

The per-scene first-pass reports can retain pre-correction strip-bound measurements in those 12 scenes; `manifests/native-nla-timing-repair.json` records the exact corrections, and the final delivery audit is the authority for saved-file timing.

## Provenance and source integrity

The original CPK still hashes to `05a38cef8f3cf9c3036d51d1ea8d624c36e38886e9ead8d237faea886afd7683`. Every extracted entry was re-hashed against its extraction manifest. Original game files were not edited and RPCS3 was not operated. Executable analysis was unnecessary for this asset-validation pass; the user's subsequent roster request led to a separate read-only EBOOT investigation, documented in [eboot-roster-data-mining.md](eboot-roster-data-mining.md). No assets were published, committed or pushed.

The audit records every local Python script's SHA-256 and the pinned upstream revision. See [tools-and-attribution.md](tools-and-attribution.md) for authors, tools, versions, source links and attribution limits.

## Fidelity and scope limits

- All identified Phyre mesh/skin/TRS and supplemental native animation channels are represented. Original shader microcode and render-state behavior are not recreated by Blender's standard material system.
- Material transparency/color bindings are explicit preview approximations. Camera FOV uses a documented vertical-angle convention; the complete native projection behavior has not been proven against the original renderer.
- Generic user-attribute curves remain animated, inspectable custom properties. Their engine-side effects are not invented.
- Game-side command scripts, animation chaining, hit detection, procedural targeting, effects, audio synchronization and UI compositing remain raw extracted resources.
- Seventeen `Lip/*.pkg` files remain preserved but semantically undecoded; no Blender facial/lip-sync action is claimed for them. A future request to reconstruct that separate system would require additional format research.
- The 60 FPS Blender timeline preserves source seconds. No interactive Blender FPS benchmark or cross-game animation-quality comparison was performed. Original sparse keys and separate move fragments are retained rather than synthesized into smoother new motion.
- Variant names for `ena2` and `enza` remain unconfirmed. Resource codes and separate outputs are preserved to avoid mislabeling.
