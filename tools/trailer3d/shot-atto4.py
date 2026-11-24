# ATTO 4 · IL BOSS + CODA, animati (storyboard v2): 9 s di notte a Karakorum + la birra nel nero. EEVEE, render calmo (shot.py).
#   S21  1 s    la schiena a gradini avanza contro la luna; un tonfo a ogni passo (la camera trema)
#   S22  2 s    sotto il ventre: la camera scorre fra le 14 gambe che marciano; una gamba è FUORI PASSO, fa un saltello e rientra
#   S23  1,5 s  la testa si gira verso di noi e la mascella si spalanca; vapore dalla bocca
#   S24  1 s    il Boss si impenna sopra il cavallino, che alza la sciabola: la lama prende un lampo di luna
#   S25  1 s    la carica, col tele: lui galoppa con la sciabola alta, il Boss gli marcia contro, la distanza si chiude
#   S26  1 s    il morso a vuoto sulla polvere; poi il Boss TOSSISCE uno sbuffo di polvere
#   S27  1 s girato + 0,5 s di fermo: il salto al rallentatore sopra la schiena, la camera gira, nel fermo GUARDA IN MACCHINA
#   S28  1 s    (coda) il bicchiere sui pattini attraversa il nero
# Il montaggio: atto4.mp4 (S21–S27, 9 s, col fermo di S27) e coda.mp4 (0,5 s di fermo + 1,5 s di nero + S28 = 3 s).
#
# uso:  blender -b --python tools/trailer3d/shot-atto4.py -- <cartella base> prova|finale [S21 … S28]
#       blender -b --python tools/trailer3d/shot-atto4.py -- <cartella base> prova|finale monta      (solo il montaggio)
import bpy, sys, os, math, random, subprocess
QUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, QUI)
import animatic as AN
import animatic2 as A2
import pose
import shot as SH
import fumo as FU
import luna as LU
from shot import curva, sm
from mathutils import Vector

ARGV = sys.argv[sys.argv.index('--') + 1:]
BASE = os.path.abspath(ARGV[0]); MODO = ARGV[1] if len(ARGV) > 1 else 'prova'
TUTTI = ['S21', 'S22', 'S23', 'S24', 'S25', 'S26', 'S27', 'S28']
LISTA = ARGV[2:] or TUTTI
DUR = dict(S21=24, S22=48, S23=36, S24=24, S25=24, S26=24, S27=24, S28=24)
P = A2.P

def notte(luna_rel, luna_el, esposizione, n):
    SH.prima(MODO, 'EEVEE')
    m = A2.notte_boss(luna_rel, luna_el, esposizione)
    SH.dopo(MODO, 'EEVEE', n)
    return m

def tonfo(fase, forza):
    """Scossa della camera dopo ogni passo (le zampe appoggiano a fase 0,25 e 0,75): scende di colpo e torna oscillando."""
    u = (fase - 0.25) % 0.5
    return Vector((0, 0, -forza * math.exp(-u * 30) * math.cos(u * 60)))

def boss_vivo(m, scala=1.35):
    r, pz, base = pose.boss_crea(); r.scale = (scala,) * 3; r.rotation_mode = 'XYZ'
    return r, pz, base

def cavallo_vivo(m, x, y, yaw, corpo, arma=None):
    radice, rig, az = pose.eroe_vivo('eroe')
    radice.location = P(m, x, y); radice.rotation_euler = (0, 0, math.radians(yaw))
    st = {k: pose.traccia(rig, az[k], 'COMBINE' if k.startswith('Sguardo') else 'REPLACE') for k in corpo}
    if arma: pose.arma_viva(rig, arma)
    return radice, rig, st

def chiave_striscia(st, f, tempo, influenza=1.0):
    st.strip_time = tempo; st.keyframe_insert('strip_time', frame=f)
    st.influence = influenza; st.keyframe_insert('influence', frame=f)

