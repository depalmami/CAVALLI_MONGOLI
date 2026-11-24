# ATTO 2 · ARMI E LOTTA, animato (storyboard v2): 7 s fra il guado dell'Onon e il Burkhan Khaldun (+ S14, già girato = 9 s).
# EEVEE, render calmo (shot.py). Un colpo per battito, i tagli sui colpi.
#   S08   1,5 s  la cassa scoppia in pannelli di cartone, la sciabola vola girando e la manica la prende al volo; lui se la guarda
#   S09a  0,5 s  la sciabola dritta: un lampo scorre sul filo e scintilla sulla punta (televendita epica)
#   S09b  0,5 s  la mazza: gli spuntoni girano e si fermano di colpo
#   S09c  0,5 s  la frusta: lo schiocco, con la corona di polvere
#   S09d  0,5 s  l'arco: la freccia parte e la camera la segue
#   S10   0,5 s  tele: tre predoni escono dalla polvere uno dietro l'altro (tinte del gioco smorzate)
#   S11   1,5 s  testata contro fendente: scintille e polvere ferme al rallentatore, poi il predone cade RIGIDO come un giocattolo
#   S13a  0,5 s  il rotolo rotola incontro al cavallo: lampo, ed è avvolto nel pluriball
#   S13b  1 s    la mazza di un predone lo colpisce, le bolle scoppiano A CATENA; lui abbassa la testa a guardarsi
# Il montaggio: atto2.mp4 = S08 … S13b + S14 (trailer/blender/shot/S14/S14-finale.mp4, da shot-s14.py).
#
# uso:  blender -b --python tools/trailer3d/shot-atto2.py -- <cartella base> prova|finale [S08 … S13b | monta]
import bpy, bmesh, sys, os, math, random, subprocess
QUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, QUI)
import numpy as np
import animatic as AN
import animatic2 as A2
import pose, avvolto
import cartone as CA
import shot as SH
from shot import curva, sm
from mathutils import Vector, Matrix, Quaternion

ARGV = sys.argv[sys.argv.index('--') + 1:]
BASE = os.path.abspath(ARGV[0]); MODO = ARGV[1] if len(ARGV) > 1 else 'prova'
TUTTI = ['S08', 'S09a', 'S09b', 'S09c', 'S09d', 'S10', 'S11', 'S13a', 'S13b']
LISTA = ARGV[2:] or TUTTI
DUR = dict(S08=36, S09a=12, S09b=12, S09c=12, S09d=12, S10=12, S11=36, S13a=12, S13b=24)
P = A2.P
V = 0.17                                               # m a fotogramma: il galoppo del protagonista senza pattinare
TINTE = dict(arancio='#ffc9a3', azzurro='#a9c8ff', verde='#d6ffb3', rosa='#ffb3d1')
# i nemici: NEMICO=cartone (default) = l'uomo con la testa di cavallo di cartone (cartone.py), NEMICO=cavallo = i predoni low poly di prima
NEMICO = os.environ.get('NEMICO', 'cartone'); ALT_NEMICO = float(os.environ.get('ALT_NEMICO', '1.9'))

def giorno(k, sole_rel, n, **kw):
    SH.prima(MODO, 'EEVEE'); m = A2.mondo(k, sole_rel=sole_rel, **kw); SH.dopo(MODO, 'EEVEE', n); return m

def chiave_striscia(st, f, tempo, influenza=1.0):
    st.strip_time = tempo; st.keyframe_insert('strip_time', frame=f)
    st.influence = influenza; st.keyframe_insert('influence', frame=f)

def avanti(m, x0, y0, yaw, d, lato=0.0, dz=0.0):
    """Il punto a d metri davanti (direzione del cavallo con quel yaw: 0 = -Y) e `lato` a sinistra (+), sul terreno + dz."""
    a = math.radians(yaw)
    x = x0 + math.sin(a) * d + math.cos(a) * lato; y = y0 - math.cos(a) * d + math.sin(a) * lato
    return Vector(P(m, x, y, dz))

def rel(base, yaw, off):
    """base + off girato di yaw (off nel riferimento del cavallo: +X = sua sinistra, -Y = davanti, Z su)."""
    return Vector(base) + Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Vector(off)

def mesh_di(o): return [x for x in [o] + list(o.children_recursive) if x.type == 'MESH']
def appari(o, f):
    for x in mesh_di(o): SH.appari_da(x, f)
def nascondi(o, f):
    for x in mesh_di(o): SH.nascondi_da(x, f)

_QP = {}
def chiave_matrice(o, f, M):
    """Chiava posizione, rotazione (quaternion, sempre nello stesso emisfero: il mosso non fa giri strani) e scala."""
    o.rotation_mode = 'QUATERNION'
    loc, q, s = M.decompose()
    if o.name in _QP and _QP[o.name].dot(q) < 0: q.negate()
    _QP[o.name] = q.copy()
    o.location = loc; o.rotation_quaternion = q; o.scale = s
    for p in ('location', 'rotation_quaternion', 'scale'): o.keyframe_insert(p, frame=f)

def balistico(o, fotogrammi, q0, v0, base, asse, w, quota=None, g=9.81, tempo=None, sopra=0.02, rimbalzo=0.3):
    """Chiava o nei fotogrammi dati: volo con gravità, giro attorno ad `asse` (rad/s), rimbalzo a terra. base = rotazione e
    scala di partenza (4×4 senza traslazione). tempo(f) = fotogrammi della storia (per il rallentatore)."""
    tempo = tempo or (lambda f: f)
    p = Vector(q0); v = Vector(v0); ang = 0.0; t0 = tempo(fotogrammi[0])
    for f in fotogrammi:
        dt = (tempo(f) - t0) / 24.0; t0 = tempo(f)
        for _ in range(6):
            h = dt / 6; v.z -= g * h; p += v * h; ang += w * h
            if quota:
                z0 = quota(p.x, p.y) + sopra
                if p.z < z0: p.z = z0; v.z = -v.z * rimbalzo; v.x *= 0.55; v.y *= 0.55; w *= 0.5
        chiave_matrice(o, f, Matrix.Translation(p) @ Quaternion(asse, ang).to_matrix().to_4x4() @ base)

