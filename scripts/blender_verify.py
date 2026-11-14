"""Import a GLB into a clean Blender scene and evaluate actual animated geometry.

Run with Blender --background --factory-startup --python scripts/blender_verify.py -- ...
"""

import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blender_parameters import import_parameters


def select_clip(name):
    for obj in bpy.data.objects:
        animation = obj.animation_data
        if animation is None:
            continue
        animation.action = None
        for track in animation.nla_tracks:
            track.mute = track.name != name


def evaluated_vertices(objects):
    graph = bpy.context.evaluated_depsgraph_get()
    result = []
    local_result = []
    for obj in objects:
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        try:
            if not mesh.vertices:
                continue
            step = max(1, len(mesh.vertices) // 128)
            for index in range(0, len(mesh.vertices), step):
                vertex = mesh.vertices[index].co.copy()
                local_result.append(tuple(vertex))
                result.append(tuple(evaluated.matrix_world @ vertex))
        finally:
            evaluated.to_mesh_clear()
    return result, local_result


def distance(left, right):
    return max((math.dist(a, b) for a, b in zip(left, right)), default=0.0)


def main():
    if bpy.app.version[:2] != (5, 1):
        raise RuntimeError("Final playback validation requires Blender 5.1")
    args = sys.argv[sys.argv.index("--") + 1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--render", type=Path)
    parser.add_argument("--allow-no-mesh", action="store_true")
    parsed = parser.parse_args(args)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.render.fps = 60
    bpy.ops.import_scene.gltf(filepath=str(parsed.source.resolve()))
    scene = bpy.context.scene
    parameter_report = import_parameters(parsed.source.resolve(), scene)
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    rigs = [obj for obj in scene.objects if obj.type == "ARMATURE"]
    tracks = sorted({
        track.name for obj in scene.objects if obj.animation_data
        for track in obj.animation_data.nla_tracks
    })
    report = {
        "source": str(parsed.source.resolve()),
        "blender": bpy.app.version_string,
        "fps": scene.render.fps,
        "meshes": len(meshes),
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "armatures": len(rigs),
        "bones": sum(len(obj.data.bones) for obj in rigs),
        "actions": len(bpy.data.actions),
        "tracks": tracks,
        "clips": [],
        "native_parameters": parameter_report,
    }
    if not meshes and not parsed.allow_no_mesh:
        raise RuntimeError("No meshes were imported")
    for clip in tracks:
        select_clip(clip)
        strips = [
            strip for obj in scene.objects if obj.animation_data
            for track in obj.animation_data.nla_tracks if track.name == clip
            for strip in track.strips
        ]
        start = min(strip.frame_start for strip in strips)
        end = max(strip.frame_end for strip in strips)
        samples = sorted({int(round(start + (end - start) * index / 8)) for index in range(9)})
        baseline_world = baseline_local = None
        movement = deformation = 0.0
        for frame in samples:
            scene.frame_set(frame)
            world, local = evaluated_vertices(meshes)
            if not all(math.isfinite(value) for point in world for value in point):
                raise RuntimeError(f"Non-finite evaluated vertex in {clip}")
            if baseline_world is None:
                baseline_world, baseline_local = world, local
            movement = max(movement, distance(baseline_world, world))
            deformation = max(deformation, distance(baseline_local, local))
        report["clips"].append({
            "name": clip, "start": start, "end": end, "sampled_frames": samples,
            "max_world_vertex_displacement": movement,
            "max_local_vertex_displacement": deformation,
            "geometry_moves": movement > 1e-6,
        })
    if tracks:
        default_clip = "MOVF00L" if "MOVF00L" in tracks else tracks[0]
        select_clip(default_clip)
        first = next(item for item in report["clips"] if item["name"] == default_clip)
        scene.frame_start = int(first["start"])
        scene.frame_end = max(scene.frame_start + 1, int(math.ceil(first["end"])))
        scene.frame_set(scene.frame_start)
        scene["selected_clip"] = default_clip
        scene["available_clips"] = "\n".join(tracks)
        text = bpy.data.texts.new("Select_Animation.py")
        text.write('''# Set CLIP to any name listed in Scene custom property available_clips.
import bpy
CLIP = bpy.context.scene.get("selected_clip", "MOVF00L")
strips = []
for obj in bpy.data.objects:
    if obj.animation_data:
        obj.animation_data.action = None
        for track in obj.animation_data.nla_tracks:
            track.mute = track.name != CLIP
            if not track.mute:
                strips.extend(track.strips)
if strips:
    scene = bpy.context.scene
    scene.frame_start = int(min(strip.frame_start for strip in strips))
    scene.frame_end = int(max(strip.frame_end for strip in strips) + 0.999)
    scene.frame_set(scene.frame_start)
    scene["selected_clip"] = CLIP
else:
    raise ValueError("Unknown animation clip: " + CLIP)
''')
    bpy.ops.file.pack_all()
    if parsed.render:
        points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
        lower = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
        upper = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
        center = (lower + upper) * 0.5
        radius = max((upper - lower).length * 0.55, 1.0)
        camera_data = bpy.data.cameras.new("ResearchPreviewCamera")
        camera = bpy.data.objects.new("ResearchPreviewCamera", camera_data)
        scene.collection.objects.link(camera)
        camera.location = center + Vector((1.3, -2.0, 0.8)).normalized() * radius * 2.3
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera_data.clip_end = radius * 20
        scene.camera = camera
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 16
        if scene.world is None:
            scene.world = bpy.data.worlds.new("ResearchPreviewWorld")
        scene.world.color = (0.3, 0.3, 0.3)
        light_data = bpy.data.lights.new("ResearchPreviewSun", "SUN")
        light_data.energy = 3.0
        light = bpy.data.objects.new("ResearchPreviewSun", light_data)
        scene.collection.objects.link(light)
        light.rotation_euler = (0.5, -0.4, -0.6)
        scene.render.resolution_x = 768
        scene.render.resolution_y = 768
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        parsed.render.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(parsed.render.resolve())
        bpy.ops.render.render(write_still=True)
    parsed.blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(parsed.blend.resolve()))
    parsed.report.parent.mkdir(parents=True, exist_ok=True)
    parsed.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("PLAYBACK_VERIFICATION", json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
