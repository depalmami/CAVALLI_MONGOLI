# LA BIRRA GRANDE — bicchiere di birra sui pattini in linea, da raccogliere lungo il tracciato.
#
# Il file del generatore (assets/models/birra/src/, OBJ da 183 MB, NON va in git) contiene QUATTRO copie identiche del
# bicchiere in una griglia 2x2: qui se ne tiene una, la si alleggerisce partendo dal modello pieno e la si divide in
# tre pezzi rigidi, così il gioco (3d/birra.js) può fare il passo del pattinatore senza scheletro:
#   Bicchiere  il bicchiere (con la schiuma)         origine all'altezza dei fianchi, in mezzo
#   PattinoS   gamba + pattino sinistro              origine all'anca
#   PattinoD   gamba + pattino destro                origine all'anca
# Assi in uscita: +X davanti (la punta dei pattini), +Z alto, 1 unità = 1 m. Nel GLB: +X davanti, +Y alto.
# Del materiale resta solo il colore (4096 → 1024): metallo, rugosità e rilievo pesavano 15 MB e a gioco non servono.
#
# uso: blender -b --python tools/boss/modello_birra.py -- <obj> <cartella uscita> [angolo di giro in gradi, default 90]
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import viste

a = sys.argv[sys.argv.index('--') + 1:]
src, out_dir = os.path.abspath(a[0]), os.path.abspath(a[1])
GIRO = math.radians(float(a[2])) if len(a) > 2 else math.radians(90)
TRIANGOLI = 28000
Z_ANCA = 0.134                         # sotto: gambe e pattini; sopra: il bicchiere (la base del bicchiere sta qui)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=src)
ob = bpy.context.selected_objects[0]; ob.name = 'Birra'; me = ob.data
# il mesh resta con Y in alto (l'oggetto porta la rotazione di 90°): per scegliere la copia uso le coordinate del mesh
co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
tieni = (co[:, 0] < 0) & (co[:, 1] < 0.49)                      # la copia in basso a sinistra della griglia
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v, t in zip(bm.verts, tieni) if not t], context='VERTS')
bm.to_mesh(me); bm.free()
v = np.array([w.co[:] for w in me.vertices]); c = (v.min(axis=0) + v.max(axis=0)) / 2
me.transform(Matrix.Translation((-c[0], -v.min(axis=0)[1], -c[2])))      # centrato, pattini a terra
me.calc_loop_triangles(); n0 = len(me.loop_triangles)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
m = ob.modifiers.new('r', 'DECIMATE'); m.ratio = min(1, TRIANGOLI / n0)
bpy.ops.object.modifier_apply(modifier='r')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)          # ora z = alto
me.transform(Matrix.Rotation(GIRO, 4, 'Z'))                                         # la punta dei pattini verso +X
me.validate(); me.update()
for p in me.polygons: p.use_smooth = True

# ── materiale: solo il colore, a 1024 ──
mt = me.materials[0]; b = next(n for n in mt.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
for nome, val in (('Metallic', 0.0), ('Roughness', 0.55), ('Normal', None)):
    for l in list(b.inputs[nome].links): mt.node_tree.links.remove(l)
    if val is not None: b.inputs[nome].default_value = val
for n in list(mt.node_tree.nodes):
    if n.type == 'NORMAL_MAP' or (n.type == 'TEX_IMAGE' and not n.outputs[0].links and not n.outputs[1].links): mt.node_tree.nodes.remove(n)
    elif n.type == 'TEX_IMAGE' and n.image: n.image.scale(1024, 1024); n.image.pack()

# ── i tre pezzi ──
def pezzo(nome, filtro):
    d = ob.data.copy(); o = bpy.data.objects.new(nome, d); bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(d)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not filtro(f.calc_center_median())], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(d); bm.free(); return o
alto = pezzo('Bicchiere', lambda p: p.z >= Z_ANCA)
basso = pezzo('Gambe', lambda p: p.z < Z_ANCA)
# i due pattini sono due parti staccate (uno avanti e uno indietro, e un po' larghi): le trovo come componenti connesse
bm = bmesh.new(); bm.from_mesh(basso.data); bm.verts.ensure_lookup_table()
visti = set(); comp = []
for v0 in bm.verts:
    if v0.index in visti: continue
    pila = [v0]; visti.add(v0.index); c = []
    while pila:
        q = pila.pop(); c.append(q.index)
        for e in q.link_edges:
            w = e.other_vert(q)
            if w.index not in visti: visti.add(w.index); pila.append(w)
    comp.append(c)
