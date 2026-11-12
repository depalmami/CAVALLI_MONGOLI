# IL BOSS — modello definitivo della proposta B «La Parata», pronto per il gioco.
#
# Un costume, come il cavallo di cartone del giocatore: la testa-logo in spalla e dietro una fila di spicchi di
# scalinata, ognuno con le gambe di chi lo porta. Niente scheletro: ogni pezzo è un oggetto rigido con l'origine
# nel suo giunto, e il gioco (3d/boss.js) li muove a codice — gli spicchi seguono la strada, le gambe corrono.
#
# uso:  blender -b --python tools/boss/modello_parata.py -- assets/models/boss/testa-bocca.blend assets/models/boss
#       (testa-bocca.blend lo fa tools/boss/taglia_bocca.py: la testa divisa in Cranio e Mascella)
# esce: coccodrillo.glb (per il gioco), coccodrillo.blend (sorgente), coccodrillo-viste.png (controllo)
#
# Assi in Blender: +X = muso, +Z = alto, 1 unità = 1 m = 1000 unità di gioco. Nel GLB diventa +X muso, +Y alto, +Z destra.
# NOMI (il gioco li cerca così): Testa › Cranio, Mascella · Spicchio0-4 · Coda0-2 · Coscia_<pezzo>_<S|D> › Stinco_<pezzo>_<S|D>
import bpy, bmesh, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import viste

testa_blend, out_dir = [os.path.abspath(p) for p in sys.argv[sys.argv.index('--') + 1:][:2]]
S, PI = 3.0, math.pi
HZ = 1.05                                  # quota della testa: sotto ci stanno le gambe di chi la porta
ANCA, COSCIA, STINCO = 1.2, 0.58, 0.56     # altezza dell'anca e lunghezze della gamba

bpy.ops.wm.read_factory_settings(use_empty=True)
COL = bpy.context.scene.collection

def srgb(h):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (c(h >> 16 & 255), c(h >> 8 & 255), c(h & 255), 1)

def materiale(nome, hexc, ruvido=0.8):
    m = bpy.data.materials.new(nome); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = srgb(hexc)
    b.inputs['Roughness'].default_value = ruvido; b.inputs['Metallic'].default_value = 0.0
    return m

SCURO, MEDIO, BIANCO, TELA, JEANS, PELLE = range(6)
MATS = [materiale('grigio scuro', 0x4b4c50), materiale('grigio medio', 0x77787d), materiale('bianco', 0xf2f3f5, 0.55),
        materiale('tela', 0x26282e, 0.95), materiale('jeans', 0x8fa9c4, 0.9), materiale('pelle', 0x8b5a3c, 0.6)]

class Pezzo:
    """Geometria accumulata in coordinate LOCALI al giunto del pezzo."""
    def __init__(self, nome):
        self.nome = nome; self.bm = bmesh.new()
    def box(self, x0, x1, y0, y1, z0, z1, lato=SCURO, sopra=None):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        v = [self.bm.verts.new((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        for idx, mi in (((0, 1, 3, 2), lato), ((4, 6, 7, 5), lato), ((0, 4, 5, 1), lato), ((2, 3, 7, 6), lato),
                        ((0, 2, 6, 4), lato), ((1, 5, 7, 3), lato if sopra is None else sopra)):
            self.bm.faces.new([v[i] for i in idx]).material_index = mi
    def barra(self, a, b, t):
        lo = [min(a[i], b[i]) - t / 2 for i in range(3)]; hi = [max(a[i], b[i]) + t / 2 for i in range(3)]
        self.box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], BIANCO)
    def blocco(self, x0, x1, y0, y1, z0, z1, t=0.04):
        """Un gradino: scatola a due grigi col filo bianco sugli spigoli, come la testa."""
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        self.box(x0, x1, y0, y1, z0, z1, SCURO, MEDIO)
        for y in (y0, y1):
            self.barra((x0, y, z1), (x1, y, z1), t); self.barra((x0, y, z0), (x1, y, z0), t)
            self.barra((x0, y, z0), (x0, y, z1), t); self.barra((x1, y, z0), (x1, y, z1), t)
        for x in (x0, x1): self.barra((x, y0, z1), (x, y1, z1), t)
    def prisma(self, profilo, y0, y1, mi=SCURO):
        a = [self.bm.verts.new((x, y0, z)) for x, z in profilo]; b = [self.bm.verts.new((x, y1, z)) for x, z in profilo]
        n = len(profilo)
        self.bm.faces.new(a).material_index = mi; self.bm.faces.new(b[::-1]).material_index = mi
        for i in range(n): self.bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])).material_index = mi
    def cilindro(self, p0, p1, r0, r1, mi, seg=10):
        p0, p1 = Vector(p0), Vector(p1); a = (p1 - p0).normalized(); u = a.orthogonal().normalized(); w = a.cross(u)
        an = [[self.bm.verts.new(p + (u * math.cos(2 * PI * k / seg) + w * math.sin(2 * PI * k / seg)) * r)
               for k in range(seg)] for p, r in ((p0, r0), (p1, r1))]
        for k in range(seg):
            f = self.bm.faces.new((an[0][k], an[0][(k + 1) % seg], an[1][(k + 1) % seg], an[1][k]))
            f.material_index = mi; f.smooth = True
        self.bm.faces.new(an[0]).material_index = mi; self.bm.faces.new(an[1][::-1]).material_index = mi
    def tubo(self, punti, r, mi=BIANCO):
        for a, b in zip(punti, punti[1:]): self.cilindro(a, b, r, r, mi, 6)
    def fine(self, genitore=None, pos=(0, 0, 0)):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(self.nome); self.bm.to_mesh(me); self.bm.free()
        for m in MATS: me.materials.append(m)
        ob = bpy.data.objects.new(self.nome, me); COL.objects.link(ob)
        ob.location = pos
        if genitore: ob.parent = genitore
        return ob

