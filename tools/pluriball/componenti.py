# Divide un OBJ del generatore nelle sue parti staccate e ne stampa l'ingombro (quante copie contiene, e dove).
import bpy, sys, numpy as np
src = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=src)
ob = bpy.context.selected_objects[0]; me = ob.data
bpy.context.view_layer.objects.active = ob
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
parts = []
for o in bpy.data.objects:
    v = np.array([w.co[:] for w in o.data.vertices])
    if len(v) > 2000: parts.append((len(v), v.min(axis=0).round(3).tolist(), v.max(axis=0).round(3).tolist(), o.name))
parts.sort(reverse=True)
for p in parts[:12]: print('RISULTATO', p)