def testa_mondo(rig):
    pb = rig.pose.bones['DEF-head']; W = rig.matrix_world
    return W @ pb.head, W @ pb.tail

def guarda_in(rig, radice, cam_pos, f, yaw_di, da, passate=3, rot_x=0.0):
    """Gira il corpo (dal fotogramma `da` a f, in smoothstep) finché all'ultimo fotogramma il muso punta la camera: MISURATO."""
    sc = bpy.context.scene; corr = 0.0
    for _ in range(passate):
        sc.frame_set(f); bpy.context.view_layer.update()
        nu, mu = testa_mondo(rig); d = mu - nu; c = Vector(cam_pos) - mu
        ang = math.degrees(math.atan2(d.x * c.y - d.y * c.x, d.x * c.x + d.y * c.y)); corr += ang
        for g in range(da, f + 1):
            radice.rotation_euler = (math.radians(rot_x), 0, math.radians(yaw_di(g) + corr * sm((g - da) / max(1, f - da))))
            radice.keyframe_insert('rotation_euler', frame=g)
    print('SGUARDO IN MACCHINA: correzione %.1f°, resto %.1f°' % (corr, ang))

def bocca_fumo(r, f_dir, dentro=(-0.65, 0, 0.42)):
    """Per il fumo dalla bocca del Boss: (origine(f), direzione). L'origine sta DENTRO la bocca aperta, dietro i denti, e segue la
    mascella fotogramma per fotogramma; la direzione è l'asse del muso in piano, misurato al fotogramma f_dir."""
    sc = bpy.context.scene; mascella = next(o for o in r.children_recursive if o.name.startswith('Mascella'))
    def asse():
        pts = [mascella.matrix_world @ Vector(c) for c in mascella.bound_box]
        d = max(pts, key=lambda p: p.x) - min(pts, key=lambda p: p.x); d.z = 0; return d.normalized()
    sc.frame_set(f_dir); bpy.context.view_layer.update(); verso = asse()
    return (lambda f: pose.bocca(r) + Vector(dentro)), verso

S = {}
def shot(nome):
    def d(f): S[nome] = f; return f
    return d

# ---------------------------------------------------------------------------------------------------------------- S21
@shot('S21')
def s21():
    n = DUR['S21']; m = notte(180, 22, 0.0, n)
    r, pz, base = boss_vivo(m); v = pose.boss_velocita(0.9, 24)
    for f in range(1, n + 1):
        r.location = P(m, -5.5 + v * (f - 1), 0); r.keyframe_insert('location', frame=f)
        pose.boss_posa(pz, base, fase=0.1 + (f - 1) / 24, passo=0.9, chiave=f)
    cam = AN.camera(P(m, -0.5, -9, 0.3), P(m, -1.5, 0, 3.8), 40)
    for f in range(1, n + 1):
        SH.chiave_camera(cam, f, Vector(P(m, -0.5, -9, 0.3)) + tonfo(0.1 + (f - 1) / 24, 0.035), P(m, -1.5, 0, 3.8))

# ---------------------------------------------------------------------------------------------------------------- S22
@shot('S22')
def s22():
    n = DUR['S22']; m = notte(180, 28, 0.3, n)
    r, pz, base = boss_vivo(m); v = pose.boss_velocita(1.2, 24)
    for f in range(1, n + 1):
        r.location = P(m, v * (f - 1), 0); r.keyframe_insert('location', frame=f)
        sf = curva([(1, 0.5), (24, 0.5), (32, 0.0)], f)                       # fuori passo di mezzo ciclo, poi rientra…
        hop = 0.18 * math.sin(math.pi * (f - 24) / 8) if 24 <= f <= 32 else 0.0   # …con un saltello
        pose.boss_posa(pz, base, fase=0.22 + (f - 1) / 24, passo=1.2, ginocchio=1.3,
                       fuori={'Coscia_S2_D': sf}, saltello={'Coscia_S2_D': hop}, chiave=f)
    cam = AN.camera(P(m, 3.0, -1.6, 0.3), P(m, -6.0, 0.2, 1.0), 24)
    for f in range(1, n + 1):                                                  # la carrellata va appena più piano del Boss
        dx = 0.85 * v * (f - 1)
        SH.chiave_camera(cam, f, Vector(P(m, 3.0 + dx, -1.6, 0.3)) + tonfo(0.22 + (f - 1) / 24, 0.02), P(m, -6.0 + dx, 0.2, 1.0))

