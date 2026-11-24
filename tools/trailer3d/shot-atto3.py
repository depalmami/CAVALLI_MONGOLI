# ATTO 3 · IL VIAGGIO, animato (storyboard v2): 3,5 s di montaggio a raffica, un mondo diverso a ogni battito, il sole più basso a ogni taglio.
# EEVEE (S18 in Cycles: con sole basso EEVEE è piatto), render calmo (shot.py).
#   S15  0,5 s  Piana del Tuul: il cavallo di profilo, sempre nello STESSO punto del quadro e con lo STESSO galoppo; cambia il mondo
#   S16  0,5 s  Dune: stessa posa; il lama sulla cresta lo segue girando la testa, impassibile
#   S18  0,5 s  Khar Balgas al tramonto (Cycles): l'aquila attraversa il cielo in alto, il sole è un disco sull'orizzonte
#   S19  0,5 s  Erdene Zuu nell'ora blu: stupa e lanterne che tremolano
#   S20  1,5 s  Karakorum di notte, la terra trema: cerchi nella pozza, i sassi saltano, il cavallo si ferma e gira la testa
#               (la musica si spegne qui: l'audio non c'è ancora, lo storyboard dice dove)
# Gli shot di profilo (S15–S19) hanno la camera ATTACCATA al cavallo: lui galoppa in avanti a 0,17 m a fotogramma (il passo che non
# pattina) e il quadro lo segue, quindi sta fermo nel punto e il mondo scorre. La posa di partenza del galoppo è la stessa in tutti.
#
# uso:  blender -b --python tools/trailer3d/shot-atto3.py -- <cartella base> prova|finale [S15 … S20 | monta]
import bpy, bmesh, sys, os, math, random, subprocess
QUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, QUI)
import animatic as AN
import animatic2 as A2
import kit, pose
import fumo as FU
import shot as SH
from shot import curva, sm
from mathutils import Vector, Matrix, Quaternion

ARGV = sys.argv[sys.argv.index('--') + 1:]
BASE = os.path.abspath(ARGV[0]); MODO = ARGV[1] if len(ARGV) > 1 else 'prova'
TUTTI = ['S15', 'S16', 'S18', 'S19', 'S20']
LISTA = ARGV[2:] or TUTTI
DUR = dict(S15=12, S16=12, S18=12, S19=12, S20=36)
P = A2.P
V = 0.17                                               # m a fotogramma: il galoppo del protagonista senza pattinare
V_PASSO = 0.034                                        # m a fotogramma: il passo (Walk, 24 fotogrammi a ciclo) senza pattinare (misurato)
T0 = 2.0                                               # fotogramma della clip Gallop da cui parte OGNI shot di profilo: la stessa posa

def giorno(k, n, motore='EEVEE', **kw):
    SH.prima(MODO, motore); m = A2.mondo(k, **kw); SH.dopo(MODO, motore, n); return m

def avanti(m, x0, y0, yaw, d, lato=0.0, dz=0.0):
    """Il punto a d metri davanti (direzione del cavallo con quel yaw: 0 = -Y) e `lato` a sinistra (+), sul terreno + dz."""
    a = math.radians(yaw)
    return Vector(P(m, x0 + math.sin(a) * d + math.cos(a) * lato, y0 - math.cos(a) * d + math.sin(a) * lato, dz))

def rel(base, yaw, off):
    """base + off girato di yaw (off nel riferimento del cavallo: +X = sua sinistra, -Y = davanti, Z su)."""
    return Vector(base) + Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Vector(off)

def chiave_striscia(st, f, tempo, influenza=1.0):
    st.strip_time = tempo; st.keyframe_insert('strip_time', frame=f)
    st.influence = influenza; st.keyframe_insert('influence', frame=f)

def animale_vivo(file, nome, pos, yaw, scala=1.0):
    """Un animale del gioco con lo scheletro vivo (le clip si guidano con pose.traccia): (radice, armatura, clip)."""
    sc = bpy.context.scene; prima = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=AN.A + 'animali/%s.glb' % file)
    nuovi = [o for o in bpy.data.objects if o not in prima]
    for o in list(nuovi):
        if o.name.startswith('Icosphere'): bpy.data.objects.remove(o); nuovi.remove(o)
    arm = next(o for o in nuovi if o.type == 'ARMATURE'); ad = arm.animation_data; az = {}
    for t in list(ad.nla_tracks):
        if t.strips: az.setdefault(t.name.split('|')[-1], t.strips[0].action)
        ad.nla_tracks.remove(t)
    ad.action = None
    radice = bpy.data.objects.new(nome, None); sc.collection.objects.link(radice)
    for o in nuovi:
        if o.parent is None: o.parent = radice
    radice.rotation_mode = 'XYZ'; AN.metti(radice, pos, yaw, scala)
    return radice, arm, az

