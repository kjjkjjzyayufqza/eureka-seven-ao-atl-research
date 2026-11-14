import sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path('scripts').resolve()))
from blender_parameters import import_parameters
bpy.context.scene.render.fps=60
p=Path('playable/glb/OutGame/alert_setting/alert_setting/alert_setting_all_animations.glb').resolve()
bpy.ops.import_scene.gltf(filepath=str(p))
try:import_parameters(p,bpy.context.scene)
except Exception as e:print('ERR',e)
for o in bpy.data.objects:
 if not o.name.startswith('NativeParameters'):continue
 a=o.animation_data; print('OBJ',o.name,dict(o.items()),'SLOT',a.action_slot, 'ACTION',a.action.name if a.action else None)
 if not a.action:continue
 for l in a.action.layers:
  for s in l.strips:
   for bag in s.channelbags:
    for f in bag.fcurves:print('FC',f.data_path,f.array_index,list(tuple(k.co) for k in f.keyframe_points)[:5],f.evaluate(0),f.evaluate(12))
 for t in (0,12,20,100):
  bpy.context.scene.frame_set(t);bpy.context.view_layer.update();print('VAL',t,o.get('Transparency'),o.evaluated_get(bpy.context.evaluated_depsgraph_get()).get('Transparency'))
