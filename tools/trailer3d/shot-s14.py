# SHOT S14 · LA BIRRA GRANDE — il primo shot ANIMATO del trailer (storyboard v2): 2 s, 48 fotogrammi a 24 fps, 9:16.
# Camera bassa e ferma a bordo strada (Burkhan Khaldun, mattina). La scaletta della gag, sui quattro battiti:
#    1–19  la birra sui pattini sfreccia a zigzag da destra a sinistra davanti al cavallo che arriva al galoppo
#    8–19  il cavallo la segue con la testa… e torna avanti, come niente fosse
#   21–23  DOPPIA PRESA: la testa scatta di nuovo verso la birra
#   24–36  la sbandata: le gambe si bloccano, il corpo si piega indietro e ruota, i piedi nudi scivolano e alzano polvere
#   35–48  si gira lento e GUARDA IN MACCHINA. Fermo.
# Tutto è a chiavi in una scena vera (rig vivo con l'NLA: tempo del galoppo e influenza dello sguardo chiavati; birra a chiavi),
# salvata in trailer/blender/shot/S14.blend per aprirla e ritoccarla in Blender.
#
# uso:  blender -b --python tools/trailer3d/shot-s14.py -- <cartella uscita> [prova|finale]
#   prova   EEVEE 540×960, 16 campioni, senza mosso: per giudicare i tempi (~30 s)
#   finale  EEVEE 1080×1920, 64 campioni, mosso, e salva il .blend
import bpy, sys, os, math, random, subprocess
QUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, QUI)
import animatic as AN
import animatic2 as A2
import pose
from mathutils import Vector

N = 48
ARGV = sys.argv[sys.argv.index('--') + 1:]
USCITA = os.path.abspath(ARGV[0]); MODO = ARGV[1] if len(ARGV) > 1 else 'prova'
BLEND = os.path.abspath(os.path.join(QUI, '..', '..', 'trailer', 'blender', 'shot', 'S14.blend'))