def gambe(pezzo, nome, x, mezza):
    """Una coppia di gambe dritte (posa di riposo): coscia con l'origine all'anca, stinco con l'origine al ginocchio."""
    for lato, sigla in ((1, 'S'), (-1, 'D')):                    # +Y in Blender è la sinistra di chi guarda verso +X
        c = Pezzo('Coscia_%s_%s' % (nome, sigla))
        c.cilindro((0, 0, 0.04), (0, 0, -COSCIA), 0.13, 0.105, JEANS)
        coscia = c.fine(pezzo, (x, lato * mezza, ANCA))
        s = Pezzo('Stinco_%s_%s' % (nome, sigla))
        s.cilindro((0, 0, 0.03), (0, 0, -STINCO * 0.45), 0.105, 0.09, JEANS)          # i jeans arrivano a mezzo polpaccio
        s.cilindro((0, 0, -STINCO * 0.45), (0, 0, -STINCO), 0.07, 0.052, PELLE)
        s.cilindro((-0.05, 0, -STINCO - 0.015), (0.22, 0, -STINCO - 0.035), 0.058, 0.042, PELLE)   # il piede nudo
        s.fine(coscia, (0, 0, -COSCIA))

# ── TESTA: un vuoto nel collo (a terra) a cui stanno appesi il cranio, la mascella che scende, la tela e chi la porta.
# I portatori stanno DIETRO il perno della mascella: davanti la bocca deve potersi aprire fino a terra.
PERNO = (-0.165, 0.0, 0.12)                # in coordinate native della testa: vedi tools/boss/taglia_bocca.py
with bpy.data.libraries.load(testa_blend) as (da, a): a.objects = ['Cranio', 'Mascella']
cranio, mascella = a.objects
testa = bpy.data.objects.new('Testa', None); COL.objects.link(testa)
def applica(o, loc, sposta):
    COL.objects.link(o); o.scale = (S, S, S); o.location = loc
    for x in bpy.context.selected_objects: x.select_set(False)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.transform_apply(location=sposta, rotation=True, scale=True)
    o.parent = testa
