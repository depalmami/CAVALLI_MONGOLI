# Importa la testa (OBJ da 1,9 M di triangoli), la alleggerisce e salva un .blend leggero + un foglio di viste.
# uso: blender -b --python prep_testa.py -- <obj> <blend out> <png out> [triangoli]
import bpy, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import viste

src, dst_blend, dst_png = sys.argv[sys.argv.index('--') + 1:][:3]
bersaglio = int((sys.argv[sys.argv.index('--') + 1:] + ['60000'])[3])

bpy.ops.wm.read_factory_settings(use_empty=True)
t = time.time()
bpy.ops.wm.obj_import(filepath=src)
ob = bpy.context.selected_objects[0]
ob.name = 'Testa'
me = ob.data
me.calc_loop_triangles()
n0 = len(me.loop_triangles)
print('importato in %.1fs · triangoli %d · dimensioni %s' % (time.time() - t, n0, tuple(round(v, 3) for v in ob.dimensions)))

t = time.time()
bpy.context.view_layer.objects.active = ob
m = ob.modifiers.new('riduci', 'DECIMATE'); m.ratio = min(1, bersaglio / n0)
bpy.ops.object.modifier_apply(modifier='riduci')
me.calc_loop_triangles()
print('ridotto in %.1fs · triangoli %d' % (time.time() - t, len(me.loop_triangles)))
for p in me.polygons: p.use_smooth = True
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
print('dimensioni finali', tuple(round(v, 3) for v in ob.dimensions), 'origine', tuple(round(v, 3) for v in ob.location))

viste.scena_base()
viste.foglio(dst_png, [ob], viste=('trequarti', 'lato', 'fronte', 'alto', 'dietro34', 'sotto34'), colonne=3)
bpy.ops.wm.save_as_mainfile(filepath=dst_blend)
print('salvato', dst_blend)
