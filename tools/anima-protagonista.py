# Cavallo di cartone (protagonista): genera le clip Gallop / Walk / Idle sui controlli Rigify.
#   blender -b assets/models/protagonista-cartone.blend --python tools/anima-protagonista.py
#   (poi tools/esporta-protagonista.py per il GLB)
#
# Clip sul posto (niente root motion) e in loop: l'ultimo fotogramma è uguale al primo.
# Gallop contiene 2 falcate e Walk 4: così una clip copre circa la distanza che il gioco
# dà a un ciclo (GALLOP_STRIDE = 4 HORSE_HEIGHT, WALK_STRIDE = 1.8) e i piedi quasi non
# pattinano quando il gioco ricava il timeScale dalla velocità al suolo.
# Galoppo a 4 tempi: posteriore sx, posteriore dx, anteriore sx, anteriore dx, poi
# sospensione. Le due persone nella scatola fanno ognuna un "saltello", sfasate.
# I parametri da ritoccare sono in GAITS (falcata, appoggio, sollevamento, beccheggio…).
import bpy, math
from mathutils import Matrix, Vector

CLIPS = globals().get("CLIPS", ("Gallop", "Walk", "Idle"))
rig = bpy.data.objects["CavalloCartone_rig"]
horse = bpy.data.objects["CavalloCartone"]
pbs = rig.pose.bones
B = rig.data.bones
LEGS = ("front.L", "front.R", "rear.L", "rear.R")
PIVOT = Vector((0.0, 0.01, 0.96))          # box centre (torso pivot)
BALL_Z = 0.016                              # ball of the foot on the ground
FOOT_FLAT = math.radians(35)                # ankle->ball slope when the foot is flat
TOE_FLAT = math.radians(10)

def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def Rx(a): return Matrix.Rotation(a, 4, 'X')
def Ry(a): return Matrix.Rotation(a, 4, 'Y')
def Rz(a): return Matrix.Rotation(a, 4, 'Z')
def about(p, R): return Matrix.Translation(p) @ R @ Matrix.Translation(-p)
def ang_yz(v): return math.atan2(v.z, v.y)
def wrap(a): return (a + math.pi) % (2 * math.pi) - math.pi

# --- per-leg rest data
L = {}
for k in LEGS:
    p, s = k.split(".")
    th, sh, ft, to = (B[f"ORG-{n}_{p}.{s}"] for n in ("thigh", "shin", "foot", "toe"))
    L[k] = dict(
        hip=th.head_local.copy(),
        reach=(th.length + sh.length) * 0.985,
        legl=th.length + sh.length,
        f_rest=ft.tail_local - ft.head_local, flen=ft.length,
        t_rest=to.tail_local - to.head_local, tlen=to.length,
        foot_ctl=f"foot_{p}_ik.{s}", toe_ctl=f"toe_{p}_ik.{s}",
        side=1 if s == "L" else -1,
    )

CTRLS = ["torso", "hips", "chest", "neck", "head", "tail_master"] + \
        [L[k]["foot_ctl"] for k in LEGS] + [L[k]["toe_ctl"] for k in LEGS]
REST = {n: B[n].matrix_local.copy() for n in CTRLS}

def foot_dir(k, phi):     # flat foot pointing -Y, rotated heel-up by phi
    f0 = Vector((0, -math.cos(FOOT_FLAT), -math.sin(FOOT_FLAT))) * L[k]["flen"]
    return (Rx(phi).to_3x3() @ f0)
def toe_dir(k, psi):
    t0 = Vector((0, -math.cos(TOE_FLAT), -math.sin(TOE_FLAT))) * L[k]["tlen"]
    return (Rx(psi).to_3x3() @ t0)

def leg_cycle(k, u, P):
    """u: phase since touchdown (0..1). Returns ankle (x,y,z), foot pitch phi, toe pitch psi."""
    D, scale = P["duty"], L[k]["legl"] / 0.73
    E = P["exc"] * scale
    hip = L[k]["hip"]
    yc = hip.y + P["ycen"]
    x = L[k]["side"] * P["foot_x"]
    def ankle_at(ball_y, phi):
        a = Vector((x, ball_y, BALL_Z)) - foot_dir(k, phi)
        return a
    ph_land, ph_off = math.radians(P["phi_land"]), math.radians(P["phi_off"])
    if u < D:                                   # stance: ball slides back at ground speed
        s = u / D
        ball_y = yc - E / 2 + E * s
        phi = lerp(ph_land, 0.0, smooth(0.0, 0.25, s)) + (ph_off) * smooth(0.45, 1.0, s)
        return ankle_at(ball_y, phi), phi, 0.0
    s = (u - D) / (1 - D)                       # swing
    a_off = ankle_at(yc + E / 2, ph_off)
    a_td = ankle_at(yc - E / 2, ph_land)
    y = lerp(a_off.y, a_td.y, smooth(0.0, 1.0, s)) + P["kick"] * math.sin(math.pi * min(1.0, s / 0.5)) * (1 - s)
    z = lerp(a_off.z, a_td.z, s) + P["lift"] * math.sin(math.pi * s) ** 0.9
    peak = math.radians(P["phi_swing"])
    phi = lerp(ph_off, peak, smooth(0.0, 0.3, s)) if s < 0.3 else lerp(peak, ph_land, smooth(0.3, 1.0, s))
    bump = smooth(0.0, 0.15, s) * (1 - smooth(0.85, 1.0, s))
    psi = (phi - math.radians(10)) * bump
    return Vector((x, y, z)), phi, psi

