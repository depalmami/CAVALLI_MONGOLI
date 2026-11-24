# ATTO 1 · L'EROE, animato (storyboard v2): 5,5 s all'alba sul Kherlen, in Cycles (con sole a 4° EEVEE è piatto).
#   S03  2 s    il kolossal: la camera avanza lenta sul cavallo fermo in controluce, che respira e si guarda intorno (Idle)
#   S04  1,5 s  ZOOM A SCATTO dalla pancia di cartone ai piedi nudi; le dita dei piedi si muovono (stop della musica)
#   S05  1 s    silenzio: la testa si gira lentissima fino a GUARDARE IN MACCHINA (la camera sta dove arriva lo sguardo)
#   S06  1 s    GAMBE A VUOTO: galoppo a 2,5× sul posto, terra che vola; poi parte di colpo verso la camera e le passa accanto,
#               e dove stava resta una NUVOLA DI POLVERE CON LA SUA SAGOMA
# Stesso metodo di shot-s14.py (rig vivo, strisce NLA col tempo e l'influenza a chiavi), attrezzi in shot.py.
#
# uso:  blender -b --python tools/trailer3d/shot-atto1.py -- <cartella base> prova|finale [S03 S04 S05 S06]
#   ogni shot va in <cartella base>/<shot>/ (fotogrammi + video); con «finale» salva anche trailer/blender/shot/<shot>.blend
import bpy, sys, os, math, random
QUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, QUI)
import animatic as AN
import animatic2 as A2
import pose
import shot as SH
from shot import curva, sm
from mathutils import Vector, Quaternion

ARGV = sys.argv[sys.argv.index('--') + 1:]
BASE = os.path.abspath(ARGV[0]); MODO = ARGV[1] if len(ARGV) > 1 else 'prova'
LISTA = ARGV[2:] or ['S03', 'S04', 'S05', 'S06']
DUR = dict(S03=48, S04=36, S05=24, S06=24)

def mondo_alba(sole_rel, n, **kw):
    SH.prima(MODO, 'CYCLES')
    m = A2.mondo(0, sole_rel=sole_rel, **kw)
    SH.dopo(MODO, 'CYCLES', n)
    return m

def cavallo(m, x, y, base, t0, passo=1.0, n=48):
    """Il cavallo vivo fermo in (x, y), con la clip `base` che scorre da t0 a `passo` fotogrammi per fotogramma."""
    radice, rig, az = pose.eroe_vivo('eroe')
    st = pose.traccia(rig, az[base])
    for f in range(1, n + 1):
        st.strip_time = t0 + (f - 1) * passo; st.keyframe_insert('strip_time', frame=f)
        st.influence = 1.0; st.keyframe_insert('influence', frame=f)
    radice.location = A2.P(m, x, y); radice.rotation_euler = (0, 0, math.radians(A2.yaw_su(m, x, y)))
    return radice, rig, az

def testa_mondo(rig):
    pb = rig.pose.bones['DEF-head']; W = rig.matrix_world
    return W @ pb.head, W @ pb.tail                     # nuca, muso

S = {}
def shot(nome):
    def d(f): S[nome] = f; return f
    return d

# ---------------------------------------------------------------------------------------------------------------- S03
@shot('S03')
def s03():
    n = DUR['S03']; m = mondo_alba(180, n)              # sole alle spalle del cavallo: controluce verso di noi
    cavallo(m, 0, 0, 'Idle', 10, n=n)
    cam = AN.camera(A2.P(m, 0.35, -9.6, 0.35), A2.P(m, 0, 0, -0.4), 50)
    for f in (1, n):                                    # carrellata lenta in avanti, la mira sale appena
        k = (f - 1) / (n - 1)
        SH.chiave_camera(cam, f, A2.P(m, 0.35, -9.6 + 1.7 * k, 0.35 + 0.05 * k), A2.P(m, 0, 0, -0.4 + 0.15 * k))

# ---------------------------------------------------------------------------------------------------------------- S04
@shot('S04')
def s04():
    n = DUR['S04']; m = mondo_alba(160, n, erba=None)
    m.erba_vicino(s=0, lat=7, raggio=7, densita=480)
    radice, rig, az = cavallo(m, -7, 0, 'Idle', 30, n=n)
    # le dita dei piedi davanti si muovono: rotazioni RELATIVE (COMBINE) sul controllo delle dita, attorno all'asse X del modello
    ad = rig.animation_data; ad.action_blend_type = 'COMBINE'
    for lato, fase in (('L', 0.0), ('R', 0.5)):
        pb = rig.pose.bones['toe_front_ik.%s' % lato]
        asse = rig.data.bones[pb.name].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0))
        for f in range(1, n + 1):
            a = 0.0 if f < 9 else math.radians(22) * max(0.0, math.sin(2 * math.pi * ((f - 9) / 8.0 + fase))) * (1 - sm((f - 30) / 6))
            pb.rotation_quaternion = Quaternion(asse, -a); pb.keyframe_insert('rotation_quaternion', frame=f)
    # ZOOM A SCATTO: la camera sta ferma a 18 cm da terra; dal fotogramma 2 al 6 l'ottica passa da 22 a 42 mm e la mira scende
    # dalla pancia di cartone ai piedi, poi un piccolo rimbalzo e fermo
    pos = A2.P(m, -7.55, -1.25, 0.18)
    cam = AN.camera(pos, A2.P(m, -7.0, -0.05, 0.9), 22, fstop=3.2, fuoco=A2.P(m, -7.0, -0.25, 0.25))
    for f, lens, mz in ((1, 22, 0.95), (2, 22, 0.95), (6, 44, 0.30), (8, 41, 0.34), (10, 42, 0.32), (n, 43, 0.31)):
        SH.chiave_camera(cam, f, pos, A2.P(m, -7.0, -0.05, mz), lens=lens)