S = {}
def shot(nome):
    def d(f): S[nome] = f; return f
    return d

# ---------------------------------------------------------------------------------------------------------------- il profilo
def profilo(m, n):
    """Il cavallo al galoppo in avanti (rig vivo) e la camera attaccata a lui, di profilo da 6,5 m: sta fermo nel quadro."""
    radice, rig, az = pose.eroe_vivo('eroe')
    gal = pose.traccia(rig, az['Gallop'])
    yaw0 = A2.yaw_su(m, 0, 0)
    pos = lambda f: avanti(m, 0, 0, yaw0, V * (f - 1))
    for f in range(1, n + 1):
        chiave_striscia(gal, f, T0 + (f - 1))
        radice.location = pos(f); radice.rotation_euler = (0, 0, math.radians(yaw0))
        radice.keyframe_insert('location', frame=f); radice.keyframe_insert('rotation_euler', frame=f)
    cam = AN.camera(rel(pos(1), yaw0, (6.5, 0, 1.0)), rel(pos(1), yaw0, (0, 0, 1.3)), 50, fstop=3.5, fuoco=rel(pos(1), yaw0, (0, 0, 1.0)))
    for f in range(1, n + 1):
        SH.chiave_camera(cam, f, rel(pos(f), yaw0, (6.5, 0, 1.0)), rel(pos(f), yaw0, (0, 0, 1.3)), fuoco=6.5)
    return radice, rig, yaw0, pos

# ---------------------------------------------------------------------------------------------------------------- S15
@shot('S15')
def s15():
    n = DUR['S15']; m = giorno(3, n, sole_rel=120)
    profilo(m, n)

# ---------------------------------------------------------------------------------------------------------------- S16
@shot('S16')
def s16():
    n = DUR['S16']; m = giorno(5, n, sole_rel=70)
    profilo(m, n)
    # il lama sulla cresta: guarda avanti (come il cavallo) e gira la testa verso di lui mentre passa, senza un'espressione
    zc = m.quota(-34, 3.0) + 1.5
    radice, arm, az = animale_vivo('lama', 'lama_cresta', (-34, 3.0, zc), 0.0, 1.2)
    st = pose.traccia(arm, az['Idle'])
    for f in range(1, n + 1): chiave_striscia(st, f, 40.0 + 0.5 * (f - 1))
    bpy.context.view_layer.update()
    ad = arm.animation_data; ad.action_blend_type = 'COMBINE'
    su = arm.matrix_world.to_3x3().inverted() @ Vector((0, 0, 1))
    for nome_osso, quota in (('Neck', 0.45), ('Head', 0.55)):
        pb = arm.pose.bones[nome_osso]; asse = arm.data.bones[nome_osso].matrix_local.to_3x3().inverted() @ su
        for f in range(1, n + 1):
            a = math.radians(62 * quota * sm((f - 1) / (n - 1)))
            pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(asse, a); pb.keyframe_insert('rotation_quaternion', frame=f)

# ---------------------------------------------------------------------------------------------------------------- S18
@shot('S18')
def s18():
    n = DUR['S18']; m = giorno(9, n, motore='CYCLES', sole_rel=90)
    radice, rig, yaw0, pos = profilo(m, n)
    # l'aquila attraversa il cielo in alto, in senso contrario al cavallo, battendo le ali
    er, arm, az = animale_vivo('aquila', 'aquila', (0, 0, 0), 0.0, 0.32)
    st = pose.traccia(arm, az['Flying'])
    for f in range(1, n + 1):
        chiave_striscia(st, f, 1.0 + ((f - 1) * 1.4) % 28.0)
        er.location = P(m, -25.0, -4.0 + 0.47 * (f - 1), 9.0); er.rotation_euler = (0, 0, math.radians(-90))
        er.keyframe_insert('location', frame=f); er.keyframe_insert('rotation_euler', frame=f)

