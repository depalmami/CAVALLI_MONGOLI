# IL PREDONE DI CARTONE (24 nov): un nemico a due gambe, preso da assets/models/predone-cartone-tavola.glb («cardboard armor 3d model»).
# Il file è una TAVOLA A QUATTRO VISTE (davanti, di lato, dietro, di lato) uscita da un generatore di modelli: quattro uomini con
# la testa di cavallo di cartone e la tunica a strisce, in posa a T, nello stesso mesh, senza scheletro e con una sola texture 4096².
# Qui se ne prende UNO (il frontale), lo si rimette ritto e girato con la faccia verso -Y come tutti i personaggi del trailer, e gli si
# costruisce uno scheletro a 17 ossa con i pesi ricavati dalla distanza di ogni vertice dall'osso (il mesh è un pezzo solo: strisce
# e corpo fusi, quindi niente pesi «rigidi» per isola).
#
#   radice, arm, az = predone_cartone('azzurro', altezza=2.0, nome='rivale')
#       radice   Empty da chiavare (posizione e giro; l'origine è fra i piedi, la faccia guarda -Y come yaw 0)
#       arm      lo scheletro; az = {'Gallop', 'Idle', 'Attack_Headbutt'}: le clip, con gli STESSI nomi del cavallo di Quaternius
#                (così pose.traccia() e le chiavi sulle strisce di shot-atto2.py funzionano uguali)
#   Gallop è un CICLO di CICLO_N=24 fotogrammi di clip (frame 1..25, il 25 = l'1). Il passo è fatto con una cinematica inversa piana
#   dei piedi: durante l'appoggio il piede va indietro a velocità COSTANTE rispetto al bacino, quindi non pattina se la striscia
#   corre alla velocità giusta: vedi velocita_ciclo() e tempo_corsa().
#
#   python3 -I … blender -b --python tools/trailer3d/cartone.py -- <cartella>     scheda di prova: T-pose, corsa, testata, rigido
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Euler

QUI = os.path.dirname(os.path.abspath(__file__))
if QUI not in sys.path: sys.path.insert(0, QUI)
GLB = os.path.abspath(os.path.join(QUI, '..', '..', 'assets', 'models', 'predone-cartone-tavola.glb'))
H0 = 0.453                                           # altezza nativa della figura (m del file)
Y0 = 0.032                                           # asse del corpo (dietro il centro dei piedi: la caviglia sta sopra il tallone)
CICLO_N = 24                                         # fotogrammi di clip di un ciclo di corsa
DS = 0.26                                            # frazione del ciclo in appoggio (corsa: tanto volo)
PASSO = 0.17                                         # lunghezza dell'appoggio (unità native): il piede percorre questo, a terra
L1, L2 = 0.095, 0.080                                # coscia e stinco (unità native)
Z_ANCA, Z_GINOCCHIO, Z_CAV = 0.200, 0.105, 0.025

# ---------------------------------------------------------------------------------------------------------- scheletro
# (nome, testa, coda, padre) in unità native, la figura già rimessa a faccia -Y e coi piedi al centro. L = +X.
def _ossa():
    o = [('bacino', (0, Y0, 0.200), (0, Y0, 0.235), None),
         ('schiena', (0, Y0, 0.235), (0, Y0, 0.290), 'bacino'),
         ('petto', (0, Y0, 0.290), (0, Y0, 0.330), 'schiena'),
         ('collo', (0, Y0, 0.330), (0, Y0 + 0.004, 0.350), 'petto'),
         ('testa', (0, Y0 + 0.004, 0.350), (0, -0.090, 0.390), 'collo')]
    for s, x in (('L', 1), ('R', -1)):
        o += [('coscia.' + s, (0.030 * x, Y0, Z_ANCA), (0.030 * x, Y0, Z_GINOCCHIO), 'bacino'),
              ('stinco.' + s, (0.030 * x, Y0, Z_GINOCCHIO), (0.030 * x, Y0, Z_CAV), 'coscia.' + s),
              ('piede.' + s, (0.030 * x, Y0, Z_CAV), (0.030 * x, -0.022, 0.008), 'stinco.' + s),
              ('braccio.' + s, (0.065 * x, 0.007, 0.306), (0.135 * x, 0.007, 0.306), 'petto'),
              ('avambraccio.' + s, (0.135 * x, 0.007, 0.306), (0.185 * x, 0.007, 0.306), 'braccio.' + s),
              ('mano.' + s, (0.185 * x, 0.007, 0.306), (0.222 * x, 0.007, 0.306), 'avambraccio.' + s)]
    return o