GAITS = {
    # name: cycles per clip, frames per cycle, footfall phases, gait params, body params
    "Gallop": dict(cycles=2, fpc=20,
                   on={"rear.L": 0.00, "rear.R": 0.12, "front.L": 0.32, "front.R": 0.46},
                   leg=dict(duty=0.19, exc=0.60, ycen=-0.03, foot_x=0.085, phi_land=-4, phi_off=42,
                            phi_swing=62, kick=0.10, lift=0.27),
                   body=dict(base=-0.035, bob=0.045, rear_low=0.17, front_low=0.50, roll=3.0,
                             neck=7.0, head=5.0, tail_lift=22.0, tail_amp=16.0, tail_sway=8.0)),
    "Walk":   dict(cycles=4, fpc=24,
                   on={"rear.L": 0.00, "front.L": 0.25, "rear.R": 0.50, "front.R": 0.75},
                   leg=dict(duty=0.62, exc=0.50, ycen=-0.02, foot_x=0.085, phi_land=-14, phi_off=32,
                            phi_swing=30, kick=0.03, lift=0.11),
                   body=dict(base=-0.01, bob=0.012, rear_low=None, front_low=None, roll=2.0,
                             neck=3.0, head=2.0, tail_lift=6.0, tail_amp=5.0, tail_sway=6.0)),
}

def body_pose(t, gait, G):
    b = G["body"]
    if gait == "Gallop":
        h_r = -b["bob"] * math.cos(2 * math.pi * (t - b["rear_low"]))
        h_f = -b["bob"] * math.cos(2 * math.pi * (t - b["front_low"]))
    else:   # walk: each person dips twice per cycle (once per own footfall)
        on = G["on"]
        h_r = -b["bob"] * math.cos(4 * math.pi * (t - on["rear.L"] - 0.12))
        h_f = -b["bob"] * math.cos(4 * math.pi * (t - on["front.L"] - 0.12))
    z = b["base"] + (h_r + h_f) / 2
    pitch = math.atan2(h_f - h_r, 0.58)
    roll_r = math.radians(b["roll"]) * math.sin(2 * math.pi * (t - 0.10))
    roll_f = math.radians(b["roll"]) * math.sin(2 * math.pi * (t - 0.42))
    neck = math.radians(b["neck"]) * math.cos(2 * math.pi * (t - 0.52))
    head = math.radians(b["head"]) * math.cos(2 * math.pi * (t - 0.62))
    tail_x = math.radians(b["tail_lift"] + b["tail_amp"] * math.cos(2 * math.pi * (t - 0.30)))
    tail_z = math.radians(b["tail_sway"]) * math.sin(2 * math.pi * (t - 0.15))
    return dict(z=z, pitch=pitch, roll_r=roll_r, roll_f=roll_f, neck=neck, head=head,
                tail_x=tail_x, tail_z=tail_z)

def reset():
    for n in CTRLS:
        pb = pbs[n]; pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)

def upd(): bpy.context.view_layer.update()

def apply_body(bp):
    pbs["torso"].matrix = Matrix.Translation((0, 0, bp["z"])) @ about(PIVOT, Rx(-bp["pitch"])) @ REST["torso"]
    upd()
    for n, r in (("hips", bp["roll_r"]), ("chest", bp["roll_f"])):
        m = pbs[n].matrix.copy(); pbs[n].matrix = about(m.translation, Ry(r)) @ m
    upd()
    for n, R in (("neck", Rx(bp["neck"])), ("head", Rx(bp["head"]))):
        m = pbs[n].matrix.copy(); pbs[n].matrix = about(m.translation, R) @ m
        upd()
    m = pbs["tail_master"].matrix.copy()
    pbs["tail_master"].matrix = about(m.translation, Rz(bp["tail_z"]) @ Rx(bp["tail_x"])) @ m
    upd()