comp.sort(key=len, reverse=True)
print('componenti delle gambe:', [len(c) for c in comp[:6]])
lato = {}                                                      # indice vertice -> +1 sinistra (+Y) / -1 destra
for c in comp[:2]:
    y = np.mean([bm.verts[i].co.y for i in c]); [lato.__setitem__(i, 1 if y > 0 else -1) for i in c]
# se la divisione non dà due parti distinte (una a sinistra e una a destra) ripiego sul taglio per larghezza
if sorted({lato[i] for c in comp[:2] for i in c}) != [-1, 1]:
    ymed = np.mean([w.co.y for w in bm.verts]); print('ripiego sul taglio laterale a y =', round(ymed, 3))
    for w in bm.verts: lato[w.index] = 1 if w.co.y > ymed else -1
for w in bm.verts: lato.setdefault(w.index, 1 if w.co.y > 0 else -1)
fl = {f.index: (1 if sum(lato[v.index] for v in f.verts) > 0 else -1) for f in bm.faces}
bm.free()
basso.data.update()
def lato_faccia(poly_index): return fl[poly_index]
def pezzo_lato(nome, segno):
    d = basso.data.copy(); o = bpy.data.objects.new(nome, d); bpy.context.scene.collection.objects.link(o)
    b2 = bmesh.new(); b2.from_mesh(d); b2.faces.ensure_lookup_table()
    bmesh.ops.delete(b2, geom=[f for f in b2.faces if fl[f.index] != segno], context='FACES')
    bmesh.ops.delete(b2, geom=[v for v in b2.verts if not v.link_faces], context='VERTS')
    b2.to_mesh(d); b2.free(); return o
sx = pezzo_lato('PattinoS', 1)       # +Y è la SINISTRA di chi guarda verso +X
dx = pezzo_lato('PattinoD', -1)
bpy.data.objects.remove(basso)
# origini: il bicchiere ai fianchi in mezzo; i pattini all'anca, cioè al centro della loro sezione alta
for o in (alto, sx, dx):
    vv = np.array([w.co[:] for w in o.data.vertices])
    if o is alto: pivot = Vector((0, 0, Z_ANCA))
    else:
        alta = vv[vv[:, 2] > Z_ANCA - 0.03]; pivot = Vector((alta[:, 0].mean(), alta[:, 1].mean(), Z_ANCA))
    o.data.transform(Matrix.Translation(-pivot)); o.location = pivot
bpy.data.objects.remove(ob)
for o in (alto, sx, dx):
    o.data.calc_loop_triangles(); print('%s: %d triangoli, origine %s' % (o.name, len(o.data.loop_triangles), tuple(round(t, 3) for t in o.location)))
bpy.context.view_layer.update()
lo, hi = viste.ingombro([alto, sx, dx])
print('ingombro: x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f' % (lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))
os.makedirs(out_dir, exist_ok=True)
glb = os.path.join(out_dir, 'birra.glb')
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_apply=True, export_yup=True, export_image_format='JPEG', export_jpeg_quality=85, export_animations=False)
print('glb: %.2f MB' % (os.path.getsize(glb) / 1e6))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, 'birra.blend'))

# controllo: tre quarti, lato (la freccia gialla va dove guarda), fronte, dietro — con una freccia sul +X
sc = viste.scena_base(res=(640, 640), fondo=(0.55, 0.62, 0.7))
fr = bpy.data.meshes.new('f'); bmf = bmesh.new()
bmesh.ops.create_cone(bmf, cap_ends=True, segments=8, radius1=0.02, radius2=0.0, depth=0.08, matrix=Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Translation((0, 0, 0.04)))
bmf.to_mesh(fr); bmf.free()
mm = bpy.data.materials.new('g'); mm.use_nodes = True
bs = next(n for n in mm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); bs.inputs['Base Color'].default_value = (1, 0.1, 0.1, 1); bs.inputs['Emission Color'].default_value = (1, 0.1, 0.1, 1); bs.inputs['Emission Strength'].default_value = 3
fr.materials.append(mm); fo = bpy.data.objects.new('freccia', fr); fo.location = (0.2, 0, 0.02); bpy.context.scene.collection.objects.link(fo)
viste.foglio(os.path.join(out_dir, 'birra-viste.png'), [alto, sx, dx], viste=((0.8, -0.8, 0.35), (0, -1, 0.1), (1, 0, 0.1), (-0.7, -0.7, 0.4)), colonne=2, margine=0.85)