SIGMA = dict(bacino=0.060, schiena=0.060, petto=0.050, collo=0.040, testa=0.075, coscia=0.030, stinco=0.025, piede=0.030,
             braccio=0.032, avambraccio=0.028, mano=0.030)


def _punti_figura(P):
    """Vertici della figura frontale (riga bassa, T-pose a sinistra) della tavola: gli altri tre stanno ≥ 0,2 m più in là."""
    return (P[:, 0] < 0.1) & (P[:, 2] < 0.465)


def costruisci(nome='predone', altezza=2.0, tinta=None):
    """Ritorna (radice, arm, mesh). Il mesh è nelle coordinate della radice (m): origine fra i piedi, faccia verso -Y, alto `altezza`."""
    sc = bpy.context.scene; prima = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=GLB)
    nuovi = [o for o in bpy.data.objects if o not in prima]
    mesh = next(o for o in nuovi if o.type == 'MESH')
    me = mesh.data
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    P = np.array([v.co[:] for v in bm.verts])
    tieni = _punti_figura(P)
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.where(~tieni)[0]], context='VERTS')
    bm.verts.ensure_lookup_table()
    P = np.array([v.co[:] for v in bm.verts])
    piedi = P[P[:, 2] < 0.03]; cx, cy = piedi[:, 0].mean(), piedi[:, 1].mean()
    k = altezza / H0
    for v in bm.verts:                                 # al centro dei piedi, girato di 180° (la tavola guarda +Y), in scala
        x, y, z = v.co.x - cx, v.co.y - cy, v.co.z
        v.co = Vector((-x * k, -y * k, z * k))
    bm.to_mesh(me); bm.free(); me.update()
    # fuori il genitore del glTF (RootNode) e tutto il resto: il mesh va sciolto, la radice è nostra
    mesh.parent = None; mesh.matrix_world = Matrix.Identity(4); mesh.name = nome + '_mesh'
    for o in nuovi:
        if o is not mesh: bpy.data.objects.remove(o)
    radice = bpy.data.objects.new(nome, None); sc.collection.objects.link(radice)
    # scheletro
    arm_d = bpy.data.armatures.new(nome + '_rig'); arm = bpy.data.objects.new(nome + '_rig', arm_d); sc.collection.objects.link(arm)
    ossa = _ossa()
    vl = bpy.context.view_layer; vl.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    for n, h, t, p in ossa:
        eb = arm_d.edit_bones.new(n); eb.head = Vector(h) * k; eb.tail = Vector(t) * k
        if p: eb.parent = arm_d.edit_bones[p]
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.parent = radice; mesh.parent = radice
    # pesi: gaussiana della distanza dal segmento d'osso, i 3 più forti, normalizzati. Uguale per i vertici nella stessa posizione
    # (il glTF li sdoppia sulle cuciture: stessa posizione = stessi pesi, nessuna crepa).
    V = np.array([v.co[:] for v in me.vertices]) / k
    seg = [(n, np.array(h), np.array(t)) for n, h, t, p in ossa]
    D = np.zeros((len(V), len(seg)))
    for j, (n, a, b) in enumerate(seg):
        ab = b - a; u = np.clip(((V - a) @ ab) / (ab @ ab), 0.0, 1.0)
        d = np.linalg.norm(V - (a + u[:, None] * ab), axis=1)
        s = SIGMA[n.split('.')[0]]
        D[:, j] = np.exp(-(d / s) ** 2)
    chiavi = {}
    for i, p in enumerate(V): chiavi.setdefault(tuple(np.round(p * 1e4).astype(int)), []).append(i)
    gruppi = {n: mesh.vertex_groups.new(name=n) for n, *_ in ossa}
    for ids in chiavi.values():
        w = D[ids[0]].copy(); top = np.argsort(-w)[:3]
        if w[top[0]] < 1e-4: top = np.array([int(np.argmax(w))]); w = np.zeros_like(w); w[top[0]] = 1.0
        w = w[top]; w = w / w.sum()
        for j, wj in zip(top, w):
            if wj > 0.01:
                for i in ids: gruppi[seg[j][0]].add([i], float(wj), 'REPLACE')
    md = mesh.modifiers.new('Armature', 'ARMATURE'); md.object = arm
    sc.collection.objects.link(mesh) if mesh.name not in sc.collection.objects else None
    # materiale: la texture, con una tinta moltiplicata (le tinte dei predoni del gioco, smorzate)
    mt = mesh.data.materials[0]; nt = mt.node_tree
    bsdf = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'); tex = next(x for x in nt.nodes if x.type == 'TEX_IMAGE')
    if tinta is not None:
        # la tinta solo sul CARTONE: la pelle (mani, gambe, piedi) ha R molto più alto e R-G più grande (misurato sulla texture:
        # pelle R 0,64–0,67 e R-G 0,10–0,15; cartone R 0,43–0,46 e R-G 0,04–0,09) e resta com'è
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex.outputs['Color'], sep.inputs['Color'])
        def mat(op, a_, b_=None, clamp=False):
            n_ = nt.nodes.new('ShaderNodeMath'); n_.operation = op; n_.use_clamp = clamp
            for i_, v_ in enumerate((a_, b_)):
                if v_ is None: continue
                if hasattr(v_, 'node'): nt.links.new(v_, n_.inputs[i_])
                else: n_.inputs[i_].default_value = v_
            return n_.outputs[0]
        def liscia(x, da, a2):
            n_ = nt.nodes.new('ShaderNodeMapRange'); n_.interpolation_type = 'SMOOTHSTEP'; n_.clamp = True
            nt.links.new(x, n_.inputs['Value']); n_.inputs['From Min'].default_value = da; n_.inputs['From Max'].default_value = a2
            return n_.outputs['Result']
        rg = mat('SUBTRACT', sep.outputs['Red'], sep.outputs['Green'])
        pelle = mat('MULTIPLY', liscia(rg, 0.080, 0.115), liscia(sep.outputs['Red'], 0.52, 0.60))
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
        ing = lambda idf: next(i for i in mx.inputs if i.identifier == idf)
        nt.links.new(mat('SUBTRACT', 1.0, pelle), next(i for i in mx.inputs if i.identifier == 'Factor_Float'))
        ing('B_Color').default_value = tuple(tinta) + (1,)
        nt.links.new(tex.outputs['Color'], ing('A_Color')); nt.links.new(next(o for o in mx.outputs if o.identifier == 'Result_Color'), bsdf.inputs['Base Color'])
    if 'Roughness' in bsdf.inputs: bsdf.inputs['Roughness'].default_value = 0.85
    return radice, arm, mesh