applica(cranio, (0.4905 * S, 0, HZ), True)                       # il piano posteriore della testa finisce a x = 0: è il collo
applica(mascella, ((PERNO[0] + 0.4905) * S, 0, PERNO[2] * S + HZ), False)   # l'origine resta nel perno
for mt in bpy.data.materials:                                    # della testa solo il colore: metallo e rilievo pesavano 12 MB e schiarivano
    if not mt.use_nodes or not mt.name.startswith('tripo'): continue
    b = next(n for n in mt.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for nome, v in (('Metallic', 0.0), ('Roughness', 0.8), ('Normal', None)):
        for l in list(b.inputs[nome].links): mt.node_tree.links.remove(l)
        if v is not None: b.inputs[nome].default_value = v
    for n in list(mt.node_tree.nodes):
        if n.type == 'TEX_IMAGE' and not n.outputs[0].links and not n.outputs[1].links: mt.node_tree.nodes.remove(n)
        elif n.type == 'NORMAL_MAP': mt.node_tree.nodes.remove(n)
    for n in mt.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image: n.image.scale(2048, 2048); n.image.pack()
t = Pezzo('TelaTesta'); t.box(0.12, 0.84, -0.36, 0.36, 0.98, HZ + 0.16, TELA)
tela = t.fine(testa)
gambe(testa, 'T0', 0.24, 0.2); gambe(testa, 'T1', 0.76, 0.2)

# ── SPICCHI: cinque, con la gobba; ognuno due gradini e la tela davanti ─────
cima0 = HZ + 0.431 * S
N, LUNG, VUOTO = 5, 1.1, 0.22
PASSO = LUNG + VUOTO
gobba = [0.14, 0.3, 0.3, 0.12, -0.14]
for i in range(N):
    w = 1.4 - i * 0.11; cima = cima0 + gobba[i]; orlo = 1.1 + i * 0.03
    s = Pezzo('Spicchio%d' % i)
    s.box(-VUOTO - 0.02, 0.02, -w / 2 + 0.14, w / 2 - 0.14, orlo + 0.12, cima - 0.42, TELA)
    s.blocco(-VUOTO - LUNG / 2, -VUOTO, -w / 2, w / 2, orlo, cima)
    s.blocco(-VUOTO - LUNG, -VUOTO - LUNG / 2, -w / 2, w / 2, orlo, cima - 0.15)
    ob = s.fine(None, (-i * PASSO, 0, 0))
    gambe(ob, 'S%d' % i, -VUOTO - LUNG / 2, min(0.24, w / 2 - 0.14))

# ── CODA: due spicchi piccoli senza gambe e la punta ───────────────────────
x = -N * PASSO
PASSO_CODA = 0.75
for i in range(3):
    w = 0.8 - i * 0.2; cima = cima0 - 0.42 - i * 0.26; orlo = 1.26 + i * 0.05
    s = Pezzo('Coda%d' % i)
    s.box(-0.22, 0.02, -w / 2 + 0.08, w / 2 - 0.08, orlo + 0.08, cima - 0.2, TELA)
    if i < 2: s.blocco(-0.2 - 0.55, -0.2, -w / 2, w / 2, orlo, cima)
    else:
        s.prisma([(-0.2, orlo), (-0.2, cima), (-1.1, orlo + 0.1)], -w / 2, w / 2, SCURO)
        for y in (-w / 2, w / 2): s.tubo([(-0.2, y, orlo), (-0.2, y, cima), (-1.1, y, orlo + 0.1), (-0.2, y, orlo)], 0.02)
        s.tubo([(-0.2, -w / 2, cima), (-0.2, w / 2, cima)], 0.02)
    s.fine(None, (x, 0, 0))
    x -= PASSO_CODA

# ── uscita ─────────────────────────────────────────────────────────────────
bpy.context.view_layer.update()
oggetti = [o for o in COL.all_objects if o.type == 'MESH']
tri = 0
for o in oggetti:
    o.data.calc_loop_triangles(); tri += len(o.data.loop_triangles)
lo, hi = viste.ingombro(oggetti)
print('modello: %d oggetti · %d triangoli · x %.2f..%.2f · alto %.2f · largo %.2f' % (len(oggetti), tri, lo.x, hi.x, hi.z, hi.y - lo.y))
glb = os.path.join(out_dir, 'coccodrillo.glb')
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_apply=True, export_yup=True,
                          export_image_format='JPEG', export_jpeg_quality=82, export_animations=False)
print('glb: %.2f MB' % (os.path.getsize(glb) / 1e6))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, 'coccodrillo.blend'))

# foglio di controllo (dopo l'export: luci, suolo e camera non devono finire nel GLB)
sc = viste.scena_base(res=(800, 500), fondo=(0.42, 0.52, 0.62))
p = bmesh.new(); bmesh.ops.create_grid(p, x_segments=1, y_segments=1, size=60)
su = bpy.data.meshes.new('Suolo'); p.to_mesh(su); p.free(); su.materials.append(materiale('steppa', 0x8c9366, 1.0))
COL.objects.link(bpy.data.objects.new('Suolo', su))
viste.foglio(os.path.join(out_dir, 'coccodrillo-viste.png'), oggetti, viste=((0.8, -0.85, 0.38), 'lato', (-0.8, -0.8, 0.4), 'alto'), colonne=2)