# ---------------------------------------------------------------------------------------------------------------- S23
@shot('S23')
def s23():
    n = DUR['S23']; m = notte(150, 24, 0.0, n)
    r, pz, base = boss_vivo(m); r.location = P(m, 0, 0)
    for f in range(1, n + 1):
        pose.boss_posa(pz, base, fase=0.5 + (f - 1) / 96, passo=0.35,
                       testa=curva([(1, 0), (14, -26), (n, -26)], f),
                       mascella=curva([(1, 0), (8, 0), (20, 44), (24, 38), (n, 40)], f),
                       alza=curva([(1, 0), (20, 8), (n, 6)], f), chiave=f)
    # il fiato: un getto di gas procedurale (volume in EEVEE, fumo.py) che esce dal fondo della bocca aperta, sale col calore
    FU.eevee_volume(MODO == 'finale')
    bocca_f, verso = bocca_fumo(r, 24)
    FU.soffio(bocca_f, verso + Vector((0, 0, 0.12)), 15, 29, n, nome='fiato', velocita=3.2, sale=0.16, grana=3.0,
              taglio=1.05, lunghezza=2.8, luce=((0.55, -0.6, -0.45), 2.4))
    cam = AN.camera(P(m, 7.4, -5.8, 2.1), P(m, 3.0, -0.7, 2.0), 50, fstop=2.8, fuoco=P(m, 3.2, -0.7, 2.0))
    for f in (1, n):
        k = (f - 1) / (n - 1)
        SH.chiave_camera(cam, f, P(m, 7.4 - 0.4 * k, -5.8 + 0.4 * k, 2.1), P(m, 3.0, -0.7, 2.0), fuoco=6.0 - 0.5 * k)

