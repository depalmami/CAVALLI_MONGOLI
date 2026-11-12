# Tre proposte di corpo per il Boss, costruite attorno alla testa-logo (il coccodrillo a scalinata).
# uso: blender -b --python costruisci.py -- <p1|p2|p3> <testa.blend> <cavallo.glb> <cartella out>
# Assi: +X = muso, +Z = alto, 1 unità = 1 m = 1000 unità di gioco (HORSE_HEIGHT = 1,3).
import bpy, bmesh, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import viste

quale, testa_blend, glb_cavallo, out_dir = sys.argv[sys.argv.index('--') + 1:][:4]
S = 3.0                                   # scala della testa: 0,98 → 2,94 m
PI = math.pi

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = viste.scena_base(res=(800, 500), fondo=(0.42, 0.52, 0.62))
COL = sc.collection

def srgb(h):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (c(h >> 16 & 255), c(h >> 8 & 255), c(h & 255), 1)

def materiale(nome, hexc, ruvido=0.8, metallo=0.0):
    m = bpy.data.materials.new(nome); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = srgb(hexc)
    b.inputs['Roughness'].default_value = ruvido
    b.inputs['Metallic'].default_value = metallo
    return m

# indici fissi dei materiali in ogni pezzo
SCURO, MEDIO, BIANCO, TELA, JEANS, PELLE = range(6)
MATS = [materiale('grigio scuro', 0x4b4c50), materiale('grigio medio', 0x77787d), materiale('bianco', 0xf2f3f5, 0.55),
        materiale('tela', 0x26282e, 0.95), materiale('jeans', 0x8fa9c4, 0.9), materiale('pelle', 0x8b5a3c, 0.6)]

class Pezzo:
    def __init__(self, nome):
        self.nome = nome; self.bm = bmesh.new()
    def box(self, x0, x1, y0, y1, z0, z1, lato=SCURO, sopra=None):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        v = [self.bm.verts.new((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        for idx, mi in (((0, 1, 3, 2), lato), ((4, 6, 7, 5), lato), ((0, 4, 5, 1), lato), ((2, 3, 7, 6), lato),
                        ((0, 2, 6, 4), lato), ((1, 5, 7, 3), lato if sopra is None else sopra)):
            self.bm.faces.new([v[i] for i in idx]).material_index = mi
    def barra(self, a, b, t):                                    # listello bianco lungo uno spigolo allineato agli assi
        lo = [min(a[i], b[i]) - t / 2 for i in range(3)]; hi = [max(a[i], b[i]) + t / 2 for i in range(3)]
        self.box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], BIANCO)
    def blocco(self, x0, x1, y0, y1, z0, z1, t=0.04, lato=SCURO, sopra=MEDIO, sotto=True):
        """Un gradino: scatola a due grigi con il filo bianco sugli spigoli, come la testa."""
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        self.box(x0, x1, y0, y1, z0, z1, lato, sopra)
        for y in (y0, y1):
            self.barra((x0, y, z1), (x1, y, z1), t)
            self.barra((x0, y, z0), (x0, y, z1), t); self.barra((x1, y, z0), (x1, y, z1), t)
            if sotto: self.barra((x0, y, z0), (x1, y, z0), t)
        for x in (x0, x1): self.barra((x, y0, z1), (x, y1, z1), t)
    def prisma(self, profilo, y0, y1, mi=SCURO):                 # profilo [(x, z)...] estruso lungo Y
        a = [self.bm.verts.new((x, y0, z)) for x, z in profilo]; b = [self.bm.verts.new((x, y1, z)) for x, z in profilo]
        n = len(profilo)
        self.bm.faces.new(a).material_index = mi; self.bm.faces.new(b[::-1]).material_index = mi
        for i in range(n):
            self.bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])).material_index = mi
    def cilindro(self, p0, p1, r0, r1, mi=SCURO, seg=12):
        p0, p1 = Vector(p0), Vector(p1); a = (p1 - p0).normalized(); u = a.orthogonal().normalized(); w = a.cross(u)
        an = [[self.bm.verts.new(p + (u * math.cos(2 * PI * k / seg) + w * math.sin(2 * PI * k / seg)) * max(r, 1e-3))
               for k in range(seg)] for p, r in ((p0, r0), (p1, r1))]
        for k in range(seg):
            f = self.bm.faces.new((an[0][k], an[0][(k + 1) % seg], an[1][(k + 1) % seg], an[1][k]))
            f.material_index = mi; f.smooth = True
        self.bm.faces.new(an[0]).material_index = mi; self.bm.faces.new(an[1][::-1]).material_index = mi
    def tubo(self, punti, r, mi=BIANCO, seg=8):
        for a, b in zip(punti, punti[1:]): self.cilindro(a, b, r, r, mi, seg)
    def pelle(self, anelli, mat_di, tappi=True):                 # superficie tesa fra anelli di punti
        vv = [[self.bm.verts.new(p) for p in an] for an in anelli]; n = len(vv[0])
        for i in range(len(vv) - 1):
            for k in range(n):
                q = (vv[i][k], vv[i][(k + 1) % n], vv[i + 1][(k + 1) % n], vv[i + 1][k])
                f = self.bm.faces.new(q); f.smooth = True
                f.material_index = mat_di(sum((v.co for v in q), Vector()) / 4, i)
        if tappi:
            self.bm.faces.new(vv[0]).material_index = SCURO; self.bm.faces.new(vv[-1][::-1]).material_index = SCURO
    def fine(self, genitore=None, pos=(0, 0, 0), rz=0.0):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(self.nome); self.bm.to_mesh(me); self.bm.free()
        for m in MATS: me.materials.append(m)
        ob = bpy.data.objects.new(self.nome, me); COL.objects.link(ob)
        ob.location = pos; ob.rotation_euler = (0, 0, rz)
        if genitore: ob.parent = genitore
        BOSS.append(ob)
        return ob

