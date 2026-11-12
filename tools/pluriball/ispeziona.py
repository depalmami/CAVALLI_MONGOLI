# Misura un OBJ: triangoli, ingombro, componenti connesse (quante copie contiene).
import bpy, sys, numpy as np
src = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=src)
ob = bpy.context.selected_objects[0]; me = ob.data
co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
me.calc_loop_triangles()
print('RISULTATO tri', len(me.loop_triangles), 'vert', len(co), 'rot', tuple(round(x,3) for x in ob.rotation_euler), 'scala', tuple(ob.scale))
print('RISULTATO min', co.min(axis=0).round(3), 'max', co.max(axis=0).round(3))
for ax in range(3):
    h, e = np.histogram(co[:, ax], bins=10); print('RISULTATO asse', ax, h.tolist())
