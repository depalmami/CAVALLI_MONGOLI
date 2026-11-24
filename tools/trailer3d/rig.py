# RIG DEL PROTAGONISTA PER IL TRAILER. Parte dal .blend del gioco (che NON modifica) e ne salva una copia con:
#   - il BRACCIO destro, che nel gioco non ha ossa (la manica pesa sulla colonna): braccio.R (dalla spalla, dentro la scatola,
#     al gomito, che sta sulla fessura del cartone), avambraccio.R (gomito → polsino), mano.R (polsino → nocche) e presa.R
#     (dove si impugna l'arma, non deforma: la sua Y è la lunghezza dell'arma). I pesi della manica e della mano si
#     ricalcolano qui: capsule attorno alle ossa, ma solo sui vertici BLU (manica) o COLOR PELLE (mano), così il cartone
#     vicino al gomito e le redini nel pugno restano dove sono.
#   - le CLIP che il gioco non ha, tutte a 24 fps:
#       solo braccio (da sovrapporre a Gallop/Walk/Idle):  Sciabola_Fendente, Sciabola_Alta, Frusta, Afferra
#       collo e testa, relative (blend COMBINE sopra un'altra clip):  Sguardo_D, Sguardo_S
#       corpo e gambe:  Salto
#
# uso:  blender -b assets/models/protagonista-cartone.blend --python tools/trailer3d/rig.py -- <uscita.blend> [foglio.jpg]
#   (con il secondo argomento fa anche un foglio delle pose in Workbench)
#
# Spazio del modello: 1 unità = 1 m, il cavallo guarda -Y, Z su, il lato destro (quello del braccio) è -X.
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
rig = bpy.data.objects['CavalloCartone_rig']
horse = bpy.data.objects['CavalloCartone']
sc = bpy.context.scene

# ---------------------------------------------------------------------------------------------------------------- il braccio
# Punti misurati sul modello (viste ortogonali con i segni): il gomito è dove la manica esce dalla fessura della scatola,
# la spalla è nascosta dentro. Avambraccio 0,25 m, mano 0,10 m fino al centro del pugno.
SPALLA = Vector((-0.17, -0.22, 1.17))
GOMITO = Vector((-0.295, -0.35, 1.03))
POLSO = Vector((-0.236, -0.555, 1.16))
PUGNO = Vector((-0.16, -0.57, 1.225))
NOCCHE = POLSO + (PUGNO - POLSO) * 1.5
REDINE = Vector((0.12, -0.05, 1.0)).normalized()      # la redine nel pugno: è l'asse dell'impugnatura a riposo

OSSA = ('braccio.R', 'avambraccio.R', 'mano.R')

def colori_vertici():
    """Colore medio della texture sotto ogni vertice (dalle UV)."""
    me = horse.data
    img = next(n.image for n in me.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE'
               and any(l.to_socket.name == 'Base Color' for o in n.outputs for l in o.links))
    W, H = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)
    uv = me.uv_layers.active.data
    col = np.zeros((len(me.vertices), 3)); cnt = np.zeros(len(me.vertices))
    for l in me.loops:
        u, v = uv[l.index].uv
        col[l.vertex_index] += px[min(H - 1, max(0, int(v % 1.0 * H))), min(W - 1, max(0, int(u % 1.0 * W))), :3]
        cnt[l.vertex_index] += 1
    return col / np.maximum(cnt, 1)[:, None]

def dist_segmento(P, a, b):
    a = np.array(a); b = np.array(b); ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1), t