# ---------------------------------------------------------------------------------------------------------- pose
def _R(x=0.0, y=0.0, z=0.0):
    """Rotazione (gradi) attorno agli assi dello scheletro: si applica prima la Z, poi la Y, poi la X (matrice Rx·Ry·Rz)."""
    return Euler((math.radians(x), math.radians(y), math.radians(z)), 'ZYX').to_matrix()

def applica(arm, delta, bacino_loc=(0, 0, 0)):
    """delta = {osso: matrice 3×3 di rotazione nel riferimento dello scheletro, relativa al padre}. Ogni osso ruota attorno alla propria
    testa, e il padre (già ruotato) si compone a sinistra: è una FK normale scritta negli assi del mondo del riposo."""
    for pb in arm.pose.bones:
        R = pb.bone.matrix_local.to_3x3(); D = delta.get(pb.name)
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (R.inverted() @ D @ R).to_quaternion() if D is not None else (1, 0, 0, 0)
        if pb.name == 'bacino': pb.location = R.inverted() @ Vector(bacino_loc)
    bpy.context.view_layer.update()

def chiave_posa(arm, f):
    for pb in arm.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=f)
        if pb.name == 'bacino': pb.keyframe_insert('location', frame=f)


def _gamba(arm, lato, bacino, ankle_y, ankle_z, pitch):
    """IK piana (piano YZ) di una gamba: ritorna le rotazioni di coscia, stinco e piede. bacino = (y, z) dell'anca, ankle = (y, z)
    del bersaglio, in coordinate dello scheletro (unità del file × k: qui già in m)."""
    k = arm['k']
    l1, l2 = L1 * k, L2 * k
    dy, dz = ankle_y - bacino[0], ankle_z - bacino[1]
    D = math.hypot(dy, dz); D = max(abs(l1 - l2) + 1e-4, min(l1 + l2 - 1e-4, D))
    uy, uz = dy / math.hypot(dy, dz), dz / math.hypot(dy, dz)
    al = math.acos(max(-1, min(1, (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D))))
    ny, nz = uz, -uy                                   # perpendicolare dal lato -Y (il ginocchio va avanti)
    ky = l1 * (math.cos(al) * uy + math.sin(al) * ny); kz = l1 * (math.cos(al) * uz + math.sin(al) * nz)
    ay, az_ = bacino[0] + uy * D, bacino[1] + uz * D
    f1 = math.atan2(ky, -kz); f2 = math.atan2(ay - (bacino[0] + ky), -(az_ - (bacino[1] + kz)))
    f3 = math.radians(pitch)
    return _R(math.degrees(f1)), _R(math.degrees(f2 - f1)), _R(math.degrees(f3 - f2))