BOSS = []

def porta_testa(hz):
    with bpy.data.libraries.load(testa_blend) as (da, a): a.objects = ['Testa']
    ob = a.objects[0]; COL.objects.link(ob)
    ob.scale = (S, S, S); ob.location = (0.4905 * S, 0, hz)     # il piano posteriore della testa finisce a x = 0
    for m in ob.data.materials:                                  # niente mappa del metallo: rifletteva il cielo e schiariva tutto
        b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for nome, v in (('Metallic', 0.0), ('Roughness', 0.8)):
            for l in list(b.inputs[nome].links): m.node_tree.links.remove(l)
            b.inputs[nome].default_value = v
    BOSS.append(ob)
    return ob

def porta_cavallo(pos):
    """Il cavallo del giocatore accanto al Boss, per il confronto di taglia."""
    try:
        bpy.ops.import_scene.gltf(filepath=glb_cavallo)
        nuovi = list(bpy.context.selected_objects)
        radice = bpy.data.objects.new('Cavallo', None); COL.objects.link(radice)
        for o in nuovi:
            if o.parent is None: o.parent = radice
        bpy.context.view_layer.update()
        lo, hi = viste.ingombro(nuovi)
        k = 1.55 / max(1e-6, hi.z - lo.z)
        radice.scale = (k, k, k); radice.rotation_euler = (0, 0, PI / 2)   # il glTF guarda -Y in Blender: lo giro verso +X
        bpy.context.view_layer.update()
        lo, hi = viste.ingombro(nuovi)
        radice.location = (pos[0] - (lo.x + hi.x) / 2, pos[1] - (lo.y + hi.y) / 2, -lo.z)
        print('cavallo: scala %.3f' % k)
    except Exception as e:
        print('cavallo non importato:', e)
        p = Pezzo('Cavallo'); p.box(pos[0] - 0.8, pos[0] + 0.8, pos[1] - 0.3, pos[1] + 0.3, 0.5, 1.3, TELA); o = p.fine(); BOSS.remove(o)

def suolo():
    p = bmesh.new(); bmesh.ops.create_grid(p, x_segments=1, y_segments=1, size=60)
    me = bpy.data.meshes.new('Suolo'); p.to_mesh(me); p.free()
    me.materials.append(materiale('steppa', 0x8c9366, 1.0))
    COL.objects.link(bpy.data.objects.new('Suolo', me))

def artigli(p, x, y, lato, n=3, lung=0.34, alt=0.24, larg=0.5):
    """Unghie bianche a cuneo davanti al piede, come le dita disegnate sul logo."""
    passo = larg / n
    for i in range(n):
        y0 = y - larg / 2 + i * passo + 0.02; y1 = y0 + passo - 0.04
        p.prisma([(x, 0.0), (x + lung, 0.0), (x, alt)], y0, y1, BIANCO)