def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def costruisci_braccio():
    assert horse.matrix_world == Matrix.Identity(4) and rig.matrix_world == Matrix.Identity(4)
    rig.animation_data.action = None
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = rig.data.edit_bones
    def osso(nome, testa, coda, padre, deform=True, z=None):
        b = eb.new(nome); b.head = testa; b.tail = coda; b.parent = eb[padre]; b.use_connect = False; b.use_deform = deform
        if z is not None: b.align_roll(z)
        return b
    osso('braccio.R', SPALLA, GOMITO, 'DEF-spine.003', z=Vector((0, -1, 0)))
    osso('avambraccio.R', GOMITO, POLSO, 'braccio.R', z=Vector((-1, 0, 0)))
    osso('mano.R', POLSO, NOCCHE, 'avambraccio.R', z=Vector((-1, 0, 0)))
    # presa: nel pugno, lungo la redine; la sua Z guarda in avanti (-Y) = il filo della sciabola
    osso('presa.R', PUGNO, PUGNO + REDINE * 0.2, 'mano.R', deform=False, z=Vector((0, -1, 0)))
    bpy.ops.object.mode_set(mode='OBJECT')

    # --- pesi
    me = horse.data
    P = np.array([v.co for v in me.vertices])
    col = colori_vertici(); r, g, b = col[:, 0], col[:, 1], col[:, 2]
    blu = (b > r + 0.05) & (b > g) & (b < 0.5)
    # pelle in HSV (misurata sul pugno): tinta 0,045–0,065, saturazione 0,37–0,47. Il cartone e la redine hanno tinta ~0,08 e
    # saturazione 0,5–0,78, le frange della criniera tinta ~0,09: con RGB grezzo si confondevano
    mx = col.max(1); mn = col.min(1); sat = (mx - mn) / np.maximum(mx, 1e-3)
    tinta = np.where(mx == r, ((g - b) / np.maximum(mx - mn, 1e-4)) / 6.0, 0.5) % 1.0
    pelle = (mx == r) & (tinta > 0.030) & (tinta < 0.070) & (sat > 0.28) & (sat < 0.52) & (mx > 0.45) & ~blu
    k, u, dentro, W4, uW = lungo_braccio(P)
    regione = dentro & (((k < 2) & blu) | ((k == 2) & (pelle | blu)) | ((k == 1) & pelle & (u > uW - 0.04)))

    # La mesh di Meshy è UNA superficie: il pugno è saldato alla redine e alle frange della criniera, e i triangoli in mezzo si
    # allungavano in strisce marroni quando la mano si muove. Si taglia: le facce a maggioranza «braccio» si staccano dalle
    # altre, ma solo nella zona della mano (il gomito resta saldato alla scatola, lì i pesi sfumano).
    import bmesh
    n0 = len(P)
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    lf = bm.faces.layers.int.new('braccio')
    for f in bm.faces:
        vs = [v.index for v in f.verts]; f[lf] = int(2 * sum(bool(regione[i]) for i in vs) > len(vs))
    mano = u > uW - 0.05
    taglio = [e for e in bm.edges if len(e.link_faces) == 2 and e.link_faces[0][lf] != e.link_faces[1][lf]
              and mano[e.verts[0].index] and mano[e.verts[1].index]]
    bmesh.ops.split_edges(bm, edges=taglio)
    bm.verts.ensure_lookup_table()
    P1 = np.array([v.co for v in bm.verts])
    k1, u1, _, W1, _ = lungo_braccio(P1)
    dl = bm.verts.layers.deform.verify()
    gruppi = {n: (horse.vertex_groups.get(n) or horse.vertex_groups.new(name=n)).index for n in OSSA}
    arto = set(gruppi.values())
    n_br = 0
    for v in bm.verts:
        i = v.index
        lato = bool(v.link_faces) and all(f[lf] for f in v.link_faces)
        if not (lato or (i < n0 and regione[i] and not mano[i])): continue
        d = v[dl]; ws, wb, wa, wm = (float(x[i]) for x in W1)
        for gi in list(d.keys()):
            if gi not in arto: d[gi] = d[gi] * ws
        for n, w in zip(OSSA, (wb, wa, wm)):
            if w > 1e-3: d[gruppi[n]] = w
        n_br += 1
    bm.faces.layers.int.remove(lf)
    bm.to_mesh(me); bm.free(); me.update()
    print('BRACCIO: tagliati', len(taglio), 'spigoli · vertici al braccio', n_br, '(prima', n0, 'ora', len(me.vertices), ')')

def lungo_braccio(P):
    """Per ogni punto: su quale tratto del braccio sta (0 spalla-gomito, 1 avambraccio, 2 mano), a che distanza lungo il
    braccio (u, m), se sta dentro le capsule, e i pesi (scatola, braccio, avambraccio, mano)."""
    a0 = GOMITO + (SPALLA - GOMITO).normalized() * 0.10          # dove la manica entra nella scatola
    fine = POLSO + (PUGNO - POLSO).normalized() * 0.14           # punta delle dita
    d1, t1 = dist_segmento(P, a0, GOMITO)
    d2, t2 = dist_segmento(P, GOMITO, POLSO)
    d3, t3 = dist_segmento(P, POLSO, fine)
    L1, L2, L3 = (GOMITO - a0).length, (POLSO - GOMITO).length, (fine - POLSO).length
    D = np.stack([d1 - 0.075, d2 - 0.07, d3 - 0.058], 1)
    k = D.argmin(1)
    u = np.choose(k, [t1 * L1, L1 + t2 * L2, L1 + L2 + t3 * L3])
    uE, uW = L1, L1 + L2
    w_scatola = 1 - sm(0.0, 0.07, u)
    w_br = sm(0.0, 0.07, u) * (1 - sm(uE - 0.03, uE + 0.04, u))
    w_av = sm(uE - 0.03, uE + 0.04, u) * (1 - sm(uW - 0.02, uW + 0.02, u))
    w_ma = sm(uW - 0.02, uW + 0.02, u)
    return k, u, D.min(1) < 0, (w_scatola, w_br, w_av, w_ma), uW