def posa_corsa(arm, ph, v_ciclo=None):
    """La corsa a fase ph ∈ [0,1): appoggio a piede in avanti → indietro (piede fermo a terra), poi volo con il ginocchio alto."""
    k = arm['k']; delta = {}
    hh = 0.172 * k; bob = 0.014 * k; S = PASSO * k; y0 = Y0 * k; az0 = Z_CAV * k; lift = 0.075 * k
    ph2 = ph % 0.5; in_app = ph2 < DS
    quota = hh - (bob * math.sin(math.pi * ph2 / DS) if in_app else 0.0)
    bac = (y0, quota)
    for lato, off in (('L', 0.0), ('R', 0.5)):
        p = (ph + off) % 1.0
        if p < DS:                                      # appoggio: davanti → dietro, a terra
            f = S / 2 - S * (p / DS); z = az0; pitch = -8 + 22 * (p / DS) ** 2
        else:                                           # volo: dietro → davanti, in alto
            u = (p - DS) / (1 - DS); su = u * u * (3 - 2 * u)
            f = -S / 2 + S * su; z = az0 + lift * math.sin(math.pi * u) ** 1.15; pitch = 26 - 40 * math.sin(math.pi * min(1.0, u * 1.15)) * (1 - u)
        c, s_, p_ = _gamba(arm, lato, bac, y0 - f, z, pitch)
        delta['coscia.' + lato] = c; delta['stinco.' + lato] = s_; delta['piede.' + lato] = p_
    # tronco: inclinato in avanti, con una torsione contraria al passo; le braccia pompano
    c1 = math.cos(2 * math.pi * ph); s1 = math.sin(2 * math.pi * ph)
    delta['schiena'] = _R(9, 0, 7 * c1); delta['petto'] = _R(7, 0, 6 * c1); delta['collo'] = _R(-4, 0, -5 * c1)
    delta['testa'] = _R(-6 + 3 * math.cos(4 * math.pi * ph), 0, -4 * c1)
    for lato, x, ph_b in (('L', 1, ph + 0.5), ('R', -1, ph)):
        sw = math.cos(2 * math.pi * ph_b)                # +1 = braccio in avanti
        delta['braccio.' + lato] = _R(-38 * sw, 72 * x, 0)  # giù di 72° (Y), poi avanti/indietro (X)
        delta['avambraccio.' + lato] = _R(0, 0, -(70 + 25 * sw) * x)
        delta['mano.' + lato] = _R(0, 0, 0)
    return delta, (0.0, 0.0, 0.0)


def posa_riposo(arm):
    """Il «giocattolo» rigido: dritto, braccia lungo i fianchi, gambe unite e tese."""
    d = {}
    for lato, x in (('L', 1), ('R', -1)):
        d['braccio.' + lato] = _R(0, 78 * x, 0)
    return d, (0.0, 0.0, 0.0)


