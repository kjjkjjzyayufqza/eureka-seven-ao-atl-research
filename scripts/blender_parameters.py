"""Import preserved native parameter curves into Blender 5.1 custom properties.

Camera FOV also drives a perspective camera. Known material properties drive a
documented preview approximation; original values remain directly inspectable.
"""

import json
import math
from pathlib import Path

import bpy


def driver(socket, path, owner, prop, index=None, expression="v"):
    curve = socket.driver_add(path) if index is None else socket.driver_add(path, index)
    curve.driver.expression = expression
    variable = curve.driver.variables.new()
    variable.name = "v"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id = owner
    variable.targets[0].data_path = '["' + prop + '"]' + (f"[{index}]" if index is not None else "")


def bind_preview(owner, channel, prop, scene):
    target = channel["target_name"]
    if channel["key_type"] == "CameraFov":
        data = bpy.data.cameras.new((target or "NativeCamera") + "_Perspective")
        camera = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(camera)
        camera.parent = scene.objects.get(target) if target else None
        data.sensor_fit = "VERTICAL"
        data.sensor_height = 24
        data.clip_start = max(channel["camera"].get("m_nearPlane", 0.1), 0.0001)
        data.clip_end = channel["camera"].get("m_farPlane", 10000)
        driver(data, "lens", owner, prop, expression="12.0/tan(max(0.0001,v)/2.0)")
        scene.camera = camera
        return "camera_lens_from_vertical_fov_radians"
    material = bpy.data.materials.get(target) if target else None
    if not material or not material.node_tree:
        return "custom_property_only"
    shader = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        return "custom_property_only"
    tree = material.node_tree
    if prop == "Transparency":
        socket = shader.inputs["Alpha"]
        if socket.is_linked:
            previous = socket.links[0].from_socket
            multiply = tree.nodes.new("ShaderNodeMath")
            multiply.operation = "MULTIPLY"
            tree.links.new(previous, multiply.inputs[0])
            driver(multiply.inputs[1], "default_value", owner, prop)
            tree.links.new(multiply.outputs[0], socket)
        else:
            driver(socket, "default_value", owner, prop)
        material.surface_render_method = "DITHERED"
        return "preview_alpha_multiplier"
    if prop == "MaterialColour":
        socket = shader.inputs["Base Color"]
        multiply = tree.nodes.new("ShaderNodeMixRGB")
        multiply.blend_type = "MULTIPLY"
        multiply.inputs[0].default_value = 1
        if socket.is_linked:
            tree.links.new(socket.links[0].from_socket, multiply.inputs[1])
        else:
            multiply.inputs[1].default_value = socket.default_value
        for index in range(4):
            driver(multiply.inputs[2], "default_value", owner, prop, index=index)
        tree.links.new(multiply.outputs[0], socket)
        return "preview_base_color_multiplier"
    return "custom_property_only"


def import_parameters(glb, scene):
    sidecar = Path(str(glb) + ".parameters.json")
    if not sidecar.is_file():
        return []
    text = bpy.data.texts.new("Native_Parameters.json")
    text.write(sidecar.read_text(encoding="utf-8"))
    data = json.loads(text.as_string())
    owners = {}
    mappings = {}
    reports = []
    for clip in data["clips"]:
        touched = set()
        for channel in clip["channels"]:
            key = (clip["source"], channel["target_class"], channel["target_location"])
            if key not in owners:
                owner = bpy.data.objects.new("NativeParameters::" + (channel["target_name"] or str(channel["target_location"])), None)
                scene.collection.objects.link(owner)
                owner["native_source"] = clip["source"]
                owner["native_target_class"] = channel["target_class"]
                owners[key] = owner
            owner = owners[key]
            prop = channel["property"]
            dimensions = len(channel["values"][0])
            owner[prop] = channel["values"][0][0] if dimensions == 1 else channel["values"][0]
            path = '["' + prop + '"]'
            points = sorted(zip(channel["times_seconds"], channel["values"]))
            for time, values in points:
                owner[prop] = values[0] if dimensions == 1 else values
                owner.keyframe_insert(data_path=path, frame=time * scene.render.fps, group="Native " + channel["key_type"])
            mapping_key = (key, prop)
            if mapping_key not in mappings:
                mappings[mapping_key] = bind_preview(owner, channel, prop, scene)
            # keyframe_insert creates a slotted Action in Blender 5.1.
            action = owner.animation_data.action
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            if curve.data_path == path:
                                for point in curve.keyframe_points:
                                    point.interpolation = "CONSTANT" if channel["interpolation_code"] == 2 else "LINEAR"
            error = 0.0
            owner.update_tag(refresh={"OBJECT"})
            bpy.context.view_layer.update()
            for time, expected in points:
                scene.frame_set(int(math.floor(time * scene.render.fps)), subframe=(time * scene.render.fps) % 1)
                actual = owner[prop]
                actual = [actual] if dimensions == 1 else list(actual)
                error = max(error, max(abs(a - b) for a, b in zip(actual, expected)))
            if not math.isfinite(error) or error > 0.002:
                raise ValueError(f"Native parameter curve mismatch: {clip['name']} {prop}: {error}")
            reports.append({
                "clip": clip["name"], "target": channel["target_name"], "property": prop,
                "key_type": channel["key_type"], "mapping": mappings[mapping_key],
                "key_count": len(points), "max_key_error": error,
            })
            touched.add(owner)
        for owner in touched:
            animation = owner.animation_data
            action = animation.action
            action.name = clip["name"] + "_NativeParameters"
            slot = animation.action_slot
            animation.action = None
            track = animation.nla_tracks.new()
            track.name = clip["name"]
            strip = track.strips.new(clip["name"], int(action.frame_range[0]), action)
            strip.action_slot = slot
            # NLA strips.new takes an integer start; restore the original
            # fractional key bounds so float32 source times cannot shift a clip.
            strip.frame_start = float(action.frame_range[0])
            strip.frame_end = float(action.frame_range[1])
            strip.scale = 1.0
            track.mute = True
    return reports