# ─────────────────────────────────────────────────────────────────────────────
# PROPOSTA 1 — LA SCALINATA: il logo continua. I gradini della testa salgono fino alle spalle e ridiscendono
# lungo la coda: tutto il coccodrillo è una gradinata di pietra che cammina. Zampe a gradoni.
# ─────────────────────────────────────────────────────────────────────────────
def p1():
    hz = 0.55
    porta_testa(hz)
    cima_testa = hz + 0.431 * S
    c = Pezzo('Corpo')
    alzata, pedata, pancia = 0.13, 0.45, 0.5
    largh = [1.25, 1.5, 1.7, 1.8]
    x, z = 0.0, cima_testa
    for i in range(4):
        z += alzata
        lung = pedata if i < 3 else pedata + 1.1               # l'ultimo gradino è il pianerottolo delle spalle
        c.blocco(x - lung, x, -largh[i] / 2, largh[i] / 2, pancia, z)
        x -= lung
    # zampe a gradoni: coscia, stinco, piede con le unghie
    for xc, mezza, k in ((-0.85, 0.75, 1.0), (-2.25, 0.9, 1.15)):
        for lato in (-1, 1):
            y = lato * mezza
            c.blocco(xc - 0.42 * k, xc + 0.42 * k, y, y + lato * 0.5 * k, 0.8, 1.45 * k)
            c.blocco(xc - 0.32 * k, xc + 0.36 * k, y + lato * 0.3 * k, y + lato * 0.85 * k, 0.28, 0.9)
            c.blocco(xc - 0.3 * k, xc + 0.62 * k, y + lato * 0.45 * k, y + lato * 1.1 * k, 0.0, 0.3)
            artigli(c, xc + 0.62 * k, y + lato * 0.775 * k, lato, larg=0.6 * k)
    corpo = c.fine()
    # coda: dodici gradini che scendono, ognuno un pezzo a sé (si potrà muovere) in leggera S
    n, ped = 12, 0.4
    prec, cima = corpo, z
    for i in range(n):
        cima -= (z - 0.62) / n
        w = 1.6 - i * 0.11
        g = Pezzo('Coda%02d' % i)
        g.blocco(-ped, 0, -w / 2, w / 2, 0.42, cima)
        prec = g.fine(prec, (x if i == 0 else -ped, 0, 0), 0.085 * math.sin(i * 0.62 + 0.4))
    return hz

# ─────────────────────────────────────────────────────────────────────────────
# PROPOSTA 2 — LA PARATA: un costume, come il cavallo di cartone del giocatore. La testa-logo in spalla e dietro
# una fila di spicchi di scalinata, ognuno con le gambe di chi lo porta: un drago da festa che corre.
# ─────────────────────────────────────────────────────────────────────────────
def gambe_umane(p, x, mezza, fase):
    for lato, a in ((-1, fase), (1, -fase)):
        y = lato * mezza
        anca = Vector((x, y, 1.2))
        if a > 0:   ginocchio = anca + Vector((0.3, 0, -0.5));  caviglia = ginocchio + Vector((0.08, 0, -0.52))
        else:       ginocchio = anca + Vector((-0.12, 0, -0.56)); caviglia = ginocchio + Vector((-0.42, 0, -0.3))
        p.cilindro(anca, ginocchio, 0.12, 0.1, JEANS)
        meta = ginocchio.lerp(caviglia, 0.45)
        p.cilindro(ginocchio, meta, 0.1, 0.085, JEANS); p.cilindro(meta, caviglia, 0.065, 0.05, PELLE)
        punta = caviglia + (Vector((0.24, 0, -0.06)) if a > 0 else Vector((0.1, 0, -0.22)))
        p.cilindro(caviglia, punta, 0.055, 0.04, PELLE)