def emissivo(nome, colore, forza, alfa=None):
    m = bpy.data.materials.new(nome); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = colore; em.inputs['Strength'].default_value = forza
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    if alfa is None: nt.links.new(em.outputs[0], out.inputs['Surface'])
    else:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = alfa
        nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def stella(cam, forza=30.0, nome='stella'):
    """Il lampo «ting»: una stella a quattro punte piatta che guarda sempre la camera (Empty che punta + stella figlia che gira)."""
    bm = bmesh.new(); c = bm.verts.new((0, 0, 0)); pts = []
    for i in range(8):
        a = i * math.pi / 4; r = 1.0 if i % 2 == 0 else 0.11
        pts.append(bm.verts.new((r * math.cos(a), r * math.sin(a), 0)))
    for i in range(8): bm.faces.new((c, pts[i], pts[(i + 1) % 8]))
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free()
    me.materials.append(emissivo('stella', (1.0, 0.97, 0.9, 1), forza))
    perno = bpy.data.objects.new(nome + '_perno', None); bpy.context.scene.collection.objects.link(perno)
    o = bpy.data.objects.new(nome, me); bpy.context.scene.collection.objects.link(o); o.parent = perno
    piccola = bpy.data.objects.new(nome + '_2', me); bpy.context.scene.collection.objects.link(piccola); piccola.parent = o
    piccola.rotation_euler.z = math.pi / 4; piccola.scale = (0.55,) * 3
    k = perno.constraints.new('TRACK_TO'); k.target = cam; k.track_axis = 'TRACK_Z'; k.up_axis = 'UP_Y'
    return perno, o