# ---------------------------------------------------------------------------------------------------------------- S19
@shot('S19')
def s19():
    n = DUR['S19']; m = giorno(10, n, sole_rel=90, esposizione=1.3)
    profilo(m, n)
    # le lanterne tremolano (ognuna ha il suo materiale: «lanterna», «lanterna.001»…)
    random.seed(19)
    for mt in bpy.data.materials:
        if mt.name.startswith('lanterna') and mt.node_tree:
            b = next((x for x in mt.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
            if not b: continue
            ph = random.uniform(0, 6.28)
            for f in range(1, n + 1):
                b.inputs['Emission Strength'].default_value = 30.0 * (0.8 + 0.2 * math.sin(f * 1.3 + ph) + 0.08 * math.sin(f * 3.1 + 2 * ph))
                b.inputs['Emission Strength'].keyframe_insert('default_value', frame=f)

# ---------------------------------------------------------------------------------------------------------------- S20
BATTITI = [(5, 0.25), (13, 0.5), (21, 0.8), (28, 1.0)]          # (fotogramma, forza) dei tonfi: ogni passo del Boss è più forte

def tremore(f):
    """Quanto trema la terra al fotogramma f: la somma dei tonfi, ognuno che si smorza."""
    return sum(s * math.exp(-(f - b) * 0.42) * math.cos((f - b) * 2.4) for b, s in BATTITI if f >= b)

def materiale_pozza(battiti, vita=12, ritardi=(0, 3), raggio=2.15, larghezza=0.03):
    """L'acqua della pozza (24 nov, rifatta): superficie speculare (IOR 1,33, rugosità 0,03) che riflette cielo, luna, luci e cavallo, con le
    INCRESPATURE vere (un pacchetto d'onde per ogni anello, in rilievo → la normale cambia e il riflesso ondeggia) e un alone sottile degli anelli.
    Il tempo è un driver sul fotogramma; gli anelli sono calcolati sulle coordinate d'oggetto, così la riga resta sottile."""
    m = bpy.data.materials.new('pozza'); m.use_nodes = True; nt = m.node_tree
    bs = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'); N = FU._Nodi(nt)
    bs.inputs['Base Color'].default_value = (0.010, 0.016, 0.026, 1); bs.inputs['Roughness'].default_value = 0.03
    try: bs.inputs['IOR'].default_value = 1.33; bs.inputs['Specular IOR Level'].default_value = 0.8
    except KeyError: pass
    bs.inputs['Emission Color'].default_value = (0.6, 0.7, 1.0, 1)
    tv = nt.nodes.new('ShaderNodeValue'); fc = tv.outputs[0].driver_add('default_value'); fc.driver.type = 'SCRIPTED'; fc.driver.expression = 'frame'
    t = tv.outputs[0]
    P = nt.nodes.new('ShaderNodeTexCoord').outputs['Object']
    d = N.v('LENGTH', N.v('MULTIPLY', P, (1.0, 1.0, 0.0)), esci='Value')
    somma = 0.0; alt = 0.0
    for b0, forza in battiti:
        for rit in ritardi:
            f0 = b0 + rit
            u = N.m('DIVIDE', N.m('SUBTRACT', t, f0), float(vita), clamp=True)
            r = N.m('ADD', 0.12, N.m('MULTIPLY', N.m('SUBTRACT', 1.0, N.m('POWER', N.m('SUBTRACT', 1.0, u), 2.0)), raggio))
            dd = N.m('SUBTRACT', d, r)
            riga = N.m('SUBTRACT', 1.0, N.m('DIVIDE', N.m('ABSOLUTE', dd), larghezza), clamp=True)
            vivo = N.m('MULTIPLY', N.m('POWER', N.m('SUBTRACT', 1.0, u), 1.4), 6.0 * (0.5 + 0.5 * forza))
            nato = N.m('GREATER_THAN', t, f0 - 0.5)
            somma = N.m('ADD', somma, N.m('MULTIPLY', N.m('MULTIPLY', riga, vivo), nato))
            # il pacchetto d'onde: tre creste dietro il fronte, che si spengono col tempo e con la distanza dal fronte
            inv = N.m('POWER', 2.718, N.m('MULTIPLY', N.m('POWER', N.m('DIVIDE', dd, 0.22), 2.0), -1.0))
            onda = N.m('MULTIPLY', N.m('SINE', N.m('MULTIPLY', dd, 34.0)), inv)
            alt = N.m('ADD', alt, N.m('MULTIPLY', N.m('MULTIPLY', onda, nato), N.m('MULTIPLY', N.m('POWER', N.m('SUBTRACT', 1.0, u), 1.2), 0.5 + 0.5 * forza)))
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.9; bump.inputs['Distance'].default_value = 0.05
    nt.links.new(alt, bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], bs.inputs['Normal'])
    nt.links.new(N.m('MULTIPLY', somma, 0.35), bs.inputs['Emission Strength'])
    return m

def strada_bagnata(m, s0=-30.0, s1=30.0, lat=4.2, seme=11.0):
    """Chiazze d'acqua sulla pista (S20): un nastro appena sopra la strada, trasparente dove è asciutto e speculare dove è bagnato (rumore a macchie):
    le luci della città ci si specchiano in strisce verticali."""
    bm = bmesh.new(); prev = None
    for i in range(61):
        s = s0 + (s1 - s0) * i / 60
        a = m.tr.pos(s, -lat); c = m.tr.pos(s, lat)
        r = (bm.verts.new((a.x, a.y, m.quota(a.x, a.y) + 0.012)), bm.verts.new((c.x, c.y, m.quota(c.x, c.y) + 0.012)))
        if prev: bm.faces.new((prev[0], prev[1], r[1], r[0]))
        prev = r
    me = bpy.data.meshes.new('bagnato'); bm.to_mesh(me); bm.free()
    mt = bpy.data.materials.new('bagnato'); mt.use_nodes = True; nt = mt.node_tree; nt.nodes.clear(); N = FU._Nodi(nt)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    bs.inputs['Base Color'].default_value = (0.012, 0.014, 0.02, 1); bs.inputs['Roughness'].default_value = 0.10
    try: bs.inputs['Specular IOR Level'].default_value = 0.8
    except KeyError: pass
    P = nt.nodes.new('ShaderNodeTexCoord').outputs['Object']
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.35; nz.inputs['Detail'].default_value = 5.0; nz.inputs['Roughness'].default_value = 0.6
    nz.noise_dimensions = '3D'; off = nt.nodes.new('ShaderNodeVectorMath'); off.operation = 'ADD'; off.inputs[1].default_value = (seme, seme * 0.6, 0.0)
    nt.links.new(P, off.inputs[0]); nt.links.new(off.outputs['Vector'], nz.inputs['Vector'])
    nt.links.new(N.liscia(nz.outputs['Fac'], 0.46, 0.58), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(bs.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    o = AN.collega(bpy.data.objects.new('bagnato', me), mt); o.visible_shadow = False
    return o

@shot('S20')
def s20():
    n = DUR['S20']; m = giorno(11, n, motore='CYCLES', luna_rel=163, luna_el=17, pezzi=False)
    # le luci della città, in alto sull'orizzonte (la camera guarda indietro lungo la pista: la città sta dietro di lui, grandi perché lontane)
    random.seed(7); luce_c = kit.mat_semplice('luce_citta', (0, 0, 0, 1), nebbia=False, emissione=AN.hexc('#ff9a48'), forza=26.0)
    for i in range(80):
        p = m.tr.pos(-190 + random.uniform(-45, 45), random.uniform(-130, 130))
        AN.sfera((p.x, p.y, m.quota(p.x, p.y) + random.uniform(0.8, 6.0)), random.uniform(0.6, 1.3), luce_c, 'luce_citta_%d' % i)
    strada_bagnata(m)
    c = m.punto(3, -1.5)
    bm = __import__('bmesh').new(); __import__('bmesh').ops.create_circle(bm, cap_ends=True, radius=2.3, segments=64)
    me = bpy.data.meshes.new('pozza'); bm.to_mesh(me); bm.free()
    acqua = AN.collega(bpy.data.objects.new('pozza', me), materiale_pozza(BATTITI)); acqua.location = (c.x, c.y, c.z + 0.05)
    # i sassi della strada saltano a ogni tonfo (più forte il tonfo, più alto il salto), ognuno col suo ritardo
    random.seed(20); sasso = kit.mat_semplice('sasso', (0.10, 0.095, 0.09, 1), nebbia=False)
    for i in range(18):
        x, y = random.uniform(-1.0, 3.0), random.uniform(-4.0, -0.8)
        if math.hypot(x - 2.4, y + 5.4) < 1.8: continue                      # non davanti all'obiettivo
        o = AN.sfera((x, y, m.quota(x, y) + 0.02), random.uniform(0.025, 0.07), sasso, 'sasso%d' % i); o.scale.z = 0.7
        z0 = m.quota(x, y) + 0.02; rit = random.randrange(0, 2); alt = random.uniform(0.6, 1.4)
        for f in range(1, n + 1):
            z = 0.0
            for b, s in BATTITI:
                u = (f - (b + rit)) / 7.0
                if 0 <= u <= 1: z = max(z, 0.28 * s * alt * 4 * u * (1 - u))
            o.location = (x, y, z0 + z); o.keyframe_insert('location', frame=f)
    # le luci della città sussultano a ogni tonfo
    mc = next((x for x in bpy.data.materials if x.name.startswith('luce_citta')), None)
    if mc:
        b = next(x for x in mc.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
        for f in range(1, n + 1):
            b.inputs['Emission Strength'].default_value = 26.0 * max(0.35, 1.0 - 0.6 * abs(tremore(f)))
            b.inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
    # il cavallo cammina verso di noi, rallenta, si ferma e gira la testa (come un orecchio che sente): il passo senza pattinare
    radice, rig, az = pose.eroe_vivo('eroe')
    wk = pose.traccia(rig, az['Walk']); idl = pose.traccia(rig, az['Idle']); sg = pose.traccia(rig, az['Sguardo_D'], 'COMBINE')
    yaw0 = A2.yaw_su(m, 0, 0); d = 0.0; t = 20.0
    for f in range(1, n + 1):
        vel = curva([(1, 1.0), (14, 1.0), (23, 0.0), (n, 0.0)], f)
        if f > 1: d += V_PASSO * vel; t += vel
        chiave_striscia(wk, f, t, 1.0 - sm((f - 21) / 6.0))
        chiave_striscia(idl, f, 10.0 + 0.4 * f, sm((f - 21) / 6.0))
        chiave_striscia(sg, f, 9.0, curva([(1, 0.0), (22, 0.0), (29, 0.6), (n, 0.6)], f))
        radice.location = avanti(m, 0, 0, yaw0, d); radice.rotation_euler = (0, 0, math.radians(yaw0))
        radice.keyframe_insert('location', frame=f); radice.keyframe_insert('rotation_euler', frame=f)
    # la camera: bassa, vicina alla pozza, entra piano e trema coi tonfi (forza e verso diversi a ogni tonfo)
    cam = AN.camera(P(m, 2.4, -5.4, 0.35), P(m, 0.5, -0.6, 1.0), 38)
    random.seed(21)
    for f in range(1, n + 1):
        k = (f - 1) / (n - 1); tr = tremore(f)
        pos = Vector(P(m, 2.4 - 0.2 * k, -5.4 + 0.6 * k, 0.35)) + Vector((0.5 * tr * random.uniform(-1, 1), 0.3 * tr * random.uniform(-1, 1), 0.10 * tr))
        SH.chiave_camera(cam, f, pos, Vector(P(m, 0.5, -0.6, 1.0 + 0.03 * tr)))

# ---------------------------------------------------------------------------------------------------------------- montaggio
def ff(*a): subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *a], check=True)

def monta():
    v = lambda s: os.path.join(BASE, s, '%s-%s.mp4' % (s, MODO))
    ing = sum((['-i', v(s)] for s in TUTTI), [])
    filt = ''.join('[%d:v]setpts=PTS-STARTPTS[v%d];' % (i, i) for i in range(len(TUTTI))) + ''.join('[v%d]' % i for i in range(len(TUTTI))) + 'concat=n=%d:v=1:a=0[o]' % len(TUTTI)
    ff(*ing, '-filter_complex', filt, '-map', '[o]', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', '24', '-movflags', '+faststart', os.path.join(BASE, 'atto3.mp4'))
    print('MONTATO', os.path.join(BASE, 'atto3.mp4'))

if __name__ == '__main__':
    if LISTA == ['monta']: monta()
    else:
        for nome in LISTA:
            S[nome]()
            if MODO == 'finale': SH.salva(nome)
            SH.gira(os.path.join(BASE, nome), nome, MODO)
        if set(LISTA) == set(TUTTI): monta()