# ---------------------------------------------------------------------------------------------------------------- pose
pbs = rig.pose.bones
B = rig.data.bones
def upd(): bpy.context.view_layer.update()

def reset(nomi):
    for n in nomi:
        pb = pbs[n]; pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)

def dirige(nome, d, giro=0.0):
    """Gira l'osso (attorno alla sua testa) finché la sua Y punta verso d (spazio del modello); giro = torsione attorno a d."""
    upd()
    pb = pbs[nome]; b = B[nome]
    M0 = (pbs[b.parent.name].matrix @ (b.parent.matrix_local.inverted() @ b.matrix_local)) if b.parent else b.matrix_local
    y0 = M0.to_3x3() @ Vector((0, 1, 0))
    q = Quaternion(Vector(d).normalized(), giro) @ y0.rotation_difference(Vector(d).normalized())
    R = q.to_matrix() @ M0.to_3x3()
    pb.matrix = Matrix.Translation(M0.translation) @ R.to_4x4()
    upd()

# Pose del braccio: direzioni (spazio del modello, corpo a riposo) di braccio, avambraccio, mano e dell'arma (presa).
# None = lascia l'osso come segue il padre.
BR = {
    'redini':   dict(),
    # sciabola in alto, dritta: la lama prende la luna (S24, S27)
    'alta':     dict(br=(-0.70, -0.35, -0.05), av=(-0.28, -0.12, 0.95), ma=(-0.10, -0.05, 1.0), presa=(-0.12, 0.10, 1.0)),
    # fendente: carica dietro la spalla, colpo in fuori a destra, seguito davanti
    'carica':   dict(br=(-0.75, -0.10, 0.05), av=(-0.30, 0.45, 0.84), ma=(-0.15, 0.70, 0.70), presa=(-0.20, 0.80, 0.30)),
    'colpo':    dict(br=(-0.85, -0.40, 0.05), av=(-0.72, -0.58, 0.30), ma=(-0.68, -0.62, 0.25), presa=(-0.60, -0.78, 0.08)),
    'seguito':  dict(br=(-0.60, -0.60, -0.30), av=(-0.10, -0.95, -0.25), ma=(0.25, -0.90, -0.30), presa=(0.45, -0.85, -0.25)),
    # frusta: su e indietro, poi lo schiocco in avanti
    'frusta_su': dict(br=(-0.75, -0.05, 0.10), av=(-0.20, 0.30, 0.93), ma=(-0.10, 0.55, 0.83), presa=(-0.10, 0.70, 0.70)),
    'schiocco': dict(br=(-0.70, -0.65, 0.00), av=(-0.35, -0.85, 0.40), ma=(-0.30, -0.90, 0.30), presa=(-0.30, -0.92, 0.25)),
    # afferra al volo (S08): il braccio si allunga avanti e in alto
    'afferra':  dict(br=(-0.65, -0.70, 0.05), av=(-0.25, -0.70, 0.67), ma=(-0.15, -0.60, 0.78), presa=(-0.25, -0.15, 0.96)),
}

def posa_braccio(nome):
    reset(OSSA + ('presa.R',)); upd()
    p = BR[nome]
    for osso, chiave in (('braccio.R', 'br'), ('avambraccio.R', 'av'), ('mano.R', 'ma'), ('presa.R', 'presa')):
        if chiave in p: dirige(osso, p[chiave])

def chiavi_braccio(f):
    for n in OSSA + ('presa.R',):
        pbs[n].keyframe_insert('rotation_quaternion', frame=f)