def predone_vivo(colore, scala=0.46, nome='predone'):
    """Un predone VIVO (horse-quaternius.glb con lo scheletro) con le tinte del gioco smorzate: (radice, armatura, clip)."""
    sc = bpy.context.scene; prima = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=AN.A + 'models/horse-quaternius.glb')
    nuovi = [o for o in bpy.data.objects if o not in prima]
    for o in list(nuovi):
        if o.name.startswith('Icosphere'): bpy.data.objects.remove(o); nuovi.remove(o)
    arm = next(o for o in nuovi if o.type == 'ARMATURE')
    ad = arm.animation_data; az = {}
    for t in list(ad.nla_tracks):
        if t.strips: az.setdefault(t.name.split('|')[-1], t.strips[0].action)
        ad.nla_tracks.remove(t)
    ad.action = None
    tinta = pose.tinta_smorzata(TINTE[colore], 0.35)
    for o in nuovi:
        if o.type == 'MESH':
            for mt in o.data.materials:
                b = next((x for x in mt.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
                if b and not b.inputs['Base Color'].is_linked:
                    c = b.inputs['Base Color'].default_value; b.inputs['Base Color'].default_value = (c[0] * tinta[0], c[1] * tinta[1], c[2] * tinta[2], 1)
    radice = bpy.data.objects.new(nome, None); sc.collection.objects.link(radice)
    for o in nuovi:
        if o.parent is None: o.parent = radice
    radice.scale = (scala,) * 3; radice.rotation_mode = 'XYZ'
    return radice, arm, az

def scossa(f, da, forza, smorza=0.45, freq=2.3):
    if f < da: return Vector()
    u = f - da; return Vector((0, 0, forza * math.exp(-u * smorza) * math.cos(u * freq)))

S = {}
def shot(nome):
    def d(f): S[nome] = f; return f
    return d

# ---------------------------------------------------------------------------------------------------------------- S08
def cassa_in_pezzi(M):
    """La cassa del gioco divisa nelle sue sei facce (ogni faccia del mesh va alla parete più vicina, dentro e fuori insieme),
    ognuna col suo centro: [(oggetto, normale nel mondo)]. M = matrice della cassa nel mondo."""
    r, _ = AN.importa('models/armi/cassa.glb', nome='cassa')
    figli = [o for o in r.children if o.type == 'MESH']
    main = max(figli, key=lambda o: len(o.data.vertices)); me = main.data
    me.transform(main.matrix_world)
    co = np.array([v.co[:] for v in me.vertices]); lo, hi = co.min(axis=0), co.max(axis=0); c = (lo + hi) / 2; h = (hi - lo) / 2
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    gruppi = {}
    for fc in bm.faces:
        cc = np.array(fc.calc_center_median()[:]) - c; a = int(np.argmax(np.abs(cc) / h))
        gruppi.setdefault((a, 1 if cc[a] > 0 else -1), []).append(fc.index)
    bm.free(); pezzi = []
    for (a, s), facce in sorted(gruppi.items()):
        b2 = bmesh.new(); b2.from_mesh(me); b2.faces.ensure_lookup_table()
        tieni = set(facce)
        bmesh.ops.delete(b2, geom=[fc for fc in b2.faces if fc.index not in tieni], context='FACES')
        bmesh.ops.delete(b2, geom=[x for x in b2.verts if not x.link_faces], context='VERTS')
        cen = sum((x.co for x in b2.verts), Vector()) / len(b2.verts)
        for x in b2.verts: x.co -= cen
        nm = bpy.data.meshes.new('pannello'); b2.to_mesh(nm); b2.free()
        for mt in me.materials: nm.materials.append(mt)
        o = bpy.data.objects.new('pannello', nm); bpy.context.scene.collection.objects.link(o)
        o.matrix_world = M @ Matrix.Translation(cen)
        n_loc = Vector((0, 0, 0)); n_loc[a] = s
        pezzi.append((o, (M.to_3x3().normalized() @ n_loc).normalized(), (a, s)))
    for o in [r] + figli: bpy.data.objects.remove(o)
    return pezzi

@shot('S08')
def s08():
    n = DUR['S08']; m = giorno(1, 170, n)
    E, G = 6, 22                                        # la cassa scoppia al 6, la manica prende la sciabola al 22
    yaw = A2.yaw_su(m, 0, -2.0)
    radice, rig, az = pose.eroe_vivo('eroe'); radice.rotation_mode = 'XYZ'
    gal = pose.traccia(rig, az['Gallop']); aff = pose.traccia(rig, az['Afferra']); alta = pose.traccia(rig, az['Sciabola_Alta'])
    sgu = pose.traccia(rig, az['Sguardo_D'], 'COMBINE')
    sciabola = pose.arma_viva(rig, 'saber')
    D_CASSA = 2.0                                       # la cassa sta 2 m avanti; il petto (0,62 m davanti alla radice) ci arriva al 6
    D0 = D_CASSA - 0.62 - 0.35 - V * (E - 1)
    radici = {}
    for f in range(1, n + 1):
        radici[f] = avanti(m, 0, 0, yaw, D0 + V * (f - 1))
        radice.location = radici[f]; radice.rotation_euler = (0, 0, math.radians(yaw))
        radice.keyframe_insert('location', frame=f); radice.keyframe_insert('rotation_euler', frame=f)
        chiave_striscia(gal, f, 3.0 + (f - 1))
        chiave_striscia(aff, f, curva([(1, 1.0), (G - 7, 1.0), (G, 8.0), (G + 4, 10.0), (n, 10.0)], f))
        chiave_striscia(alta, f, 12.0, curva([(1, 0.0), (G + 3, 0.0), (G + 11, 1.0), (n, 1.0)], f))
        chiave_striscia(sgu, f, 9.0, curva([(1, 0.0), (G + 5, 0.0), (G + 13, 0.7), (n, 0.7)], f))
    # --- la cassa: sei pannelli fermi fino al 6, poi in volo (il cavallo la sfonda: i pezzi volano avanti, di lato e in alto)
    k = 0.7; centro = avanti(m, 0, 0, yaw, D_CASSA, dz=0.409 * k)
    Mc = Matrix.Translation(centro) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Scale(k, 4)
    random.seed(8)
    Ry = Matrix.Rotation(math.radians(yaw), 3, 'Z')
    for o, nw, (a, s) in cassa_in_pezzi(Mc):
        base = o.matrix_world.copy(); base.translation = Vector()
        q0 = o.matrix_world.translation.copy()
        chiave_matrice(o, 1, o.matrix_world); chiave_matrice(o, E - 1, o.matrix_world)
        if a == 2 and s > 0:   v = Ry @ Vector((random.uniform(-0.6, 0.6), -1.6, 5.2))          # coperchio: in alto
        elif a == 2:           v = Ry @ Vector((0.0, -1.2, 0.4))                                  # fondo: striscia avanti
        elif a == 1 and s > 0: v = Ry @ Vector((random.choice((-1, 1)) * 1.4, -4.6, 4.2))         # parete dal lato del cavallo: scavalca
        elif a == 1:           v = Ry @ Vector((random.uniform(-0.8, 0.8), -4.8, 2.4))            # parete davanti: avanti
        else:                  v = nw * 3.6 + Ry @ Vector((0, -2.0, 2.9))                         # fianchi: in fuori
        asse = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized()
        balistico(o, list(range(E, n + 1)), q0, v, base, asse, random.uniform(7, 14), quota=m.quota, sopra=0.015)
    # trucioli di cartone e polvere
    cart = AN.materiale('cartone', colore=AN.hexc('#b98a55'), rough=0.9)
    for i in range(22):
        dim = (random.uniform(0.04, 0.10), 0.004, random.uniform(0.03, 0.08))
        o = AN.scatola(centro, dim, cart)
        base = Matrix.Diagonal((*dim, 1.0))
        chiave_matrice(o, E - 1, Matrix.Translation(centro) @ Matrix.Diagonal((0.001, 0.001, 0.001, 1.0)))
        d = Vector((random.gauss(0, 1), random.gauss(0, 1) - 0.8, abs(random.gauss(0, 1)) + 0.5)).normalized()
        balistico(o, list(range(E, n + 1)), centro + d * 0.2, Ry @ (d * random.uniform(3, 6)), base,
                  Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized(), random.uniform(10, 25), quota=m.quota, sopra=0.005)
    polv = AN.materiale_polvere((0.74, 0.60, 0.44, 1), 0.18)
    for i in range(26):
        d = Vector((random.gauss(0, 1), random.gauss(0, 1), abs(random.gauss(0, 0.5)))).normalized()
        SH.sbuffo(centro + d * 0.3 - Vector((0, 0, 0.15)), E + random.randrange(3), polv, random.uniform(0.15, 0.32),
                  Ry @ (d * random.uniform(0.6, 1.4) + Vector((0, -0.6, 0.3))), vita=16, n=n)
    # --- la sciabola in volo: dalla cassa alla mano, girando come una ruota, e arriva ESATTAMENTE dov'è la presa al 22
    sc = bpy.context.scene; sc.frame_set(G); bpy.context.view_layer.update()
    WG = sciabola.matrix_world.copy(); cG = WG @ Vector((0, 0, 0.221))           # centro della lama (lunghezza del GLB su +Z)
    c0 = centro + Vector((0, 0, 0.15)); T = (G - E) / 24.0; gg = 20.0              # gravità da cartone: sale e ricade svelta
    v0 = (cG - c0) / T + Vector((0, 0, 0.5 * gg * T))
    volo, _ = AN.importa('models/armi/saber.glb', nome='sciabola_volo')
    asse = (Ry @ Vector((0.25, -1.0, 0.15))).normalized(); giri = -2.25 * 2 * math.pi
    for f in [1] + list(range(E, G + 1)):
        u = max(0.0, (f - E) / (G - E)); t = max(0.0, (f - E) / 24.0)
        c = c0 + v0 * t + Vector((0, 0, -0.5 * gg * t * t))
        R = Quaternion(asse, giri * (1 - u) ** 1.6).to_matrix().to_4x4()
        chiave_matrice(volo, f, Matrix.Translation(c) @ R @ Matrix.Translation(-cG) @ WG)
    appari(volo, E); nascondi(volo, G); appari(sciabola, G)
    # --- camera sopra la spalla destra, che segue il cavallo; guarda su quando la sciabola vola, trema allo scoppio
    cam = AN.camera(rel(radici[1], yaw, (-0.95, 1.35, 2.05)), rel(radici[1], yaw, (-0.42, -1.0, 1.75)), 24)
    for f in range(1, n + 1):
        su = curva([(1, 0.0), (E, 0.0), (E + 8, 0.55), (G, 0.3), (n, 0.4)], f)
        SH.chiave_camera(cam, f, rel(radici[f], yaw, (-0.95, 1.35, 2.05)) + scossa(f, E, 0.03),
                         rel(radici[f], yaw, (-0.42, -1.0, 1.75 + su)))

# ---------------------------------------------------------------------------------------------------------------- S09
def vetrina(n):
    return giorno(1, -30, n, pezzi=False)

def camera_vetrina(m, cz, n, lens=55, fstop=2.0, orbita=10.0, colpo=None, forza=0.01):
    """Camera della televendita: un lento giro di `orbita` gradi attorno all'arma e un poco più vicina; colpo = fotogramma
    in cui la camera sobbalza (il «tac» della mazza, lo schiocco della frusta)."""
    centro = Vector(P(m, 0, 0, cz)); r0 = Vector((-1.5, -2.3)); a0 = math.atan2(r0.y, r0.x)
    cam = AN.camera(P(m, r0.x, r0.y, cz + 0.1), centro, lens, fstop=fstop, fuoco=centro)
    for f in range(1, n + 1):
        k = (f - 1) / (n - 1); a = a0 + math.radians(-orbita / 2 + orbita * k); rr = r0.length * (1 - 0.08 * k)
        pos = Vector((rr * math.cos(a), rr * math.sin(a), centro.z + 0.1))
        if colpo: pos += scossa(f, colpo, forza, 0.6, 3.0)
        SH.chiave_camera(cam, f, pos, centro, fuoco=(centro - pos).length)
    return cam

def punti_arma(o):
    """Vertici dell'arma: (coordinate del GLB, mondo)."""
    bpy.context.view_layer.update()
    Ri = o.matrix_world.inverted(); loc, mondo = [], []
    for x in mesh_di(o):
        for v in x.data.vertices:
            w = x.matrix_world @ v.co; mondo.append(w); loc.append(Ri @ w)
    return loc, mondo

@shot('S09a')
def s09a():
    n = DUR['S09a']; m = vetrina(n); k = 1.5
    arma = AN.oggetto('models/armi/saber.glb', P(m, 0, 0, 1.0), rot=(8, 0, 12), scala=k, nome='arma')
    cam = camera_vetrina(m, 1.0 + 0.5 * 0.85 * k, n)
    # il filo della lama: a ogni altezza, il punto più a destra nel quadro
    destra = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
    loc, mondo = punti_arma(arma); filo = []
    for i in range(18):
        z0 = 0.07 + (0.62 - 0.07) * i / 17
        fascia = [w for l, w in zip(loc, mondo) if abs(l.z - z0) < 0.02]
        if fascia: filo.append(max(fascia, key=lambda w: w.dot(destra)))
    perno, st = stella(cam)
    for f in range(1, n + 1):
        u = sm((f - 2) / 6.0); x = u * (len(filo) - 1); i = min(len(filo) - 2, int(x))
        pos = filo[i].lerp(filo[i + 1], x - i) + destra * 0.004
        if f < 2: s = 0.001
        elif f <= 8: s = 0.035 + 0.035 * math.sin(math.pi * u)
        else: s = 0.035 + 0.13 * math.sin(math.pi * min(1.0, (f - 8) / 4.0)) ** 0.7
        perno.location = pos; perno.scale = (max(0.001, s),) * 3
        perno.keyframe_insert('location', frame=f); perno.keyframe_insert('scale', frame=f)
        st.rotation_euler.z = math.radians(8 * f); st.keyframe_insert('rotation_euler', frame=f)

@shot('S09b')
def s09b():
    n = DUR['S09b']; m = vetrina(n); k = 1.5
    perno = bpy.data.objects.new('perno', None); bpy.context.scene.collection.objects.link(perno)
    perno.location = P(m, 0, 0, 1.0); perno.rotation_euler = (math.radians(6), 0, math.radians(-18))
    arma = AN.oggetto('models/armi/mace.glb', (0, 0, 0), scala=k, nome='arma'); arma.parent = perno
    giro = [(1, 0.0), (2, 0.0), (8, 290.0), (9, 283.0), (10, 288.0), (n, 287.0)]      # gira, si ferma di colpo, tac
    for f in range(1, n + 1):
        arma.rotation_euler = (0, 0, math.radians(curva(giro, f))); arma.keyframe_insert('rotation_euler', frame=f)
    camera_vetrina(m, 1.0 + 0.5 * 0.60 * k, n, colpo=8, forza=0.008)               # un colpetto della camera sul «tac»

@shot('S09c')
def s09c():
    n = DUR['S09c']; m = vetrina(n); k = 1.5; SCH = 6
    perno = bpy.data.objects.new('perno', None); bpy.context.scene.collection.objects.link(perno)
    perno.location = P(m, 0, 0, 1.0 - 0.139 * k); perno.rotation_euler = (math.radians(4), 0, math.radians(12))
    arma = AN.oggetto('models/armi/whip.glb', (0, 0, 0.139 * k), scala=k, nome='arma'); arma.parent = perno
    # il colpo di polso: indietro, poi avanti di scatto (lo schiocco al 6), un rimbalzo; piccolo, perché il ricciolo resti in quadro
    for f in range(1, n + 1):
        perno.rotation_euler = (math.radians(4), math.radians(curva([(1, 0), (4, 5), (SCH, -7), (8, -3), (10, -4.5), (n, -4)], f)), math.radians(12))
        perno.keyframe_insert('rotation_euler', frame=f)
    cam = camera_vetrina(m, 1.0 + 0.5 * 1.0 * k, n, colpo=SCH, forza=0.012)
    bpy.context.scene.frame_set(SCH); bpy.context.view_layer.update()
    loc, mondo = punti_arma(arma)
    ricciolo = [i for i in range(len(loc)) if loc[i].x < -0.15]
    punta = mondo[min(ricciolo, key=lambda i: loc[i].z)]                            # il nodo in fondo al ricciolo: la fine della frusta
    # la corona di polvere: un anello di sbuffi che si allarga nel piano del quadro, un'onda d'urto chiara e il lampo dello schiocco
    dx, su = cam.matrix_world.to_3x3() @ Vector((1, 0, 0)), cam.matrix_world.to_3x3() @ Vector((0, 1, 0))
    polv = AN.materiale_polvere((0.78, 0.66, 0.50, 1), 0.22)
    for i in range(30):
        a = 2 * math.pi * i / 30; d = dx * math.cos(a) + su * math.sin(a)
        SH.sbuffo(punta + d * 0.03, SCH, polv, 0.016, d * 0.24 + Vector((0, 0, 0.03)), vita=7, n=n)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.025, major_segments=48, minor_segments=6)
    onda = bpy.context.object; onda.data.materials.append(emissivo('onda', (1.0, 0.97, 0.9, 1), 3.0, alfa=0.45))
    k_o = onda.constraints.new('TRACK_TO'); k_o.target = cam; k_o.track_axis = 'TRACK_Z'; k_o.up_axis = 'UP_Y'
    onda.location = punta
    for f, s in ((1, 0.001), (SCH - 1, 0.001), (SCH, 0.05), (SCH + 1, 0.14), (SCH + 2, 0.22), (SCH + 3, 0.27), (SCH + 4, 0.001)):
        onda.scale = (s,) * 3; onda.keyframe_insert('scale', frame=f)
    perno_s, st = stella(cam, forza=40)
    for f in range(1, n + 1):
        s = {SCH: 0.16, SCH + 1: 0.09, SCH + 2: 0.03}.get(f, 0.001)
        perno_s.location = punta; perno_s.scale = (s,) * 3; perno_s.keyframe_insert('location', frame=f); perno_s.keyframe_insert('scale', frame=f)

def segmento(o, f, a, b, r):
    """Un cilindro (raggio 1, alto 2, lungo Z) messo fra a e b, chiavato al fotogramma f."""
    d = b - a; q = d.to_track_quat('Z', 'Y')
    chiave_matrice(o, f, Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4() @ Matrix.Diagonal((r, r, d.length / 2, 1)))

@shot('S09d')
def s09d():
    n = DUR['S09d']; m = vetrina(n); k = 1.5; VIA = 4
    perno = bpy.data.objects.new('perno', None); bpy.context.scene.collection.objects.link(perno)
    perno.location = P(m, 0, 0, 1.0)
    arco = AN.oggetto('models/armi/bow.glb', (0, 0, 0), scala=k, nome='arco'); arco.parent = perno
    loc, _ = punti_arma(arco)
    cima = max(loc, key=lambda p: p.z); fondo = min(loc, key=lambda p: p.z)
    presa = sum((p for p in loc if abs(p.z) < 0.04), Vector()) / max(1, sum(1 for p in loc if abs(p.z) < 0.04))
    corda_y = (cima.y + fondo.y) / 2
    # via la corda del modello (dritta da punta a punta, quindi a riposo): la rifaccio io, tirata
    asse_c = (fondo - cima).normalized(); Ri = arco.matrix_world.inverted(); tolti = 0
    for x in mesh_di(arco):
        bm = bmesh.new(); bm.from_mesh(x.data); M = Ri @ x.matrix_world
        via = []
        for v in bm.verts:
            p = M @ v.co; q = p - cima; dist = (q - asse_c * q.dot(asse_c)).length
            if dist < 0.05 and abs(p.z) < 0.40: via.append(v)
        bmesh.ops.delete(bm, geom=via, context='VERTS'); bm.to_mesh(x.data); bm.free(); tolti += len(via)
    print('S09d: tolti %d vertici della corda del modello' % tolti)
    avanti_loc = Vector((0, -1 if corda_y > presa.y else 1, 0))                     # la freccia va dalla corda verso l'impugnatura
    # la camera guarda da (-1,5, -2,3) verso l'arco: la freccia deve partire verso destra nel quadro e un po' lontano (~ +X)
    yawp = math.atan2(0.06, 1.0) - math.atan2(avanti_loc.y, avanti_loc.x)
    perno.rotation_euler = (0, 0, yawp)
    bpy.context.view_layer.update()
    Mp = perno.matrix_world; Mk = Mp @ Matrix.Scale(k, 4)
    dirw = (Mp.to_3x3() @ avanti_loc).normalized()
    a_w, b_w = Mk @ Vector((cima.x, corda_y, cima.z)), Mk @ Vector((fondo.x, corda_y, fondo.z))
    corda0 = Mk @ Vector((presa.x, corda_y, presa.z))
    # la corda (rifatta: quella del modello pende), tirata indietro fino allo scocco, poi vibra
    mc = AN.materiale('corda', colore=(0.10, 0.07, 0.05, 1), rough=0.8)
    corde = []
    for i in range(2):
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, vertices=8); c = bpy.context.object; c.data.materials.append(mc); corde.append(c)
    freccia = AN.oggetto('models/armi/freccia.glb', (0, 0, 0), scala=1.3, nome='freccia')
    L = 1.3                                                                          # lunghezza della freccia (GLB ±0,5 m × 1,3)
    tirata = 0.34
    for f in range(1, n + 1):
        if f < VIA: tiro = tirata + 0.006 * math.sin(f * 2.1)
        else: tiro = {VIA: 0.0, VIA + 1: -0.05, VIA + 2: 0.025, VIA + 3: -0.012}.get(f, 0.0)
        cocca = corda0 - dirw * tiro
        segmento(corde[0], f, a_w, cocca, 0.0035); segmento(corde[1], f, cocca, b_w, 0.0035)
        corsa = 0.0 if f < VIA else 0.5 * (f - VIA + 0.4) ** 1.25                     # parte e accelera
        coda = (corda0 - dirw * tirata) if f < VIA else corda0 + dirw * corsa
        q = dirw.to_track_quat('Z', 'Y')
        chiave_matrice(freccia, f, Matrix.Translation(coda + dirw * L / 2) @ q.to_matrix().to_4x4() @ Matrix.Scale(1.3, 4))
    # la camera parte sull'arco e insegue la freccia
    centro = Vector(P(m, 0, 0, 1.0)); r0 = Vector((-1.5, -2.3)); cam0 = Vector(P(m, r0.x, r0.y, 0)); cam0.z = centro.z + 0.1
    cam = AN.camera(cam0, centro, 50, fstop=2.0, fuoco=centro)
    for f in range(1, n + 1):
        corsa = 0.0 if f < VIA else 0.5 * (f - VIA + 0.4) ** 1.25
        punta = corda0 + dirw * (corsa + L * 0.6)
        w = sm((f - VIA + 1) / 3.0)
        mira = centro.lerp(punta, w)
        pos = cam0 + dirw * corsa * 0.93 * sm((f - VIA) / 3.0)                      # le va dietro: la freccia resta grande, il mondo scorre
        SH.chiave_camera(cam, f, pos, mira, fuoco=(mira - pos).length)