def p2():
    hz = 1.05
    porta_testa(hz)
    t = Pezzo('Portatori testa')
    t.box(0.15, 2.3, -0.36, 0.36, 0.98, hz + 0.16, TELA)
    gambe_umane(t, 0.55, 0.2, 1); gambe_umane(t, 1.75, 0.2, -1)
    base = t.fine()
    cima0 = hz + 0.431 * S
    n, lung, vuoto = 5, 1.1, 0.22
    gobba = [0.14, 0.3, 0.3, 0.12, -0.14]
    prec = base
    for i in range(n):
        w = 1.4 - i * 0.11; cima = cima0 + gobba[i]; orlo = 1.1 + i * 0.03
        s = Pezzo('Spicchio%02d' % i)
        s.box(-vuoto, 0.0, -w / 2 + 0.14, w / 2 - 0.14, orlo + 0.12, cima - 0.42, TELA)      # la tela fra uno spicchio e l'altro
        s.blocco(-vuoto - lung / 2, -vuoto, -w / 2, w / 2, orlo, cima)
        s.blocco(-vuoto - lung, -vuoto - lung / 2, -w / 2, w / 2, orlo, cima - 0.15)
        gambe_umane(s, -vuoto - lung / 2, min(0.24, w / 2 - 0.14), 1 if i % 2 else -1)
        prec = s.fine(prec, (0 if i == 0 else -vuoto - lung, 0, 0), 0.17 * math.sin(i * 1.1 + 0.3))
    # coda: due spicchi piccoli senza gambe e la punta
    for i in range(3):
        w = 0.8 - i * 0.2; cima = cima0 - 0.42 - i * 0.26; orlo = 1.26 + i * 0.05
        s = Pezzo('PuntaCoda%d' % i)
        s.box(-0.2, 0.0, -w / 2 + 0.08, w / 2 - 0.08, orlo + 0.08, cima - 0.2, TELA)
        if i < 2: s.blocco(-0.2 - 0.55, -0.2, -w / 2, w / 2, orlo, cima)
        else:
            s.prisma([(-0.2, orlo), (-0.2, cima), (-1.1, orlo + 0.1)], -w / 2, w / 2, SCURO)
            s.tubo([(-0.2, y, cima) for y in (-w / 2, w / 2)], 0.02);
            for y in (-w / 2, w / 2): s.tubo([(-0.2, y, orlo), (-0.2, y, cima), (-1.1, y, orlo + 0.1), (-0.2, y, orlo)], 0.02)
        prec = s.fine(prec, (-vuoto - lung if i == 0 else -0.75, 0, 0), 0.2 * math.sin((n + i) * 1.1 + 0.3))
    return hz