def sm(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def curva(chiavi, f):
    """chiavi = [(fotogramma, valore)]: fra una chiave e l'altra si va in smoothstep (attacchi e arrivi morbidi)."""
    if f <= chiavi[0][0]: return chiavi[0][1]
    for (f0, v0), (f1, v1) in zip(chiavi, chiavi[1:]):
        if f <= f1: return v0 + (v1 - v0) * sm((f - f0) / (f1 - f0))
    return chiavi[-1][1]

# ---------------------------------------------------------------------------------------------------------------- la gag
V = 0.17                                    # m a fotogramma (~4 m/s): la velocità a cui il galoppo del rig non pattina
def velocita(f):                            # galoppo pieno fino al 24, poi frena fino a fermarsi al 36 (i piedi scivolano)
    return V if f <= 24 else V * max(0.0, (36 - f) / 12)
def tempo_galoppo(f):                       # fotogramma della clip Gallop: normale fino al 24, rallenta e si blocca al 32
    # si blocca al fotogramma 30,8 della clip: tutti e due i piedi DAVANTI a terra (anteriore sx in appoggio da 27,4 a 31,2,
    # dx da 30,2 a 34) e quelli dietro in aria: puntato sulle gambe davanti, è una frenata
    if f <= 24: return 3.0 + (f - 1)
    passi = [1.0, 0.95, 0.85, 0.75, 0.6, 0.4, 0.25, 0.0]
    return 26.0 + sum(passi[:min(len(passi), int(f) - 24)])
SGUARDO = [(1, 0.0), (10, 0.0), (15, 0.55), (17, 0.55), (19, 0.0), (21, 0.0), (23, 1.0), (35, 1.0), (41, 0.15), (48, 0.15)]
PIEGA = [(1, 0.0), (24, 0.0), (30, -9.0), (36, -9.0), (44, -4.0), (48, -4.0)]      # gradi attorno a X: − = muso su, piegato indietro
GIRO = [(1, 0.0), (22, 0.0), (32, -25.0), (48, -25.0)]                              # gradi: − = verso la sua destra (la birra)
Y_ARRIVO = 5.5                              # dove sta il cavallo al primo fotogramma (lungo la strada, verso -Y)

# la birra attraversa il quadro da destra a sinistra a 3 m dalla camera (lo stesso piano dove poi il cavallo si ferma), di
# traverso alla visuale, a 0,2 m per fotogramma: si vede per ~10 fotogrammi, il tempo di capire che è un bicchiere sui pattini
CAM, MIRA = (-1.4, -2.3, 0.5), (0.25, 1.3, 1.0)
INCROCIO, DIR_B, F_INCROCIO = Vector((-0.3, 0.4)), Vector((-0.93, 0.36)), 10
def birra_xy(f):
    perp = Vector((-DIR_B.y, DIR_B.x))
    return INCROCIO + DIR_B * 0.2 * (f - F_INCROCIO) + perp * 0.25 * math.sin(2 * math.pi * f / 12)

def costruisci():
    finale = MODO == 'finale'
    AN.W, AN.H = (1080, 1920) if finale else (540, 960)
    A2.MOTORE = 'EEVEE'
    m = A2.mondo(2, sole_rel=150)                                   # (mondo() riparte dalle impostazioni di fabbrica)
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N; sc.render.fps = 24
    try: sc.eevee.taa_render_samples = 64 if finale else 16
    except Exception: pass
    sc.render.use_motion_blur = finale
    try: sc.render.motion_blur_shutter = 0.5
    except Exception: pass

    # --- il cavallo: rig vivo, galoppo con il tempo chiavato, sguardo sommato con l'influenza chiavata
    radice, rig, az = pose.eroe_vivo('eroe')
    gal = pose.traccia(rig, az['Gallop'], 'REPLACE')
    sgu = pose.traccia(rig, az['Sguardo_D'], 'COMBINE')
    yaw0 = A2.yaw_su(m, 0.2, 2.0)
    y = Y_ARRIVO; piedi = []
    for f in range(1, N + 1):
        if f > 1: y -= velocita(f)
        gal.strip_time = tempo_galoppo(f); gal.keyframe_insert('strip_time', frame=f)
        gal.influence = 1.0; gal.keyframe_insert('influence', frame=f)
        sgu.strip_time = 9.0; sgu.keyframe_insert('strip_time', frame=f)
        sgu.influence = curva(SGUARDO, f); sgu.keyframe_insert('influence', frame=f)
        x = 0.2; z = m.quota(x, y)
        # piegato indietro attorno ai piedi DAVANTI (a 0,42 m dal centro), non attorno al centro: se no i piedi davanti si staccano
        radice.location = (x, y, z - 0.42 * math.sin(math.radians(max(0.0, -curva(PIEGA, f)))))
        radice.rotation_euler = (math.radians(curva(PIEGA, f)), 0, math.radians(yaw0 + curva(GIRO, f)))
        radice.keyframe_insert('location', frame=f); radice.keyframe_insert('rotation_euler', frame=f)
        piedi.append((f, Vector((x, y, z)), yaw0 + curva(GIRO, f)))

    # --- la birra: radice a chiavi lungo lo zigzag, pattini e bicchiere a chiavi con la spinta del gioco
    rb, pezzi, base = pose.birra_crea()
    rb.scale = (2.4,) * 3; rb.rotation_mode = 'XYZ'
    for f in range(1, N + 1):
        p = birra_xy(f); v = birra_xy(f + 0.5) - birra_xy(f - 0.5)
        acc = birra_xy(f + 1) - 2 * birra_xy(f) + birra_xy(f - 1)
        yaw = math.atan2(v.y, v.x)
        destra = Vector((math.sin(yaw), -math.cos(yaw)))                 # la destra della birra (−Y del modello) nel mondo
        piega = max(-15.0, min(15.0, 150 * acc.dot(destra)))           # si piega dentro la curva
        rb.location = (p.x, p.y, m.quota(p.x, p.y)); rb.rotation_euler = (0, 0, yaw)
        rb.keyframe_insert('location', frame=f); rb.keyframe_insert('rotation_euler', frame=f)
        pose.birra_posa(pezzi, base, fase=f / 12.0, forza=1.7, piega=piega, chiave=f)

    # --- la polvere della sbandata: sbuffi che nascono sotto i piedi mentre scivolano, crescono e salgono
    random.seed(14); mat = AN.materiale_polvere((0.66, 0.53, 0.38, 1), 0.16)
    for f, p, yw in piedi:
        if not 25 <= f <= 37: continue
        c, s_ = math.cos(math.radians(yw)), math.sin(math.radians(yw))
        for dy in (-0.42, 0.38):
            for dx in (-0.09, 0.09):
                if random.random() < 0.45: continue
                q = p + Vector((c * dx - s_ * dy, s_ * dx + c * dy, 0.04))
                o = AN.sfera(q, 1.0, mat, 'sbuffo'); r = random.uniform(0.08, 0.16)
                o.scale = (0.001,) * 3; o.keyframe_insert('scale', frame=f - 1)
                o.scale = (r,) * 3; o.keyframe_insert('scale', frame=f + 3)
                o.location = q; o.keyframe_insert('location', frame=f + 3)
                o.scale = (r * 1.8,) * 3; o.keyframe_insert('scale', frame=min(N, f + 16))
                o.location = q + Vector((random.uniform(-0.25, 0.25), random.uniform(-0.1, 0.35), random.uniform(0.15, 0.35)))
                o.keyframe_insert('location', frame=min(N, f + 16))

    # --- camera bassa e ferma a bordo strada
    cam = A2.C(m, CAM, MIRA, 32)

    # --- lo sguardo in macchina va MISURATO, non stimato: nell'ultimo fotogramma si guarda dove punta il muso e si gira il corpo
    # (dal 36 in poi, insieme alla testa) finché punta l'obiettivo. Due passate: girando, il muso si sposta un poco.
    corr = 0.0
    for _ in range(3):
        sc.frame_set(N); bpy.context.view_layer.update()
        pb = rig.pose.bones['DEF-head']; Wm = rig.matrix_world
        nu, mu = Wm @ pb.head, Wm @ pb.tail
        d = mu - nu; c = cam.location - mu
        ang = math.degrees(math.atan2(d.x * c.y - d.y * c.x, d.x * c.x + d.y * c.y))
        corr += ang
        for f in range(36, N + 1):
            radice.rotation_euler = (math.radians(curva(PIEGA, f)), 0, math.radians(yaw0 + curva(GIRO, f) + corr * sm((f - 35) / 6.0)))
            radice.keyframe_insert('rotation_euler', frame=f)
    print('SGUARDO IN MACCHINA: correzione del corpo %.1f°, resto %.1f°' % (corr, ang))
    return m

def gira():
    sc = bpy.context.scene
    os.makedirs(USCITA, exist_ok=True)
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = os.path.join(USCITA, 'f_####')
    bpy.ops.render.render(animation=True)
    mp4 = os.path.join(USCITA, 'S14-%s.mp4' % MODO)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(USCITA, 'f_%04d.png'),
                    '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4], check=True)
    print('VIDEO', mp4)

if __name__ == '__main__':
    costruisci()
    if MODO == 'finale':
        os.makedirs(os.path.dirname(BLEND), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND, relative_remap=True)
        print('SALVATO', BLEND)
    gira()