# ---------------------------------------------------------------------------------------------------------------- S10
@shot('S10')
def s10():
    n = DUR['S10']; m = giorno(1, -25, n); VR = 0.26
    random.seed(10); polv = AN.materiale_polvere((0.46, 0.38, 0.29, 1), 0.07)
    # in fila: dalla camera alta col tele, quelli dietro stanno più su nel quadro (uno sopra l'altro, come in una pila)
    for i, (col, x, y0, t0) in enumerate((('arancio', -0.35, 6.0, 0.0), ('azzurro', 0.55, 11.5, 1.6), ('verde', -0.1, 17.0, 2.6))):
        if NEMICO == 'cartone': r, arm, az = CA.predone_cartone(col, ALT_NEMICO, 'p%d' % i)
        else: r, arm, az = predone_vivo(col, nome='p%d' % i)
        st = pose.traccia(arm, az['Gallop'])
        for f in range(1, n + 1):
            y = y0 - VR * (f - 1)
            r.location = P(m, x, y); r.rotation_euler = (0, 0, math.radians(A2.yaw_su(m, x, y)))
            r.keyframe_insert('location', frame=f); r.keyframe_insert('rotation_euler', frame=f)
            chiave_striscia(st, f, CA.tempo_corsa(arm, VR, f, 1.0 + 8.0 * i) if NEMICO == 'cartone' else t0 + (f - 1))
            if f % 2 == i % 2:
                for _ in range(2):
                    SH.sbuffo(Vector(P(m, x + random.uniform(-0.4, 0.4), y + random.uniform(0.6, 1.4), 0.2)), f, polv,
                              random.uniform(0.25, 0.5), (random.uniform(-0.3, 0.3), random.uniform(0.4, 0.9), random.uniform(0.2, 0.5)), vita=16, n=n)
        # la polvere da cui esce: sbuffi fermi davanti a lui, che attraversa
        for _ in range(8):
            SH.sbuffo(Vector(P(m, x + random.uniform(-0.9, 0.9), y0 - random.uniform(0.0, 1.4), random.uniform(0.3, 1.6))), 1, polv,
                      random.uniform(0.4, 0.7), (random.uniform(-0.2, 0.2), random.uniform(-0.1, 0.3), random.uniform(0.05, 0.25)), vita=24, n=n)
    AN.polvere(P(m, 0, 23, 1.0), n=45, raggio=6, size=(0.7, 1.4), colore=(0.46, 0.38, 0.29, 1), alfa=0.04, schiaccia=0.35)
    AN.camera(P(m, 0.15, -14.0, 3.0), P(m, 0.05, 11.0, 0.9), 135)