# ---------------------------------------------------------------------------------------------------------------- S24
@shot('S24')
def s24():
    n = DUR['S24']; m = notte(90, 30, 0.2, n)
    r, pz, base = boss_vivo(m); r.location = P(m, -4.0, 0)
    for f in range(1, n + 1):
        pose.boss_posa(pz, base, fase=0.4 + (f - 1) / 48, passo=0.4,
                       alto=curva([(1, 0.0), (10, 1.3), (n, 1.3)], f),
                       mascella=curva([(1, 8), (12, 26), (n, 24)], f), alza=curva([(1, 0), (10, -18), (n, -16)], f), chiave=f)
    radice, rig, st = cavallo_vivo(m, 2.0, 0, -90, ['Idle', 'Sciabola_Alta'], arma='saber')
    for f in range(1, n + 1):
        chiave_striscia(st['Idle'], f, 10 + 0.5 * (f - 1))
        chiave_striscia(st['Sciabola_Alta'], f, curva([(1, 1.0), (16, 24.0), (n, 24.0)], f))
    # il lampo di luna sulla lama: una scintilla che segue la punta e brilla quando la sciabola arriva in alto. È un oggetto che
    # SPLENDE ma non illumina (una luce vera rischiarava tutto il terreno come di giorno)
    mat = bpy.data.materials.new('lampo'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.85, 0.9, 1.0, 1); em.inputs['Strength'].default_value = 40
    nt.links.new(em.outputs[0], nt.nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
    lampo = AN.sfera((0, 0, 0), 0.035, mat, 'lampo')
    sc = bpy.context.scene
    for f in range(1, n + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        pb = rig.pose.bones['presa.R']; lampo.location = rig.matrix_world @ (pb.matrix @ Vector((0, 0.8, 0)))
        lampo.keyframe_insert('location', frame=f)
        k = max(0.001, curva([(1, 0), (15, 0), (18, 1.0), (22, 0), (n, 0)], f)); lampo.scale = (k,) * 3; lampo.keyframe_insert('scale', frame=f)
    AN.camera(P(m, 4.6, -0.8, 0.25), P(m, -1.5, 0, 2.6), 18)

# ---------------------------------------------------------------------------------------------------------------- S25
@shot('S25')
def s25():
    n = DUR['S25']; m = notte(180, 18, 0.0, n)
    r, pz, base = boss_vivo(m); v = pose.boss_velocita(1.2, 20)
    for f in range(1, n + 1):
        r.location = P(m, -10.0 + v * (f - 1), 0); r.keyframe_insert('location', frame=f)
        pose.boss_posa(pz, base, fase=0.6 + (f - 1) / 20, passo=1.2, mascella=16, alza=4, chiave=f)
    radice, rig, st = cavallo_vivo(m, 4.5, 0, -90, ['Gallop', 'Sciabola_Alta'], arma='saber')
    random.seed(25); polv = AN.materiale_polvere((0.02, 0.022, 0.03, 1), 0.08)
    for f in range(1, n + 1):
        x = 4.5 - 0.17 * (f - 1)
        radice.location = P(m, x, 0); radice.keyframe_insert('location', frame=f)
        chiave_striscia(st['Gallop'], f, 3.0 + (f - 1))
        chiave_striscia(st['Sciabola_Alta'], f, 24.0)
        if f % 2 == 0:
            SH.sbuffo(Vector(P(m, x + 0.3, random.uniform(-0.15, 0.15), 0.05)), f, polv, random.uniform(0.12, 0.22),
                      (random.uniform(0.3, 0.7), random.uniform(-0.2, 0.2), random.uniform(0.1, 0.3)), vita=12, n=n)
    cam = AN.camera(P(m, 14, 1.8, 1.6), P(m, -3, 0, 2.0), 85)
    for f in range(1, n + 1):
        SH.chiave_camera(cam, f, Vector(P(m, 14, 1.8, 1.6)) + tonfo(0.6 + (f - 1) / 20, 0.012), P(m, -3, 0, 2.0))

# ---------------------------------------------------------------------------------------------------------------- S26
@shot('S26')
def s26():
    n = DUR['S26']; m = notte(210, 22, 0.0, n)
    r, pz, base = boss_vivo(m)
    for f in range(1, n + 1):
        r.location = P(m, curva([(1, 0.0), (4, 0.55), (n, 0.55)], f), 0); r.keyframe_insert('location', frame=f)   # l'affondo
        pose.boss_posa(pz, base, fase=0.8 + (f - 1) / 60, passo=0.5,
                       mascella=curva([(1, 34), (3, 34), (4, 2), (9, 2), (11, 20), (16, 6), (n, 6)], f),       # SNAP… poi la tosse
                       alza=curva([(1, 0), (4, -4), (9, -2), (11, 10), (16, 0), (n, 0)], f), chiave=f)
    # dove doveva esserci il cavallo, solo polvere
    AN.polvere(P(m, 6.0, 0, 0.8), n=45, raggio=1.6, size=(0.12, 0.35), colore=(0.015, 0.016, 0.022, 1), alfa=0.05, schiaccia=0.6)
    # il colpo di tosse: una sbuffata di polvere scura, breve e veloce, dalla bocca (fumo.py)
    FU.eevee_volume(MODO == 'finale')
    bocca_f, verso = bocca_fumo(r, 11, dentro=(-0.35, 0, 0.18))
    FU.soffio(bocca_f, verso + Vector((0, 0, 0.04)), 10, 14, n, nome='tosse', velocita=5.0, r0=0.34, apertura=0.42, sale=0.05, grana=3.2,
              densita=4.5, lunghezza=3.0, colore=(0.44, 0.42, 0.40), taglio=0.8, spegni=0.8, luce=((0.55, -0.6, -0.45), 2.0))
    AN.camera(P(m, 6.6, -5.6, 1.5), P(m, 3.6, 0, 1.9), 35)

# ---------------------------------------------------------------------------------------------------------------- S27
@shot('S27')
def s27():
    n = DUR['S27']; m = notte(145, 70, 0.0, n)
    r, pz, base = boss_vivo(m); r.location = P(m, 0, 0)
    for f in range(1, n + 1):
        pose.boss_posa(pz, base, fase=0.1 + (f - 1) / 72, passo=0.8, chiave=f)          # sotto, rallentato come il resto
    radice, rig, st = cavallo_vivo(m, -0.4, 0, 90, ['Salto', 'Sciabola_Alta', 'Sguardo_D'], arma='saber')
    for f in range(1, n + 1):                                                  # rallentatore: la clip del salto da 6 a 14 in 24 fotogrammi
        u = (f - 1) / (n - 1)
        chiave_striscia(st['Salto'], f, 6.0 + 8.0 * u)
        chiave_striscia(st['Sciabola_Alta'], f, 24.0)
        chiave_striscia(st['Sguardo_D'], f, 9.0, curva([(1, 0.0), (12, 0.0), (22, 1.0), (n, 1.0)], f))
        radice.location = P(m, -0.4 - 1.1 * u, 0, 4.4 + 0.6 * math.sin(math.pi * u / 2)); radice.keyframe_insert('location', frame=f)
        radice.rotation_euler = (0, 0, math.radians(90)); radice.keyframe_insert('rotation_euler', frame=f)
    # la camera gira di 30° attorno a lui (bullet time) e finisce dove l'inquadratura del verticale funzionava
    cx, cy = -1.5, 0.0; a1 = math.atan2(-1.8, 1.3); rr = math.hypot(1.3, 1.8)
    cam = AN.camera(P(m, -0.2, -1.8, 2.6), P(m, -1.45, 0, 5.4), float(os.environ.get('LUNA_L', 23)))       # 23 mm (era 26): con la luna grande il cavallo ha bisogno d'aria intorno
    for f in range(1, n + 1):
        a = a1 - math.radians(30) * (1 - sm((f - 1) / (n - 1)))
        mira = P(m, -0.4 - 1.1 * (f - 1) / (n - 1), 0, 5.2)                  # la mira segue il cavallo in volo
        SH.chiave_camera(cam, f, P(m, cx + rr * math.cos(a), cy + rr * math.sin(a), 2.6), mira)
    bpy.context.scene.frame_set(n); bpy.context.view_layer.update()
    guarda_in(rig, radice, cam.matrix_world.translation.copy(), n, lambda g: 90.0, 12)
    # la luna: ENORME, con mari e crateri, sempre dietro al cavallo (che resta «inscritto» nel disco); la luna liscia di prima va via
    vecchia = next((o for o in bpy.data.objects if o.type == 'MESH' and o.data.materials and o.data.materials[0] and o.data.materials[0].name == 'luna'), None)
    cavallo_mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('CavalloCartone'))
    def centro_cavallo(f):
        ev = cavallo_mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); pts = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
        return sum(pts, Vector()) / 8
    LU.luna_grande(cam, centro_cavallo, n, raggio=float(os.environ.get('LUNA_R', 19.0)), su=float(os.environ.get('LUNA_SU', 1.0)), forza=float(os.environ.get('LUNA_F', 0.62)), vecchia=vecchia)
    ri = bpy.data.lights.new('riempimento', 'SUN'); ri.energy = float(os.environ.get('LUNA_RI', 0.6)); ri.color = (0.72, 0.82, 1.0); ri.angle = math.radians(20); ri.use_shadow = False       # senza ombre: i raggi vengono da sotto e il Boss li copre
    ro = bpy.data.objects.new('riempimento', ri); bpy.context.scene.collection.objects.link(ro); ro.parent = cam    # luce frontale: il cavallo resta leggibile contro la luna
    coll = bpy.data.collections.new('riempimento_riceve')                                                      # la luce illumina SOLO il cavallo: il Boss sotto resta nella notte
    for o in {cavallo_mesh, *[x for x in radice.children_recursive if x.type == 'MESH']}: coll.objects.link(o)
    ro.light_linking.receiver_collection = coll

