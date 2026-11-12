# IL ROTOLO DI PLURIBALL — dal file del generatore (assets/models/pluriball/src/, OBJ da 190 MB, 2 milioni di
# triangoli, in Git LFS) al GLB leggero che usa il gioco: un pezzo solo, alleggerito, del materiale resta il colore.
# Origine al centro del rotolo, +Y in alto (convenzione GLB).
#
# uso: blender -b --python tools/pluriball/modello_rotolo.py -- <obj> <cartella uscita> [triangoli, default 40000] [nome, default rotolo] [copia]
# copia: se l'OBJ contiene più copie del modello in pose diverse (come il pony: 4 viste in una griglia), il numero d'ordine della
# copia da tenere, dalla più pesante (0) alla più leggera; vedi tools/pluriball/componenti.py
# (vale per qualunque OBJ del generatore da alleggerire: con nome «pony» esce pony.glb, il protagonista avvolto)
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'boss'))
import viste
a = sys.argv[sys.argv.index('--') + 1:]
src, out = os.path.abspath(a[0]), os.path.abspath(a[1]); TRI = int(a[2]) if len(a) > 2 else 40000
NOME = a[3] if len(a) > 3 else 'rotolo'
COPIA = int(a[4]) if len(a) > 4 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=src)
ob = bpy.context.selected_objects[0]; me = ob.data
bpy.context.view_layer.objects.active = ob
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)       # ora Z in alto
if COPIA is not None:                                                           # tengo una sola delle copie
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    parti = sorted([o for o in bpy.data.objects if len(o.data.vertices) > 2000], key=lambda o: -len(o.data.vertices))
    for i, o in enumerate(parti):
        if i != COPIA: bpy.data.objects.remove(o)
    ob = parti[COPIA]; me = ob.data
ob.name = NOME.capitalize()
me.calc_loop_triangles(); n0 = len(me.loop_triangles)
m = ob.modifiers.new('r', 'DECIMATE'); m.ratio = min(1, TRI / n0); bpy.ops.object.modifier_apply(modifier='r')
v = np.array([w.co[:] for w in me.vertices]); c = (v.min(axis=0) + v.max(axis=0)) / 2
me.transform(Matrix.Translation(-c))                                            # centrato
me.validate(); me.update()
for p in me.polygons: p.use_smooth = True
mt = me.materials[0]; b = next(n for n in mt.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
# la mappa del rilievo resta (1024): è lei che dà le bolle, la geometria alleggerita non le ha più
for nome, val in (('Metallic', 0.0), ('Roughness', 0.25)):
    for l in list(b.inputs[nome].links): mt.node_tree.links.remove(l)
    if val is not None: b.inputs[nome].default_value = val
for n in list(mt.node_tree.nodes):
    if n.type == 'TEX_IMAGE' and not n.outputs[0].links and not n.outputs[1].links: mt.node_tree.nodes.remove(n)
    elif n.type == 'TEX_IMAGE' and n.image: n.image.scale(1024, 1024); n.image.pack()
me.calc_loop_triangles(); print('RISULTATO triangoli', n0, '->', len(me.loop_triangles))
lo, hi = viste.ingombro([ob]); print('RISULTATO ingombro (Z in alto): x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f' % (lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))
os.makedirs(out, exist_ok=True); glb = os.path.join(out, NOME + '.glb')
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_apply=True, export_yup=True, export_image_format='JPEG', export_jpeg_quality=85, export_animations=False)
print('RISULTATO glb %.2f MB' % (os.path.getsize(glb) / 1e6))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, NOME + '.blend'))
viste.scena_base(res=(640, 640), fondo=(0.55, 0.62, 0.7))
viste.foglio(os.path.join(out, NOME + '-viste.png'), [ob], viste=((0.8, -0.8, 0.5), (0, -1, 0.05), (1, 0, 0.05), (0, 0.01, 1)), colonne=2, margine=0.85)