# ---------------------------------------------------------------------------------------------------------------- S11
def rallenty(n, da, a, lento=1 / 6.0, rampa=2.0):
    """Il tempo della storia: 1 fotogramma per fotogramma, ma fra `da` e `a` va a `lento` (con rampe morbide)."""
    def vel(x):
        if x < da - rampa or x > a + rampa: return 1.0
        if x < da: return 1 + (lento - 1) * sm((x - (da - rampa)) / rampa)
        if x <= a: return lento
        return lento + (1 - lento) * sm((x - a) / rampa)
    s = [0.0, 1.0]
    for f in range(1, n + 2): s.append(s[-1] + vel(f + 0.5))
    def tempo(f):
        i = max(1, min(n + 1, int(math.floor(f)))); return s[i] + (s[i + 1] - s[i]) * (f - i)
    return tempo

@shot('S11')
def s11():
    n = DUR['S11']; m = giorno(2, 210, n)
    tempo = rallenty(n, 10, 20)
    S_COLPO = 10.0                                      # nel tempo della storia: il fendente (clip 11) incontra la testata
    F_COLPO = min(range(1, n + 1), key=lambda f: abs(tempo(f) - S_COLPO))
    yaw = A2.yaw_su(m, 0, -2.0)
    radice, rig, az = pose.eroe_vivo('eroe'); radice.rotation_mode = 'XYZ'
    gal = pose.traccia(rig, az['Gallop']); fen = pose.traccia(rig, az['Sciabola_Fendente'])
    pose.arma_viva(rig, 'saber')
    eroe = lambda s: avanti(m, 0, 0, yaw, V * (s - 1))
    for f in range(1, n + 1):
        s = tempo(f)
        radice.location = eroe(s); radice.rotation_euler = (0, 0, math.radians(yaw))
        radice.keyframe_insert('location', frame=f); radice.keyframe_insert('rotation_euler', frame=f)
        chiave_striscia(gal, f, 3.0 + (s - 1)); chiave_striscia(fen, f, min(24.0, s + 1.0))
    sc = bpy.context.scene; sc.frame_set(F_COLPO); bpy.context.view_layer.update()
    pb = rig.pose.bones['presa.R']; punta = rig.matrix_world @ (pb.matrix @ Vector((0, 0.78, 0)))
    # --- il predone: arriva di traverso (37° verso il cavallo), abbassa la testa, testata contro la lama; poi RIGIDO e giù di lato
    CART = NEMICO == 'cartone'
    if CART: r, arm, azr = CA.predone_cartone('azzurro', ALT_NEMICO, 'rivale', z_colpo=punta.z - m.quota(punta.x, punta.y))
    else: r, arm, azr = predone_vivo('azzurro', nome='rivale')
    gr = pose.traccia(arm, azr['Gallop']); hb = pose.traccia(arm, azr['Attack_Headbutt']); fermo = pose.traccia(arm, azr['Idle'])
    YAWR = yaw + 36.9; ar = math.radians(YAWR); dirr = Vector((math.sin(ar), -math.cos(ar), 0))
    SR = V / 0.8                                        # così, visto dal cavallo, arriva dritto di lato
    testa = arm['testa_d'] if CART else 0.46 * 2.85       # la testa a metà testata sta 1,31 m davanti alla radice (cavallo) / dove la porta l'affondo (uomo)
    r_colpo = Vector((punta.x, punta.y, 0)) - dirr * testa
    def pos_rivale(s):
        if s <= S_COLPO: p = r_colpo - dirr * SR * (S_COLPO - s)
        else: p = r_colpo - dirr * 0.45 * (1 - math.exp(-(s - S_COLPO) / 2.0))          # respinto all'indietro
        return Vector((p.x, p.y, m.quota(p.x, p.y)))
    S_CADE, S_GIU = 11.2, 16.0
    def giro(s):                                        # gradi di ribaltamento sul fianco destro (lontano dal cavallo)
        if s < S_CADE: return 0.0
        if s < S_GIU: return 90.0 * ((s - S_CADE) / (S_GIU - S_CADE)) ** 2
        return 90.0 - 7.0 * math.sin(math.pi * min(1.0, (s - S_GIU) / 2.2))
    perno = Vector((-0.11, 0, 0)) if CART else Vector((-0.30, 0, 0))     # lo spigolo su cui si ribalta (metà larghezza del ventre / il bordo del piede)
    SCR = 1.0 if CART else 0.46
    for f in range(1, n + 1):
        s = tempo(f)
        chiave_striscia(gr, f, CA.tempo_corsa(arm, SR, s, 1.0) if CART else min(13.5, 1.0 + (s - 1)))
        chiave_striscia(hb, f, max(0.0, min(24.0, s + 1.5)), curva([(1, 0.0), (4.0, 0.0), (7.0, 1.0), (40, 1.0)], s))
        chiave_striscia(fermo, f, 0.0, curva([(1, 0.0), (10.4, 0.0), (11.1, 1.0), (40, 1.0)], s))
        M = (Matrix.Translation(pos_rivale(s)) @ Matrix.Rotation(ar, 4, 'Z') @ Matrix.Translation(perno)
             @ Matrix.Rotation(math.radians(-giro(s)), 4, 'Y') @ Matrix.Translation(-perno) @ Matrix.Scale(SCR, 4))
        chiave_matrice(r, f, M)
    # --- le scintille e la luce del colpo, al rallentatore (tutto nel tempo della storia)
    random.seed(11)
    scint = emissivo('scintilla', (1.0, 0.78, 0.45, 1), 40)
    luce = AN.lampada(punta, colore='#ffd9a0', energia=0, raggio=0.1)
    for f in range(1, n + 1):
        s = tempo(f); luce.data.energy = 0.0 if s < S_COLPO else 350 * math.exp(-(s - S_COLPO) * 1.6)
        luce.data.keyframe_insert('energy', frame=f)
    for i in range(70):
        o = AN.sfera(punta, random.uniform(0.006, 0.014), scint, 'scintilla')
        d = Vector((random.gauss(0, 1), random.gauss(0, 1), abs(random.gauss(0, 1)) * 0.8)).normalized(); vv = d * random.uniform(2.0, 6.0)
        vita = random.uniform(0.22, 0.4)
        for f in range(1, n + 1):
            t = (tempo(f) - S_COLPO) / 24.0
            if t < 0 or t > vita: o.scale = (0.0001,) * 3; o.location = punta
            else: o.location = punta + vv * t + Vector((0, 0, -4.9 * t * t)); o.scale = (1 - (t / vita) ** 2,) * 3
            o.keyframe_insert('location', frame=f); o.keyframe_insert('scale', frame=f)
    # --- la polvere ferma: sbuffi sollevati prima del colpo che al rallentatore restano sospesi
    polv = AN.materiale_polvere((0.70, 0.58, 0.44, 1), 0.16)
    def sbuffo_storia(q, s0, r0, deriva, vita=14.0):
        o = AN.sfera(q, 1.0, polv, 'sbuffo')
        for f in range(1, n + 1):
            u = (tempo(f) - s0) / vita
            if u < 0: o.scale = (0.001,) * 3; o.location = q
            else:
                u = min(1.0, u); o.scale = (r0 * (0.4 + 0.6 * min(1.0, u * 5) + 0.8 * u),) * 3; o.location = Vector(q) + Vector(deriva) * u
            o.keyframe_insert('location', frame=f); o.keyframe_insert('scale', frame=f)
    for s0 in np.arange(3.0, 13.0, 0.5):
        for p in (eroe(s0), pos_rivale(s0)):
            q = p + Vector((random.uniform(-0.4, 0.4), random.uniform(-0.3, 0.6), 0.15))
            sbuffo_storia(q, s0, random.uniform(0.12, 0.22), (random.uniform(-0.3, 0.3), random.uniform(0.2, 0.8), random.uniform(0.15, 0.4)))
    # il tonfo: polvere lungo il fianco quando arriva a terra
    pg = pos_rivale(S_GIU); lato = Matrix.Rotation(ar, 3, 'Z') @ Vector((-1, 0, 0))
    for i in range(22):
        q = pg + lato * random.uniform(0.6, 1.6) + dirr * random.uniform(-1.2, 1.2) + Vector((0, 0, 0.1))
        sbuffo_storia(q, S_GIU + random.uniform(0, 0.6), random.uniform(0.15, 0.3), (random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), random.uniform(0.2, 0.5)), vita=10)
    # --- camera davanti a sinistra che accompagna il cavallo; dopo il colpo RALLENTA e si ferma sul predone che cade (la battuta
    # è lui, rigido a terra), mentre il cavallo continua e le passa accanto
    F_GIU = min(range(1, n + 1), key=lambda f: abs(tempo(f) - S_GIU))
    def s_cam(s):                                       # il tempo della camera: segue fino a 11, poi frena e si ferma a 15
        if s <= 11: return s
        u = min(1.0, (s - 11) / 8.0); return 11 + 8.0 * (u - u * u / 2)
    # (da dove sta la camera, il predone caduto finisce esattamente DIETRO il cavallo: quindi dopo il colpo la camera scivola anche
    # di lato, verso destra del cavallo, e alla fine il cavallo esce a destra mentre il predone resta a terra a sinistra del centro)
    cam = AN.camera(rel(eroe(1), yaw, (2.6, -5.6, 1.3)), rel(eroe(1), yaw, (-0.6, 0.3, 0.95)), 30)
    if CART:                                            # il rivale è controluce e viene scuro: una luce frontale (dalla camera) che illumina SOLO lui
        fl = bpy.data.lights.new('riempimento_rivale', 'SUN'); fl.energy = float(os.environ.get('RIEMP_RIVALE', 12.0)); fl.color = (1.0, 0.95, 0.88); fl.angle = math.radians(15); fl.use_shadow = False
        fo = bpy.data.objects.new('riempimento_rivale', fl); bpy.context.scene.collection.objects.link(fo); fo.parent = cam
        fc = bpy.data.collections.new('riempimento_rivale_riceve')
        for x in r.children_recursive: fc.objects.link(x) if x.type == 'MESH' else None
        fo.light_linking.receiver_collection = fc
    for f in range(1, n + 1):
        s = tempo(f); w = 0.92 * sm((s - 11) / 7.0); lat = 2.6 - 3.0 * sm((s - 11) / 9.0)
        mira = rel(eroe(s_cam(s)), yaw, (-0.6, 0.3, 0.95)).lerp(pos_rivale(s) + Vector((0, 0, 0.5)), w)
        SH.chiave_camera(cam, f, rel(eroe(s_cam(s)), yaw, (lat, -5.6, 1.3)) + scossa(f, F_GIU, 0.04, 0.5), mira)
    print('S11: colpo al fotogramma %d, tonfo al %d' % (F_COLPO, F_GIU))
    if CART: print('S11: affondo %.2f, il muso a %.2f m dal suolo e a %.2f m dalla radice (lama a %.2f m)' % (arm['inch'], arm['muso_z'], arm['testa_d'], punta.z - m.quota(punta.x, punta.y)))