CLIP_BRACCIO = {
    # nome: [(fotogramma, posa)]
    'Sciabola_Fendente': [(1, 'redini'), (7, 'carica'), (11, 'colpo'), (15, 'seguito'), (24, 'redini')],
    'Sciabola_Alta':     [(1, 'redini'), (12, 'alta'), (24, 'alta')],
    'Frusta':            [(1, 'redini'), (6, 'frusta_su'), (10, 'schiocco'), (14, 'schiocco'), (24, 'redini')],
    'Afferra':           [(1, 'redini'), (8, 'afferra'), (12, 'afferra'), (20, 'redini')],
}

def nuova_azione(nome):
    old = bpy.data.actions.get(nome)
    if old: bpy.data.actions.remove(old)
    rig.animation_data_create(); rig.animation_data.action = None

def chiudi_azione(nome, n):
    act = rig.animation_data.action
    act.name = nome; act.use_fake_user = True; act.frame_range = (1, n); act.use_frame_range = True
    rig.animation_data.action = None
    return act

# --- lo sguardo: collo e testa girano verso un lato (asse Z del modello), come rotazione RELATIVA da sommare a un'altra clip
def chiavi_sguardo(nome, segno):
    nuova_azione(nome)
    for f, ang in ((1, 0), (6, 1.0), (9, 1.08), (18, 1.0), (24, 0)):
        for n, quota in (('neck', 0.45), ('head', 0.55)):
            asse = B[n].matrix_local.to_3x3().inverted() @ Vector((0, 0, 1))
            q = Quaternion(asse, segno * math.radians(55) * quota * ang)
            pbs[n].rotation_quaternion = q; pbs[n].keyframe_insert('rotation_quaternion', frame=f)
    reset(('neck', 'head'))
    return chiudi_azione(nome, 24)

# --- il salto: corpo e gambe. Usa la stessa geometria delle gambe di tools/anima-protagonista.py
GAMBE = ('front.L', 'front.R', 'rear.L', 'rear.R')
PIVOT = Vector((0.0, 0.01, 0.96))
FOOT_FLAT = math.radians(35); TOE_FLAT = math.radians(10)
def Rx(a): return Matrix.Rotation(a, 4, 'X')
def Ry(a): return Matrix.Rotation(a, 4, 'Y')
def Rz(a): return Matrix.Rotation(a, 4, 'Z')
def attorno(p, R): return Matrix.Translation(p) @ R @ Matrix.Translation(-p)
def ang_yz(v): return math.atan2(v.z, v.y)
def avvolgi(a): return (a + math.pi) % (2 * math.pi) - math.pi
LG = {}
for kk in GAMBE:
    p_, s_ = kk.split('.')
    th, sh, ft, to = (B[f'ORG-{n}_{p_}.{s_}'] for n in ('thigh', 'shin', 'foot', 'toe'))
    LG[kk] = dict(reach=(th.length + sh.length) * 0.985, f_rest=ft.tail_local - ft.head_local, flen=ft.length,
                  t_rest=to.tail_local - to.head_local, tlen=to.length,
                  foot_ctl=f'foot_{p_}_ik.{s_}', toe_ctl=f'toe_{p_}_ik.{s_}', side=1 if s_ == 'L' else -1,
                  anca=f'ORG-thigh_{p_}.{s_}')
CORPO = ['torso', 'hips', 'chest', 'neck', 'head', 'tail_master'] + [LG[k]['foot_ctl'] for k in GAMBE] + [LG[k]['toe_ctl'] for k in GAMBE]
REST = {n: B[n].matrix_local.copy() for n in CORPO}

def foot_dir(k, phi):
    return Rx(phi).to_3x3() @ (Vector((0, -math.cos(FOOT_FLAT), -math.sin(FOOT_FLAT))) * LG[k]['flen'])
def toe_dir(k, psi):
    return Rx(psi).to_3x3() @ (Vector((0, -math.cos(TOE_FLAT), -math.sin(TOE_FLAT))) * LG[k]['tlen'])