# ─────────────────────────────────────────────────────────────────────────────
# PROPOSTA 3 — L'ANIMALE: un coccodrillo vero, basso e largo, modellato liscio. Del logo tiene i colori, il filo
# bianco lungo il fianco, le unghie bianche e la scalinata: qui sono le scaglie del dorso, a gradini.
# ─────────────────────────────────────────────────────────────────────────────
def p3():
    hz = 0.3
    porta_testa(hz)
    #          x     largh  alt   centro z  squadratura
    staz = [( 0.0,  1.00, 1.16, hz + 0.71, 7.0), (-0.5, 1.6, 1.34, 0.99, 3.6), (-1.5, 2.2, 1.5, 0.98, 2.7),
            (-2.7,  2.1,  1.4, 0.95, 2.5), (-3.6, 1.55, 1.14, 0.88, 2.4), (-4.6, 0.98, 0.86, 0.78, 2.3),
            (-5.8,  0.64, 0.64, 0.66, 2.2), (-7.0, 0.38, 0.44, 0.56, 2.1), (-8.1, 0.14, 0.2, 0.5, 2.0)]
    def a(x):                                                    # sezione interpolata in x (Hermite morbido)
        for (x0, *v0), (x1, *v1) in zip(staz, staz[1:]):
            if x1 <= x <= x0:
                u = (x0 - x) / (x0 - x1); u = u * u * (3 - 2 * u)
                return [p + (q - p) * u for p, q in zip(v0, v1)]
        return list(staz[-1][1:])
    def dy(x):                                                   # la coda fa una S in pianta
        d = max(0.0, -x - 3.4)
        return 0.62 * (d / 4.7) * math.sin(d * 1.05)
    N = 24
    def punto(x, k, fuori=0.0):
        w, h, cz, e = a(x); th = 2 * PI * k / N
        c, s = math.cos(th), math.sin(th)
        py = (w / 2 + fuori) * math.copysign(abs(c) ** (2 / e), c)
        pz = (h / 2 + fuori) * math.copysign(abs(s) ** (2 / e), s) * (0.82 if s < 0 else 1)
        return Vector((x, dy(x) + py, cz + pz))
    xs = [0 - 8.1 * (i / 54) for i in range(55)]
    c = Pezzo('Corpo')
    c.pelle([[punto(x, k) for k in range(N)] for x in xs],
            lambda p, i: MEDIO if p.z < a(xs[i])[2] - 0.2 * a(xs[i])[1] else SCURO)
    # filo bianco lungo il fianco: parte dalla linea della bocca e arriva in punta di coda
    for k in (N - 2, N // 2 + 2):
        c.tubo([punto(x, k, 0.012) for x in xs], 0.024)
    for x in (-4.2, -5.0, -5.8, -6.6, -7.4):                     # anelli bianchi sulla coda
        an = [punto(x, k, 0.01) for k in range(N)]; c.tubo(an + an[:1], 0.018)
    # scaglie del dorso: due file di gradini, alti e bassi come una scala vista di lato
    i = 0
    x = -0.3
    while x > -3.55:
        w, h, cz, e = a(x); alt = 0.1 + 0.07 * (i % 3)
        for lato in (-1, 1):
            y = lato * min(0.34, w * 0.2)
            c.blocco(x - 0.3, x, y - 0.17, y + 0.17, cz + h / 2 - 0.12, cz + h / 2 + alt, t=0.025, sotto=False)
        x -= 0.4; i += 1
    while x > -7.7:                                              # cresta della coda: una fila sola
        w, h, cz, e = a(x); alt = max(0.08, 0.34 * (1 - (-x - 3.5) / 4.6))
        c.blocco(x - 0.26, x, dy(x) - 0.08, dy(x) + 0.08, cz + h / 2 - 0.06, cz + h / 2 + alt, t=0.022, sotto=False)
        x -= 0.4
    # zampe larghe e basse
    for xc, mezza, k in ((-0.95, 0.8, 1.0), (-3.0, 0.86, 1.2)):
        for lato in (-1, 1):
            spalla = Vector((xc, lato * mezza, 0.86)); gomito = Vector((xc - 0.18, lato * (mezza + 0.72 * k), 0.66))
            polso = Vector((xc + 0.32, lato * (mezza + 0.86 * k), 0.16))
            c.cilindro(spalla, gomito, 0.3 * k, 0.22 * k, SCURO, 14); c.cilindro(gomito, polso, 0.22 * k, 0.15 * k, SCURO, 14)
            c.box(polso.x - 0.2, polso.x + 0.45 * k, polso.y - 0.27 * k, polso.y + 0.27 * k, 0.0, 0.17, SCURO, MEDIO)
            for j in range(4):
                yy = polso.y + (j - 1.5) * 0.13 * k
                c.cilindro((polso.x + 0.42 * k, yy, 0.07), (polso.x + 0.42 * k + 0.26, yy + lato * 0.02, 0.02), 0.055, 0.004, BIANCO, 8)
    c.fine()
    return hz

hz = {'p1': p1, 'p2': p2, 'p3': p3}[quale]()
suolo()
bpy.context.view_layer.update()
lo, hi = viste.ingombro(BOSS)
XH = lo.x + 3.2                                                  # il cavallo corre all'altezza della coda
porta_cavallo((XH, -3.0))
bpy.context.view_layer.update()
NOMI = {'p1': 'A - LA SCALINATA', 'p2': 'B - LA PARATA', 'p3': 'C - L\'ANIMALE'}
cu = bpy.data.curves.new('etichetta', 'FONT'); cu.body = NOMI[quale]; cu.size = 0.026
mt = bpy.data.materials.new('scritta'); mt.use_nodes = True
bs = next(n for n in mt.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bs.inputs['Base Color'].default_value = (1, 1, 1, 1); bs.inputs['Emission Color'].default_value = (1, 1, 1, 1); bs.inputs['Emission Strength'].default_value = 1.5
cu.materials.append(mt)
et = bpy.data.objects.new('etichetta', cu); COL.objects.link(et); et.parent = sc.camera
print('%s: lungo %.2f m · largo %.2f · alto %.2f · oggetti %d · triangoli %d' % (
    quale, hi.x - lo.x, hi.y - lo.y, hi.z, len(BOSS),
    sum(len(o.data.polygons) for o in BOSS if o.name != 'Testa') * 2))

def vista_gioco():                                               # come lo vedi arrivandogli da dietro, in sella
    co = sc.camera; co.data.sensor_fit = 'VERTICAL'; co.data.angle = math.radians(62)
    co.location = (XH - 3.4, -3.7, 1.8)
    co.rotation_euler = (Vector((XH + 4.5, -0.7, 1.0)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    co.data.clip_start = 0.05; co.data.clip_end = 200

viste.foglio(os.path.join(out_dir, quale + '-viste.png'), BOSS, viste=((0.8, -0.85, 0.38), 'lato', vista_gioco, (-0.75, 0.8, 0.5)), colonne=2)
viste.foglio(os.path.join(out_dir, quale + '-34.png'), BOSS, viste=((0.8, -0.85, 0.38),), colonne=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, quale + '.blend'))