# ---------------------------------------------------------------------------------------------------------------- S13a
@shot('S13a')
def s13a():
    n = DUR['S13a']; m = giorno(2, -170, n); FL = 6
    yaw = A2.yaw_su(m, 0, -2.0)
    radice, rig, az = pose.eroe_vivo('eroe'); radice.rotation_mode = 'XYZ'
    pony = avvolto.avvolgi(rig, az)
    gal = pose.traccia(rig, az['Gallop'])
    D0 = -0.2; eroe = lambda f: avanti(m, 0, 0, yaw, D0 + V * (f - 1))
    for f in range(1, n + 1):
        radice.location = eroe(f); radice.rotation_euler = (0, 0, math.radians(yaw))
        radice.keyframe_insert('location', frame=f); radice.keyframe_insert('rotation_euler', frame=f)
        chiave_striscia(gal, f, 6.0 + (f - 1))
    avvolto.mostra(pony, rig, FL + 1)
    # il rotolo gli rotola incontro (asse di traverso alla strada) e lo tocca al 6
    k = 1.6; R = 0.3 * k; VR = 0.09
    rot = AN.oggetto('models/pluriball/rotolo.glb', (0, 0, 0), scala=k, nome='rotolo'); rot.rotation_mode = 'XYZ'
    d_tocco = D0 + V * (FL - 1) + 0.62 + R
    for f in range(1, FL + 1):
        d = d_tocco + VR * (FL - f)
        rot.location = avanti(m, 0, 0, yaw, d, dz=R); rot.rotation_euler = (0, (d_tocco + VR * FL - d) / R, math.radians(yaw + 90))
        rot.keyframe_insert('location', frame=f); rot.keyframe_insert('rotation_euler', frame=f)
    nascondi(rot, FL + 1)
    # LAMPO: una palla di luce bianca che si apre e svanisce, una luce vera per un attimo, bolle che volano via
    c = avanti(m, 0, 0, yaw, D0 + V * (FL - 1) + 0.75, dz=0.8)
    palla = AN.sfera(c, 1.0, emissivo('lampo', (1, 1, 1, 1), 12.0, alfa=0.6), 'lampo')
    for f, s in ((1, 0.001), (FL - 1, 0.001), (FL, 0.5), (FL + 1, 0.9), (FL + 2, 0.001)):
        palla.scale = (s,) * 3; palla.keyframe_insert('scale', frame=f)
    luce = AN.lampada(c, colore='#ffffff', energia=0, raggio=0.5)
    for f, e in ((1, 0), (FL - 1, 0), (FL, 5000), (FL + 1, 2200), (FL + 2, 600), (FL + 3, 0)):
        luce.data.energy = e; luce.data.keyframe_insert('energy', frame=f)
    random.seed(13); mb = avvolto._mat_bolla()
    for i in range(36):
        d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized()
        SH.sbuffo(c + d * 0.3, FL + 1, mb, random.uniform(0.02, 0.045), d * random.uniform(0.8, 1.8), vita=6, n=n, nome='bolla')
    # camera bassa di lato (a destra del cavallo): il rotolo e il cavallo si vengono incontro e si vedono tutti e due
    cp, cm = rel(avanti(m, 0, 0, yaw, 1.55), yaw, (-3.8, 0.0, 0.55)), avanti(m, 0, 0, yaw, 1.55, dz=0.75)
    cam = AN.camera(cp, cm, 30)
    for f in range(1, n + 1):
        SH.chiave_camera(cam, f, cp + scossa(f, FL, 0.02, 0.6), cm)

