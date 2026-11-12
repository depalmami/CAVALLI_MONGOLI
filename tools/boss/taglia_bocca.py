# TAGLIA LA BOCCA — la testa-logo è un blocco unico: qui la si divide in Cranio e Mascella lungo la linea della bocca
# disegnata sul fianco, così la mascella può scendere. Le facce del taglio diventano l'interno della bocca (rosso
# scuro); sui due bordi vanno i denti veri, bianchi, e sulla mascella la lingua. A bocca chiusa denti e lingua
# stanno dentro il pieno dell'altro pezzo e non si vedono.
#
# uso:  blender -b assets/models/boss/testa-60k.blend --python tools/boss/taglia_bocca.py -- assets/models/boss/testa-bocca.blend [png di controllo]
# La linea è stata letta dalla vista di lato col righello (tools/boss/righello.py). Coordinate NATIVE della testa:
# x = muso (da -0,49 a 0,49), y = largo (±0,166), z = alto (da 0 a 0,43).
import bpy, bmesh, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

args = sys.argv[sys.argv.index('--') + 1:]
dst = os.path.abspath(args[0]); png = os.path.abspath(args[1]) if len(args) > 1 else None

LINEA = [(-0.13, 0.1375), (-0.10, 0.145), (-0.07, 0.141), (-0.04, 0.131), (-0.01, 0.1175), (0.02, 0.11), (0.05, 0.105),
         (0.08, 0.1075), (0.11, 0.114), (0.14, 0.12), (0.17, 0.122), (0.20, 0.1175), (0.23, 0.105), (0.26, 0.094),
         (0.29, 0.087), (0.32, 0.085), (0.35, 0.089), (0.38, 0.0935), (0.41, 0.096), (0.45, 0.096), (0.50, 0.094)]
RETRO_X, RETRO_Z = -0.20, 0.105           # dietro la mascella finisce in verticale, poi sale all'angolo della bocca
PERNO = (-0.165, 0.0, 0.12)               # attorno a questo punto ruota la mascella
MEZZA = 0.152                             # mezza larghezza del fianco

def srgb(h):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (c(h >> 16 & 255), c(h >> 8 & 255), c(h & 255), 1)
def materiale(nome, hexc, ruvido=0.7):
    m = bpy.data.materials.new(nome); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = srgb(hexc); b.inputs['Roughness'].default_value = ruvido; b.inputs['Metallic'].default_value = 0.0
    return m
M_BOCCA, M_DENTI, M_LINGUA = materiale('bocca', 0x4a0f14, 0.6), materiale('denti', 0xf4f1e6, 0.45), materiale('lingua', 0xc4506a, 0.55)

def z_linea(x):
    for (x0, z0), (x1, z1) in zip(LINEA, LINEA[1:]):
        if x0 <= x <= x1: return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return LINEA[0][1] if x < LINEA[0][0] else LINEA[-1][1]

COL = bpy.context.scene.collection
testa = bpy.data.objects['Testa']
for o in list(bpy.data.objects):
    if o is not testa: bpy.data.objects.remove(o)
bpy.context.view_layer.objects.active = testa; testa.select_set(True)
me = testa.data; me.calc_loop_triangles()
m = testa.modifiers.new('riduci', 'DECIMATE'); m.ratio = min(1, 40000 / len(me.loop_triangles))
bpy.ops.object.modifier_apply(modifier='riduci')
me.validate(); me.update()

# il coltello: un prisma che riempie tutto quello che sta SOTTO la linea della bocca, dal retro alla punta e oltre
def oggetto(nome, bm, mats):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    d = bpy.data.meshes.new(nome); bm.to_mesh(d); bm.free()
    for mt in mats: d.materials.append(mt)
    o = bpy.data.objects.new(nome, d); COL.objects.link(o); return o
prof = LINEA[:-1] + [(0.56, LINEA[-1][1]), (0.56, -0.06), (RETRO_X, -0.06), (RETRO_X, RETRO_Z)]
bm = bmesh.new()
a = [bm.verts.new((x, -0.3, z)) for x, z in prof]; b = [bm.verts.new((x, 0.3, z)) for x, z in prof]
bm.faces.new(a); bm.faces.new(b[::-1])
for i in range(len(prof)): bm.faces.new((a[i], a[(i + 1) % len(prof)], b[(i + 1) % len(prof)], b[i]))
bmesh.ops.triangulate(bm, faces=bm.faces[:])
coltello = oggetto('Coltello', bm, [M_BOCCA])