def _liscia(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
def _mix(a, b, t): return a + (b - a) * t


def posa_testata(arm, t, inch=1.0):
    """24 fotogrammi di clip: 1–5 accucciato dalla corsa · 5–9 carica indietro · 9–11,5 AFFONDO (la testa va alla lama) · 12–24 resta lì.
    Il colpo è al fotogramma 11,5 della clip (come nell'Attack_Headbutt del cavallo). inch = quanto si china nell'affondo
    (0 = a testa alta, 1 = a testa bassa, quasi orizzontale): si sceglie in modo che il muso arrivi a una quota data (vedi crea_azioni)."""
    k = arm['k']
    ca = _liscia((t - 1) / 4.0)                          # accucciarsi
    carica = _liscia((t - 5) / 4.0)                      # indietro
    colpo = _liscia((t - 9) / 2.5)                       # affondo
    d = {}
    # gambe: la sinistra avanti, piegata; la destra dietro, tesa
    bac_z = 0.172 * k - (0.030 * k) * ca - (0.020 * k) * colpo * inch
    bac_y = Y0 * k - (0.030 * k) * colpo + 0.012 * k * carica
    for lato, avanti_ in (('L', 1), ('R', 0)):
        fw = _mix(0.04, 0.095, colpo) * k if avanti_ else _mix(-0.04, -0.105, colpo) * k
        zz = Z_CAV * k + (0.0 if avanti_ else 0.012 * k * colpo)
        c, s_, p_ = _gamba(arm, lato, (bac_y, bac_z), Y0 * k - fw - (bac_y - Y0 * k) * 0, zz, 4 if avanti_ else 40 * colpo)
        d['coscia.' + lato] = c; d['stinco.' + lato] = s_; d['piede.' + lato] = p_
    pit = _mix(_mix(12, -10, carica), 28 * inch, colpo)           # inclinazione della schiena (+ = avanti)
    d['schiena'] = _R(pit, 0, 0); d['petto'] = _R(_mix(_mix(6, -8, carica), 24 * inch, colpo), 0, 0)
    d['collo'] = _R(_mix(_mix(-6, -14, carica), 16 * inch, colpo), 0, 0); d['testa'] = _R(_mix(_mix(-8, -18, carica), 22 * inch, colpo), 0, 0)
    for lato, x in (('L', 1), ('R', -1)):
        d['braccio.' + lato] = _R(_mix(-10, 28, carica), 70 * x, 0)       # indietro per slancio, vicino al corpo
        d['avambraccio.' + lato] = _R(0, 0, -_mix(55, 25, colpo) * x)
    return d, (0.0, bac_y - Y0 * k, bac_z - 0.200 * k)


def _bacino_rel(arm, y, z):
    return (0.0, y, z)


def _muso(arm, d, loc):
    applica(arm, d, loc); return Vector(arm.pose.bones['testa'].tail)


def scegli_inch(arm, z_colpo):
    """Bisezione: la profondità dell'affondo per cui il muso (la coda dell'osso della testa) sta a z_colpo m dal suolo al fotogramma 11,5."""
    lo, hi = 0.0, 1.5
    z = lambda c: _muso(arm, *posa_testata(arm, 11.5, c)).z
    if z_colpo >= z(lo): return lo
    if z_colpo <= z(hi): return hi
    for _ in range(24):
        mid = (lo + hi) / 2
        if z(mid) > z_colpo: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def crea_azioni(arm, z_colpo=None):
    """Le tre clip, cotte a chiavi. Ritorna {'Gallop', 'Idle', 'Attack_Headbutt'}."""
    k = arm['k']; arm.animation_data_create(); az = {}
    def clip(nome, n, fun):
        a = bpy.data.actions.new(nome); arm.animation_data.action = a
        for f in range(1, n + 1):
            d, loc = fun(f)
            applica(arm, d, loc); chiave_posa(arm, f)
        arm.animation_data.action = None; az[nome] = a
    hh = 0.172 * k
    def corsa(f):
        d, _ = posa_corsa(arm, ((f - 1) % CICLO_N) / CICLO_N)
        ph = ((f - 1) % CICLO_N) / CICLO_N; ph2 = ph % 0.5
        quota = hh - ((0.014 * k) * math.sin(math.pi * ph2 / DS) if ph2 < DS else 0.0)
        return d, (0.0, 0.0, quota - 0.200 * k)                 # il bacino riposa a 0,200: si sposta della differenza
    clip('Gallop', CICLO_N + 1, corsa)
    clip('Idle', 2, lambda f: posa_riposo(arm))
    inch = 1.0 if z_colpo is None else scegli_inch(arm, z_colpo)
    m = _muso(arm, *posa_testata(arm, 11.5, inch)); arm['inch'] = inch; arm['testa_d'] = -m.y; arm['muso_z'] = m.z
    clip('Attack_Headbutt', 24, lambda f: posa_testata(arm, float(f), inch))
    return az


def velocita_ciclo(arm):
    """Metri a fotogramma-di-clip a cui il piede d'appoggio va indietro (la striscia al passo 1 per fotogramma). Un predone che corre
    a v m/fotogramma di scena vuole la striscia a v / velocita_ciclo() fotogrammi di clip per fotogramma di scena."""
    return PASSO * arm['k'] / (DS * CICLO_N)


def tempo_corsa(arm, v, f, t0=1.0):
    """Tempo della clip Gallop (1..25) al fotogramma di scena f (f=1 → t0) per un corpo che va a v m/fotogramma, senza pattinare."""
    t = t0 - 1.0 + (f - 1) * v / velocita_ciclo(arm)
    return 1.0 + (t % CICLO_N)


def predone_cartone(colore='azzurro', altezza=2.0, nome='predone', tinte=None, z_colpo=None):
    """Come predone_vivo() di shot-atto2.py: ritorna (radice, scheletro, azioni), con le clip pronte per pose.traccia().
    z_colpo = quota (m) a cui il muso deve arrivare nella testata; poi arm['testa_d'] è la distanza orizzontale radice → muso al colpo."""
    import pose
    tinta = None
    if colore is not None:
        h = (tinte or dict(arancio='#ffc9a3', azzurro='#a9c8ff', verde='#d6ffb3', rosa='#ffb3d1'))[colore]
        tinta = pose.tinta_smorzata(h, 0.35)
        m = max(tinta); tinta = tuple((c / m) ** 1.2 for c in tinta)          # solo la tinta, non il buio: il cartone resta chiaro
    radice, arm, mesh = costruisci(nome, altezza, tinta)
    arm['k'] = altezza / H0
    az = crea_azioni(arm, z_colpo)
    ad = arm.animation_data
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    ad.action = None
    return radice, arm, az


# ---------------------------------------------------------------------------------------------------------- scheda di prova
if __name__ == '__main__':
    A = sys.argv[sys.argv.index('--') + 1:]; OUT = os.path.abspath(A[0]); os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 480; sc.render.resolution_y = 640
    w = bpy.data.worlds.new('w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.62, 0.66, 0.72, 1); sc.world = w
    for rot in ((55, 0, 30), (55, 0, 200)):
        s = bpy.data.objects.new('s', bpy.data.lights.new('s', 'SUN')); s.data.energy = 2.6; s.rotation_euler = tuple(math.radians(x) for x in rot); sc.collection.objects.link(s)
    cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 45
    radice, arm, az = predone_cartone('azzurro', 2.0, 'prova')
    print('k', arm['k'], 'velocità ciclo m/clip-fotogramma', velocita_ciclo(arm))
    import pose
    def scatta(nome, d, loc, az_cam=-90, dist=6.0, h=1.0):
        applica(arm, d, loc)
        a = math.radians(az_cam); cam.location = (dist * math.cos(a), dist * math.sin(a), h + 0.2); cam.rotation_euler = (Vector((0, 0, h)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, nome + '.png'); bpy.ops.render.render(write_still=True)
    scatta('t0-davanti', {}, (0, 0, 0)); scatta('t0-lato', {}, (0, 0, 0), 0)
    for i in range(0, 24, 3):
        d, loc = posa_corsa(arm, i / 24.0); ph = i / 24.0; ph2 = ph % 0.5; k = arm['k']
        q = 0.172 * k - ((0.014 * k) * math.sin(math.pi * ph2 / DS) if ph2 < DS else 0.0)
        scatta('corsa-%02d' % i, d, (0, 0, q - 0.2 * k), 0)
    for t in (1, 5, 9, 11, 12):
        d, loc = posa_testata(arm, float(t)); scatta('testata-%02d' % t, d, loc, 0)
    d, loc = posa_riposo(arm); scatta('rigido', d, loc, -90); scatta('rigido-lato', d, loc, 0)