# ---------------------------------------------------------------------------------------------------------------- S13b
@shot('S13b')
def s13b():
    n = DUR['S13b']; m = giorno(2, -130, n); FI = 6
    yaw = A2.yaw_su(m, 0, -2.0)
    radice, rig, az = pose.eroe_vivo('eroe'); radice.rotation_mode = 'XYZ'
    pony = avvolto.avvolgi(rig, az)
    i_urto, urto = avvolto.punto_riposo(pony, (-0.3, -0.25, 0.92), lato=(-1, 0, 0))
    gal = pose.traccia(rig, az['Gallop']); sgu = pose.traccia(rig, az['Sguardo_D'], 'COMBINE')
    avvolto.mostra(pony, rig, 1)
    eroe = lambda f: avanti(m, 0, 0, yaw, V * (f - 1))
    for f in range(1, n + 1):
        spinta = 0.04 * sm((f - FI + 1) / 1.0) * math.exp(-max(0.0, f - FI) / 2.5) if f >= FI - 1 else 0.0     # il colpo lo sposta
        radice.location = rel(eroe(f), yaw, (spinta, 0, 0)); radice.rotation_euler = (0, 0, math.radians(yaw))
        radice.keyframe_insert('location', frame=f); radice.keyframe_insert('rotation_euler', frame=f)
        chiave_striscia(gal, f, 4.0 + (f - 1))
        chiave_striscia(sgu, f, 9.0, curva([(1, 0.0), (FI + 3, 0.0), (FI + 10, 1.0), (n, 1.0)], f))
    # la testa si abbassa a guardarsi il fianco (sommata allo sguardo), con un cenno soddisfatto alla fine
    for nome, quota in (('neck', 0.45), ('head', 0.55)):
        pb = rig.pose.bones[nome]; pb.rotation_mode = 'QUATERNION'
        asse = rig.data.bones[nome].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0))
        for f in range(1, n + 1):
            a = math.radians(52) * quota * curva([(1, 0.0), (FI + 4, 0.0), (FI + 11, 1.0), (FI + 14, 0.8), (FI + 16, 1.0), (n, 1.0)], f)
            pb.rotation_quaternion = Quaternion(asse, a); pb.keyframe_insert('rotation_quaternion', frame=f)
    rig.animation_data.action_blend_type = 'COMBINE'
    sc = bpy.context.scene; sc.frame_set(FI); bpy.context.view_layer.update()
    W_urto = avvolto.mondo_vertice(pony, i_urto)
    fronte = avvolto.bolle(pony, urto)
    for f in range(1, n + 1):                                # il fronte delle bolle che scoppiano parte dall'urto e si allarga
        u = min(1.0, max(0.0, (f - FI) / 12.0)); fronte(f, 0.0 if f <= FI else 0.03 + 0.22 * (1 - (1 - u) ** 2))
    # la mazza: arriva dall'alto e da dietro (un predone fuori quadro), colpisce al 6, rimbalza e se ne va
    k = 1.2; mazza = AN.oggetto('models/armi/mace.glb', (0, 0, 0), scala=k, nome='mazza')
    pugno = Vector((0, 0, -0.10)); L = (0.33 + 0.10) * k
    Ryw = Matrix.Rotation(math.radians(yaw), 3, 'Z')
    d_urto = (Ryw @ Vector((0.55, -0.30, -0.50))).normalized()
    d_su = (Ryw @ Vector((-0.15, 0.55, 0.85))).normalized(); d_via = (Ryw @ Vector((-0.35, 0.45, 0.6))).normalized()
    fuori = (Ryw @ Vector((-1, 0, 0)))
    H0 = W_urto + fuori * 0.09 - d_urto * L - eroe(FI)
    q_su, q_urto, q_via = (d.to_track_quat('Z', 'Y') for d in (d_su, d_urto, d_via))
    for f in range(1, n + 1):
        if f <= FI: q = q_su.slerp(q_urto, ((f - 1) / (FI - 1)) ** 2)
        else: q = q_urto.slerp(q_via, sm((f - FI) / 5.0))
        H = eroe(f) + H0 + (Ryw @ Vector((-0.3, 0.7, 0.45))) * sm((f - FI - 1) / 7.0)
        chiave_matrice(mazza, f, Matrix.Translation(H) @ q.to_matrix().to_4x4() @ Matrix.Translation(-pugno * k) @ Matrix.Scale(k, 4))
    # camera al fianco destro, un po' davanti: il fianco colpito e la testa che si gira a guardarlo
    for_cam = lambda f: (rel(eroe(f), yaw, (-1.75, -1.35, 1.3)) + scossa(f, FI, 0.015, 0.6, 2.8), rel(eroe(f), yaw, (-0.2, -0.3, 1.1)))
    p1, m1 = for_cam(1); cam = AN.camera(p1, m1, 35, fstop=2.8, fuoco=m1)
    for f in range(1, n + 1):
        p, mi = for_cam(f); SH.chiave_camera(cam, f, p, mi, fuoco=(mi - p).length)