def apply_feet(targets):
    clamp = 0.0
    for k, (ank, phi, psi) in targets.items():
        hip = pbs[f"ORG-thigh_{k.split('.')[0]}.{k.split('.')[1]}"].head
        d = ank - hip
        if d.length > L[k]["reach"]:
            clamp = max(clamp, d.length - L[k]["reach"])
            ank = hip + d.normalized() * L[k]["reach"]
        delta = wrap(ang_yz(foot_dir(k, phi)) - ang_yz(L[k]["f_rest"]))
        R = REST[L[k]["foot_ctl"]].to_3x3().to_4x4()
        pbs[L[k]["foot_ctl"]].matrix = Matrix.Translation(ank) @ Rx(delta) @ R
    upd()
    for k, (ank, phi, psi) in targets.items():
        pb = pbs[L[k]["toe_ctl"]]
        dt = wrap(ang_yz(toe_dir(k, psi)) - ang_yz(L[k]["t_rest"]))
        R = REST[L[k]["toe_ctl"]].to_3x3().to_4x4()
        pb.matrix = Matrix.Translation(pb.matrix.translation) @ Rx(dt) @ R
    return clamp

def key_all(f):
    for n in CTRLS:
        pbs[n].keyframe_insert("location", frame=f)
        pbs[n].keyframe_insert("rotation_quaternion", frame=f)

def new_action(name):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    rig.animation_data_create()
    rig.animation_data.action = None

def finish_action(name, frames):
    act = rig.animation_data.action
    act.name = name; act.use_fake_user = True
    act.frame_range = (1, frames + 1)
    act.use_frame_range = True
    act.use_cyclic = True
    return act

horse.hide_viewport = True     # niente deformazione della mesh mentre si mettono le chiavi (molto più veloce)
report = {}
for clip in CLIPS:
    new_action(clip)
    if clip in GAITS:
        G = GAITS[clip]; n = G["cycles"] * G["fpc"]; maxc = 0.0
        for i in range(n + 1):
            t = (i / G["fpc"]) % 1.0
            reset(); upd()
            apply_body(body_pose(t, clip, G))
            targets = {k: leg_cycle(k, (t - G["on"][k]) % 1.0, G["leg"]) for k in LEGS}
            maxc = max(maxc, apply_feet(targets))
            key_all(i + 1)
        report[clip] = dict(frames=n, max_clamp=round(maxc, 3))
    else:   # Idle: 3 s, two breaths, slow look around, weight shift, lazy tail
        n = 72; maxc = 0.0
        stance = {"front.L": -0.05, "front.R": 0.05, "rear.L": 0.03, "rear.R": -0.03}
        for i in range(n + 1):
            t = i / n
            reset(); upd()
            bp = dict(z=-0.012 + 0.006 * math.sin(4 * math.pi * t), pitch=0.004 * math.sin(4 * math.pi * t + 1),
                      roll_r=math.radians(1.2) * math.sin(2 * math.pi * t),
                      roll_f=math.radians(1.2) * math.sin(2 * math.pi * t + 0.8),
                      neck=math.radians(-3 + 3 * math.sin(2 * math.pi * t)),
                      head=math.radians(4 * math.sin(2 * math.pi * t + 1.3)),
                      tail_x=math.radians(-4 + 3 * math.sin(4 * math.pi * t)),
                      tail_z=math.radians(9) * math.sin(2 * math.pi * t + 0.5))
            apply_body(bp)
            m = pbs["head"].matrix.copy()          # slow look to the sides
            pbs["head"].matrix = about(m.translation, Rz(math.radians(10) * math.sin(2 * math.pi * t))) @ m
            upd()
            targets = {}
            for k in LEGS:
                hip = L[k]["hip"]
                ball_y = hip.y + stance[k] - 0.02
                ank = Vector((L[k]["side"] * 0.085, ball_y, BALL_Z)) - foot_dir(k, 0.0)
                targets[k] = (ank, 0.0, 0.0)
            maxc = max(maxc, apply_feet(targets))
            key_all(i + 1)
        report[clip] = dict(frames=n, max_clamp=round(maxc, 3))
    finish_action(clip, report[clip]["frames"])

horse.hide_viewport = False
for act in bpy.data.actions:
    for fc in act.fcurves if hasattr(act, "fcurves") else []:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
rig.animation_data.action = bpy.data.actions["Gallop"]
bpy.context.scene.frame_start = 1; bpy.context.scene.frame_end = report.get("Gallop", {"frames": 40})["frames"] + 1
bpy.context.scene.frame_set(1)
print(report)
print("actions:", [a.name for a in bpy.data.actions])
if bpy.app.background:
    bpy.ops.wm.save_mainfile()
    print("OK salvato", bpy.data.filepath)