def posa_corpo(z, beccheggio, collo, testa, coda, piedi):
    """z, beccheggio (gradi, + = muso in su), collo/testa (gradi, + = muso in giù), coda (gradi in su);
    piedi = {gamba: (dy, dz, phi)}: caviglia rispetto all'anca della gamba (m), phi = punta del piede verso il basso (gradi)."""
    reset(CORPO); upd()
    pbs['torso'].matrix = Matrix.Translation((0, 0, z)) @ attorno(PIVOT, Rx(-math.radians(beccheggio))) @ REST['torso']; upd()
    for n, a in (('neck', collo), ('head', testa)):
        m = pbs[n].matrix.copy(); pbs[n].matrix = attorno(m.translation, Rx(math.radians(a))) @ m; upd()
    m = pbs['tail_master'].matrix.copy(); pbs['tail_master'].matrix = attorno(m.translation, Rx(math.radians(coda))) @ m; upd()
    for k, (dy, dz, phi) in piedi.items():
        anca = pbs[LG[k]['anca']].head.copy()
        ank = anca + Vector((LG[k]['side'] * 0.0, dy, dz))
        ank.x = LG[k]['side'] * 0.085
        d = ank - anca
        if d.length > LG[k]['reach']: ank = anca + d.normalized() * LG[k]['reach']
        ph = math.radians(phi)
        delta = avvolgi(ang_yz(foot_dir(k, ph)) - ang_yz(LG[k]['f_rest']))
        pbs[LG[k]['foot_ctl']].matrix = Matrix.Translation(ank) @ Rx(delta) @ REST[LG[k]['foot_ctl']].to_3x3().to_4x4()
    upd()
    for k, (dy, dz, phi) in piedi.items():
        pb = pbs[LG[k]['toe_ctl']]
        dt = avvolgi(ang_yz(toe_dir(k, math.radians(phi) * 0.6)) - ang_yz(LG[k]['t_rest']))
        pb.matrix = Matrix.Translation(pb.matrix.translation) @ Rx(dt) @ REST[LG[k]['toe_ctl']].to_3x3().to_4x4()
    upd()

def piedi(fr, rr):
    """fr/rr: (dy, dz, phi) per le due gambe davanti e le due dietro (la destra appena sfalsata, si legge meglio)."""
    return {'front.L': fr, 'front.R': (fr[0] - 0.04, fr[1] + 0.02, fr[2]), 'rear.L': rr, 'rear.R': (rr[0] + 0.04, rr[1] + 0.02, rr[2])}

SALTO = [
    # f, z, beccheggio, collo, testa, coda, piedi davanti (dy, dz, phi), piedi dietro
    (1,  -0.06,  4,  4,  2, 10, (-0.10, -0.72, 0), (0.08, -0.74, 0)),            # raccolto, pronto
    (5,  -0.10,  10, -4, -2, 20, (-0.28, -0.42, 40), (0.05, -0.78, 30)),          # stacco: davanti si raccolgono, dietro spingono
    (9,   0.04,  12, -8, -4, 35, (-0.22, -0.34, 70), (0.42, -0.58, 75)),          # in aria: davanti piegate, dietro tese all'indietro
    (14,  0.10,  0,  -12, -6, 45, (-0.18, -0.30, 75), (0.30, -0.34, 80)),         # apice: tutto raccolto
    (20,  0.04, -10, -4, 0, 30, (-0.30, -0.70, 20), (0.26, -0.36, 70)),           # discesa: davanti si allungano per atterrare
    (26, -0.08, -4,  6,  4, 12, (-0.12, -0.74, 0), (0.10, -0.60, 40)),            # atterraggio
]

def chiavi_salto():
    nuova_azione('Salto')
    for f, z, bec, collo, testa, coda, fr, rr in SALTO:
        posa_corpo(z, bec, collo, testa, coda, piedi(fr, rr))
        for n in CORPO:
            pbs[n].keyframe_insert('location', frame=f); pbs[n].keyframe_insert('rotation_quaternion', frame=f)
    reset(CORPO)
    return chiudi_azione('Salto', 26)