def taglia(nome, operazione):
    o = testa.copy(); o.data = testa.data.copy(); o.name = nome; COL.objects.link(o)
    mod = o.modifiers.new('taglio', 'BOOLEAN'); mod.object = coltello; mod.operation = operazione
    for s in ('EXACT', 'MANIFOLD', 'FLOAT', 'FAST'):
        try: mod.solver = s; break
        except TypeError: continue
    try: mod.material_mode = 'TRANSFER'          # le facce nuove prendono il materiale del coltello: l'interno della bocca
    except Exception: pass
    for ob in bpy.context.selected_objects: ob.select_set(False)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.modifier_apply(modifier='taglio')
    o.data.calc_loop_triangles()
    print('%s: %d triangoli, materiali %s' % (nome, len(o.data.loop_triangles), [mt.name[:14] for mt in o.data.materials]))
    return o
cranio = taglia('Cranio', 'DIFFERENCE')
mascella = taglia('Mascella', 'INTERSECT')
bpy.data.objects.remove(coltello); bpy.data.objects.remove(testa)

# denti e lingua
def cono(bm, base, punta, r, mi, seg=6):
    base, punta = Vector(base), Vector(punta); ax = (punta - base).normalized(); u = ax.orthogonal().normalized(); w = ax.cross(u)
    an = [bm.verts.new(base + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)]
    p = bm.verts.new(punta)
    for k in range(seg): bm.faces.new((an[k], an[(k + 1) % seg], p)).material_index = mi
    bm.faces.new(an[::-1]).material_index = mi
def denti(verso, sfasa):
    """Una fila per fianco lungo la linea, più quattro davanti. verso -1 = pendono dal cranio, +1 = salgono dalla mascella."""
    bm = bmesh.new()
    x = 0.0 + sfasa
    while x < 0.47:
        h = 0.044 + 0.014 * math.sin(x * 40)                    # alti e bassi, come quelli disegnati
        for y in (-MEZZA + 0.022, MEZZA - 0.022):
            z = z_linea(x); cono(bm, (x, y, z - verso * 0.004), (x + 0.004, y, z + verso * h), 0.016, 0)
        x += 0.044
    for y in (-0.09, -0.03, 0.03, 0.09):
        z = z_linea(0.47); cono(bm, (0.468, y + sfasa * 0.5, z - verso * 0.004), (0.47, y + sfasa * 0.5, z + verso * 0.04), 0.015, 0)
    return oggetto('denti', bm, [M_DENTI])
def lingua():
    bm = bmesh.new()
    xs = [-0.06 + i * 0.02 for i in range(24)]                   # segue la linea, appena sopra il taglio
    def sez(x):
        w = 0.085 * min(1, (0.44 - x) / 0.12 + 0.25); z = z_linea(x)
        return [bm.verts.new((x, -w, z + 0.002)), bm.verts.new((x, -w * 0.5, z + 0.014)), bm.verts.new((x, w * 0.5, z + 0.014)), bm.verts.new((x, w, z + 0.002))]
    r = [sez(x) for x in xs]
    for i in range(len(r) - 1):
        for k in range(3): bm.faces.new((r[i][k], r[i][k + 1], r[i + 1][k + 1], r[i + 1][k]))
    return oggetto('lingua', bm, [M_LINGUA])
def unisci(base, altri):
    for ob in bpy.context.selected_objects: ob.select_set(False)
    for o in altri: o.select_set(True)
    base.select_set(True); bpy.context.view_layer.objects.active = base
    bpy.ops.object.join()
unisci(cranio, [denti(-1, 0.0)])
unisci(mascella, [denti(+1, 0.022), lingua()])
for o in (cranio, mascella):
    o.data.validate(); o.data.update(); o.data.calc_loop_triangles()
    print('%s finale: %d triangoli' % (o.name, len(o.data.loop_triangles)))
# la mascella ha l'origine nel perno: chi la ruota non deve sapere altro
p = Vector(PERNO)
mascella.data.transform(__import__('mathutils').Matrix.Translation(-p)); mascella.location = p
bpy.ops.wm.save_as_mainfile(filepath=dst)
print('salvato', dst)

if png:                                                          # controllo: chiusa e aperta, di lato e di tre quarti
    import viste
    sc = viste.scena_base(res=(800, 500))
    tess = []
    for ang, nome in ((0.0, 'chiusa'), (math.radians(26), 'aperta')):
        mascella.rotation_euler = (0, ang, 0)                    # +Y in Blender: con X in avanti la punta scende
        bpy.context.view_layer.update()
        f = png.replace('.png', '-%s.png' % nome)
        viste.foglio(f, [cranio, mascella], viste=('lato', (0.9, -0.6, 0.15)), colonne=2, margine=0.75)
    mascella.rotation_euler = (0, 0, 0)