# ---------------------------------------------------------------------------------------------------------------- S28
@shot('S28')
def s28():
    n = DUR['S28']
    SH.prima(MODO, 'EEVEE'); AN.nuovo(campioni=32); SH.dopo(MODO, 'EEVEE', n)
    sc = bpy.context.scene
    w = bpy.data.worlds.new('nero'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1); sc.world = w
    rb, pezzi, base = pose.birra_crea(); rb.scale = (2.0,) * 3; rb.rotation_mode = 'XYZ'
    for f in range(1, n + 1):                                                  # attraversa il quadro da sinistra a destra
        rb.location = (-1.6 + 3.2 * (f - 1) / (n - 1), 0, 0); rb.rotation_euler = (0, 0, 0)
        rb.keyframe_insert('location', frame=f); rb.keyframe_insert('rotation_euler', frame=f)
        pose.birra_posa(pezzi, base, fase=f / 12.0, forza=1.7, piega=3, chiave=f)
    for pos, col, e in (((0.6, 0.8, 1.0), '#ffd9a0', 900), ((-0.8, 0.7, 0.5), '#a0b8ff', 350), ((0.3, -1.5, 1.2), '#ffe6c0', 40)):
        l = AN.lampada(pos, colore=col, energia=e, raggio=0.2)
        l.parent = rb; l.location = Vector(pos) / 2.0                          # figlie del bicchiere (scala 2): lo accompagnano
    AN.camera((0, -3.2, 0.45), (0, 0, 0.42), 50)