# ---------------------------------------------------------------------------------------------------------------- foglio
def foglio(percorso):
    """Una riga per posa: lato destro, 3/4 davanti, da dietro. Workbench con la texture: serve a vedere le pose, non la luce."""
    import tempfile
    for o in bpy.data.objects:
        if o.name.startswith('WGT') or o.name == 'metarig': o.hide_render = True
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
    sc.render.resolution_x = sc.render.resolution_y = 420
    sc.render.film_transparent = False
    # la sciabola come bastone: 0,85 m lungo la Y della presa
    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.85, location=(0, 0.425, 0), rotation=(math.radians(90), 0, 0))
    lama = bpy.context.object; lama.name = 'lama_prova'
    bpy.ops.object.transform_apply(location=True, rotation=True)
    def cam(nome, dirz, centro, orto):
        c = bpy.data.cameras.new(nome); c.type = 'ORTHO'; c.ortho_scale = orto
        o = bpy.data.objects.new(nome, c); sc.collection.objects.link(o)
        o.location = centro + Vector(dirz).normalized() * 6; o.rotation_euler = (-Vector(dirz)).to_track_quat('-Z', 'Y').to_euler(); return o
    camere = [cam('lato', (-1, 0, 0.1), Vector((-0.2, -0.1, 1.0)), 2.6), cam('tq', (-1, -1, 0.3), Vector((-0.2, -0.1, 1.0)), 2.6),
              cam('dietro', (-0.4, 1, 0.25), Vector((-0.2, -0.1, 1.0)), 2.6)]
    righe = [('Sciabola_Fendente', 7, 'Gallop', 10, 'carica'), ('Sciabola_Fendente', 11, 'Gallop', 14, 'colpo'),
             ('Sciabola_Fendente', 15, 'Gallop', 18, 'seguito'), ('Sciabola_Alta', 24, 'Idle', 10, 'alta'),
             ('Frusta', 10, 'Gallop', 4, 'schiocco'), ('Afferra', 8, 'Gallop', 6, 'afferra'),
             ('Salto', 9, None, 0, 'salto 9'), ('Salto', 14, None, 0, 'salto 14'), ('Salto', 20, None, 0, 'salto 20'),
             ('Sguardo_D', 9, 'Gallop', 2, 'sguardo D')]
    tmp = tempfile.mkdtemp()
    files = []
    for i, (clip, f, base, fb, et) in enumerate(righe):
        applica(base, fb, clip, f)
        lama.matrix_world = rig.matrix_world @ pbs['presa.R'].matrix
        for c in camere:
            sc.camera = c; p = os.path.join(tmp, '%02d_%s.png' % (i, c.name)); sc.render.filepath = p
            bpy.ops.render.render(write_still=True); files.append((i, c.name, p, et))
    # montaggio con le immagini di Blender (niente PIL qui)
    W = 420; n = len(righe)
    out = bpy.data.images.new('foglio', W * 3, W * n)
    buf = np.ones((W * n, W * 3, 4), dtype=np.float32)
    for i, cn, p, et in files:
        im = bpy.data.images.load(p); a = np.array(im.pixels[:], dtype=np.float32).reshape(W, W, 4)
        j = ['lato', 'tq', 'dietro'].index(cn)
        buf[(n - 1 - i) * W:(n - i) * W, j * W:(j + 1) * W] = a
    out.pixels = buf.ravel(); out.filepath_raw = percorso; out.file_format = 'JPEG'; out.save()
    print('FOGLIO', percorso, [r[4] for r in righe])

def applica(base, fb, clip, f):
    """Mette il rig in posa: clip di base al fotogramma fb + clip (braccio/sguardo/salto) al fotogramma f, via NLA."""
    ad = rig.animation_data
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    ad.action = None
    reset([pb.name for pb in pbs])
    F = 500
    for nome, fr, modo in ((base, fb, 'REPLACE'), (clip, f, 'COMBINE' if clip and clip.startswith('Sguardo') else 'REPLACE')):
        if not nome: continue
        act = bpy.data.actions[nome]; tr = ad.nla_tracks.new(); tr.name = nome
        st = tr.strips.new(nome, int(F - (fr - act.frame_range[0])), act); st.blend_type = modo
        if hasattr(st, 'action_slot') and len(getattr(act, 'slots', [])): st.action_slot = act.slots[0]
        st.extrapolation = 'HOLD'
    sc.frame_set(F); upd()

# ---------------------------------------------------------------------------------------------------------------- main
costruisci_braccio()
for nome, chiavi in CLIP_BRACCIO.items():
    nuova_azione(nome)
    for f, posa in chiavi:
        posa_braccio(posa); chiavi_braccio(f)
    reset(OSSA + ('presa.R',))
    chiudi_azione(nome, chiavi[-1][0])
chiavi_sguardo('Sguardo_D', -1)        # destra del cavallo = -X: si gira in senso orario visto dall'alto
chiavi_sguardo('Sguardo_S', +1)
chiavi_salto()
for act in bpy.data.actions:
    if act.name in CLIP_BRACCIO or act.name.startswith('Sguardo') or act.name == 'Salto':
        for fc in (act.fcurves if hasattr(act, 'fcurves') else []):
            for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.easing = 'AUTO'
print('CLIP', sorted(a.name for a in bpy.data.actions))
if ARGV:
    os.makedirs(os.path.dirname(os.path.abspath(ARGV[0])), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(ARGV[0]), relative_remap=True, copy=False)
    print('SALVATO', ARGV[0])
if len(ARGV) > 1:
    foglio(os.path.abspath(ARGV[1]))
