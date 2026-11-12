# Viste pulite del protagonista (cavallo di cartone con le gambe) su fondo chiaro: servono come riferimento per un
# generatore image-to-3D (il modello avvolto nel pluriball). uso: blender -b assets/models/protagonista-cartone.blend --python <questo> -- <cartella>
import bpy, sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'boss'))
import viste
out = os.path.abspath(sys.argv[sys.argv.index('--') + 1]); os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
for a in list(bpy.data.actions): pass
print('RISULTATO oggetti', [(o.name, o.type) for o in bpy.data.objects])
for o in bpy.data.objects:
    if o.name.startswith('WGT'): o.hide_render = True; o.hide_viewport = True
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('WGT')]
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o)
viste.scena_base(res=(1024, 1024), fondo=(0.93, 0.93, 0.92))
# il protagonista guarda verso -Y in Blender
for nome, d in (('fronte', (0, -1, 0.12)), ('trequarti', (-0.75, -0.8, 0.3)), ('lato', (-1, 0, 0.1)), ('dietro', (0, 1, 0.12))):
    viste.inquadra(meshes, d, 0.95)
    sc.render.filepath = os.path.join(out, 'protagonista-%s.png' % nome); bpy.ops.render.render(write_still=True)
lo, hi = viste.ingombro(meshes); print('RISULTATO ingombro', lo, hi)
