# Reproduction and Blender 5.1 Playback

## Environment

Run PowerShell in the research directory. Use Python 3.11 on PATH. Set `BLENDER_51` locally to the Blender 5.1 executable and `EUREKA_AO_USRDIR` locally to your original game's USRDIR directory. Keep those private environment values outside Git. A clean clone contains no game inputs or generated outputs; supply the original archive separately and run extraction first. The tested Python is CPython 3.11.4 with PyCriCodecs 0.4.11 and Pillow 12.3.0 already installed. The included pinned minimal `ed8pkg2glb` source snapshot is described in [tools-and-attribution.md](tools-and-attribution.md). The production Blender executable reports **5.1.2**, build hash `ec6e62d40fa9`.

```powershell
$python = 'python'
$blender = $env:BLENDER_51
$gameArchive = Join-Path $env:EUREKA_AO_USRDIR 'EurekaAODataR.cpk'
# Run the commands from the repository root.
```

## Extraction and conversion

```powershell
& $python scripts\extract_archives.py $gameArchive
& $python scripts\convert_all.py --workers 4
& $python scripts\prepare_playback.py
& $python scripts\export_parameters.py
& $python scripts\refresh_textures.py
& $python scripts\build_catalog.py
```

`extract_archives.py` requires an explicit input archive path and has no workstation-specific default. It will not replace an extracted file with different bytes. Conversion writes only inside this research directory. `convert_all.py` reuses successful manifest records; `--retry-failed --refresh-models` was used during the initial UI/material repair. The supplemental texture pass force-decodes scene-pack textures using the corrected RSX layout selection and refreshes the PNG copies beside assembled GLBs.

## Create and verify every Blender scene

Run each shard once, in separate terminal sessions if desired:

```powershell
& $blender --background --factory-startup --python scripts\blender_batch.py -- --shard 0 --shards 3
& $blender --background --factory-startup --python scripts\blender_batch.py -- --shard 1 --shards 3
& $blender --background --factory-startup --python scripts\blender_batch.py -- --shard 2 --shards 3
```

Blender's executable can return success even when an embedded Python script raises an exception. Consult the JSON shard results and logs, not the exit code alone. `--repair` restricts a corrective run to parameter-bearing scenes and previous failures. It is not needed for a clean reproduction.

The actual research sequence discovered the RSX texture issue after the first scenes were saved. Existing scenes were therefore refreshed without rebuilding their unchanged actions:

```powershell
& $blender --background --factory-startup --python scripts\blender_refresh_textures.py -- --shard 0 --shards 3
& $blender --background --factory-startup --python scripts\blender_refresh_textures.py -- --shard 1 --shards 3
& $blender --background --factory-startup --python scripts\blender_refresh_textures.py -- --shard 2 --shards 3
```

On a fresh run using corrected textures before Blender import, that refresh is unnecessary. The original first-probe files under `converted/enao/` and `previews/enao-probe.png` predate the Blender 5.1 requirement and are historical artifacts. Use the `playable/` deliverables.

During corrective work, `refresh_textures.py --rsx-only` and `--format RGB565` restricted decoding to changed layouts; the same options on `blender_refresh_textures.py` restricted repacking to affected model folders. These are recovery paths, not additional steps required after a clean conversion.

`repair_native_nla.py` was used once to correct fractional strip bounds in previously saved parameter scenes. The current importer already applies this fix. The repair manifest records 12 changed scenes; a clean reproduction does not need that recovery step.

The final semantic delivery audit runs with:

```powershell
& $blender --background --factory-startup --python scripts\audit_delivery.py
```

Its successful result is `manifests/delivery-audit.json`. Capture and inspect console output during a new run: a Python exception is a failure even if Blender's process exit code is zero. The original `delivery-audit.log` was moved to the external historical-log archive during cleanup.

## Select and play actions

1. Open the desired `playable/blend/.../*.blend` in Blender 5.1.
2. Press Space. The selected clip and its frame range are already configured. AO Nirvash defaults to `MOVF00L`.
3. For another clip, switch an editor to Text Editor and select the embedded `Select_Animation.py`.
4. Set `CLIP = "ATKF10N"`, for example, or set the Scene `selected_clip` custom property and use the existing assignment.
5. Run Script. Press Space again.

The script mutes every other NLA track across all objects. Selecting an Action only on the armature can omit animation on independent control nodes or material/camera parameter objects. Do not unmute all clips simultaneously.

Each parameter-bearing scene also contains `Native_Parameters.json`, preserving source target names, interpolation codes, times in seconds and scalar/vector values. `NativeParameters::...` Empty objects hold corresponding custom-property F-curves. Their tracks switch with the skeletal tracks. Some scenes are intentionally static; auxiliary camera scenes intentionally have no meshes.

## Time and motion fidelity

The conversion retains original timestamps and quaternion/translation/scale values; it does not generate additional motion detail. The Blender scene uses 60 FPS to express source seconds as frames. Observed AO Nirvash variable-key gaps are mostly approximately 1/15 and 1/30 second. Those gaps describe authored key spacing, not the game's render rate. Linear or step interpolation follows the existing exporter (`m_interp == 2` becomes step). A displayed 60 FPS timeline does not establish that the source contains 60 independently authored poses per second.

Short attack fragments, loops and transition clips remain separate. Filename groups such as `ATK`, `MOV`, `DSH`, `DM` and `SPF` are useful browsing hints, but are not a fully reverse-engineered move-command graph. Game-side attack chaining, hitboxes, procedural targeting, effects and state transitions have not been recreated.

## Standalone GLB use

Standard mesh, skin and TRS animation data are in `playable/glb/`. Keep referenced PNGs beside each GLB. A plain glTF import does not interpret the adjacent `.glb.parameters.json` file; use the supplied Blender script to add those native curves or open the saved `.blend`. Some source clips contain only native parameters and no TRS channels, so a plain glTF importer will not create an action for those clips.