# ---------------------------------------------------------------------------------------------------------------- S05
@shot('S05')
def s05():
    n = DUR['S05']; m = mondo_alba(200, n)
    radice, rig, az = cavallo(m, 0, 0, 'Idle', 12, passo=0.5, n=n)
    sg = pose.traccia(rig, az['Sguardo_D'], 'COMBINE')
    for f in range(1, n + 1):
        sg.strip_time = 9.0; sg.keyframe_insert('strip_time', frame=f)
        sg.influence = curva([(1, 0.0), (4, 0.0), (20, 1.0), (n, 1.0)], f); sg.keyframe_insert('influence', frame=f)
    # la camera sta dove arriva lo sguardo all'ultimo fotogramma (misurato), e si avvicina appena
    bpy.context.scene.frame_set(n); bpy.context.view_layer.update()
    nu, mu = testa_mondo(rig)
    d = mu - nu; d.z = 0; d.normalize()
    mira = mu * 0.6 + nu * 0.4
    cam = AN.camera(mira + d * 1.75, mira, 55, fstop=2.8, fuoco=mira)
    for f, dist in ((1, 1.75), (n, 1.5)):
        SH.chiave_camera(cam, f, mira + d * dist + Vector((0, 0, 0.05)), mira, fuoco=dist)

# ---------------------------------------------------------------------------------------------------------------- S06
@shot('S06')
def s06():
    n = DUR['S06']; m = mondo_alba(150, n)
    radice, rig, az = pose.eroe_vivo('eroe')
    gal = pose.traccia(rig, az['Gallop'])
    yaw0 = A2.yaw_su(m, 0, 0)
    corsa = {12: (0.0, 0.0), 13: (-0.25, -1.2), 14: (-0.6, -3.0), 15: (-1.0, -5.0), 16: (-1.4, -7.2), 17: (-1.8, -9.5)}
    for f in range(1, n + 1):
        gal.strip_time = min(40.0, 3.0 + 2.5 * (f - 1)); gal.keyframe_insert('strip_time', frame=f)     # gambe a 2,5×
        gal.influence = 1.0; gal.keyframe_insert('influence', frame=f)
        x, y = corsa.get(f, (0.0, 0.0) if f < 12 else (-1.8, -9.5))
        radice.location = A2.P(m, x, y)
        radice.rotation_euler = (math.radians(4.0 if f <= 12 else 9.0), 0, math.radians(yaw0 - (12.0 if f > 12 else 0.0)))
        radice.keyframe_insert('location', frame=f); radice.keyframe_insert('rotation_euler', frame=f)
    for o in (radice, rig, *rig.children): SH.nascondi_da(o, 17)
    # la sagoma: la posa del fotogramma 12 cotta in una mesh di polvere, che compare quando lui parte e si sfalda piano
    sc = bpy.context.scene; sc.frame_set(12); bpy.context.view_layer.update()
    corpo = next(o for o in rig.children if o.type == 'MESH')
    me = bpy.data.meshes.new_from_object(corpo.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    sag = bpy.data.objects.new('sagoma', me); sc.collection.objects.link(sag); sag.matrix_world = corpo.matrix_world.copy()
    sag.data.materials.clear(); sag.data.materials.append(AN.materiale_polvere((0.80, 0.62, 0.44, 1), 0.45))
    SH.appari_da(sag, 13)
    s0 = sag.scale.copy(); sag.keyframe_insert('scale', frame=13); sag.scale = s0 * 1.05; sag.keyframe_insert('scale', frame=n)
    random.seed(6); mat = AN.materiale_polvere((0.80, 0.62, 0.44, 1), 0.18); vs = me.vertices; Mw = sag.matrix_world
    for i in range(90):
        q = Mw @ vs[random.randrange(len(vs))].co
        SH.sbuffo(q, 13 + random.randrange(3), mat, random.uniform(0.04, 0.11),
                  (random.uniform(-0.15, 0.15), random.uniform(-0.1, 0.25), random.uniform(0.0, 0.25)), vita=12, n=n)
    # terra che vola dietro i piedi mentre le gambe girano a vuoto
    zolla = AN.materiale('zolla', colore=(0.16, 0.11, 0.07, 1), rough=1.0); polv = AN.materiale_polvere((0.72, 0.56, 0.40, 1), 0.16)
    base = A2.P(m, 0, 0)
    for f in range(2, 13):
        for k in range(3):
            q = Vector(base) + Vector((random.uniform(-0.2, 0.2), random.uniform(0.0, 0.5), 0.05))
            SH.sbuffo(q, f, zolla, random.uniform(0.012, 0.03), (random.uniform(-0.3, 0.3), random.uniform(0.6, 1.4), random.uniform(0.3, 0.8)), vita=6, n=n, nome='zolla')
        SH.sbuffo(Vector(base) + Vector((random.uniform(-0.25, 0.25), random.uniform(0.1, 0.6), 0.05)), f, polv,
                  random.uniform(0.08, 0.16), (random.uniform(-0.2, 0.2), random.uniform(0.3, 0.8), random.uniform(0.1, 0.3)), vita=12, n=n)
    AN.camera(A2.P(m, 0.6, -4.2, 0.45), A2.P(m, 0, 0, 0.85), 30)

if __name__ == '__main__':
    for nome in LISTA:
        S[nome]()
        if MODO == 'finale': SH.salva(nome)
        SH.gira(os.path.join(BASE, nome), nome, MODO)