# ---------------------------------------------------------------------------------------------------------------- montaggio
def ff(*a): subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *a], check=True)

def monta():
    W, H = (1080, 1920) if MODO == 'finale' else (540, 960)
    v = lambda s: os.path.join(BASE, s, '%s-%s.mp4' % (s, MODO))
    enc = ['-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', '24', '-movflags', '+faststart']
    # atto 4: S21…S26 e S27 col suo fermo di 0,5 s (12 fotogrammi)
    ing = sum((['-i', v(s)] for s in TUTTI[:7]), [])
    filt = ''.join('[%d:v]setpts=PTS-STARTPTS%s[v%d];' % (i, ',tpad=stop_mode=clone:stop=12' if i == 6 else '', i) for i in range(7))
    filt += ''.join('[v%d]' % i for i in range(7)) + 'concat=n=7:v=1:a=0[o]'
    ff(*ing, '-filter_complex', filt, '-map', '[o]', *enc, os.path.join(BASE, 'atto4.mp4'))
    # coda: 0,5 s ancora sul fermo del salto, 1,5 s di nero (lo spazio per i titoli), 1 s di birra
    ff('-sseof', '-0.05', '-i', v('S27'), '-f', 'lavfi', '-i', 'color=c=black:s=%dx%d:r=24:d=1.5' % (W, H), '-i', v('S28'),
       '-filter_complex', '[0:v]trim=end_frame=1,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop=11[a];[1:v]setpts=PTS-STARTPTS[b];'
       '[2:v]setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0[o]', '-map', '[o]', *enc, os.path.join(BASE, 'coda.mp4'))
    print('MONTATO', os.path.join(BASE, 'atto4.mp4'), os.path.join(BASE, 'coda.mp4'))

if __name__ == '__main__':
    if LISTA == ['monta']: monta()
    else:
        for nome in LISTA:
            S[nome]()
            if MODO == 'finale': SH.salva(nome)
            SH.gira(os.path.join(BASE, nome), nome, MODO)
        if set(LISTA) == set(TUTTI): monta()