# ---------------------------------------------------------------------------------------------------------------- montaggio
def ff(*a): subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *a], check=True)

def monta():
    W, H = (1080, 1920) if MODO == 'finale' else (540, 960)
    v = lambda s: os.path.join(BASE, s, '%s-%s.mp4' % (s, MODO))
    clip = [v(s) for s in TUTTI]
    s14 = os.path.join(BASE, 'S14', 'S14-%s.mp4' % MODO)
    if os.path.exists(s14): clip.append(s14)
    else: print('MANCA', s14, '(atto2.mp4 senza S14)')
    ing = sum((['-i', c] for c in clip), [])
    filt = ''.join('[%d:v]setpts=PTS-STARTPTS,scale=%d:%d,fps=24[v%d];' % (i, W, H, i) for i in range(len(clip)))
    filt += ''.join('[v%d]' % i for i in range(len(clip))) + 'concat=n=%d:v=1:a=0[o]' % len(clip)
    ff(*ing, '-filter_complex', filt, '-map', '[o]', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', '24',
       '-movflags', '+faststart', os.path.join(BASE, 'atto2.mp4'))
    print('MONTATO', os.path.join(BASE, 'atto2.mp4'))

if __name__ == '__main__':
    if LISTA == ['monta']: monta()
    else:
        for nome in LISTA:
            S[nome]()
            if MODO == 'finale': SH.salva(nome)
            SH.gira(os.path.join(BASE, nome), nome, MODO)
        if set(LISTA) == set(TUTTI): monta()
