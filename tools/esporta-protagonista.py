# Cavallo di cartone (protagonista) → GLB per il gioco.
#   blender -b assets/models/protagonista-cartone.blend --python tools/esporta-protagonista.py -- assets/models/protagonista-cartone.glb
#
# Il .blend ha il rig Rigify con le clip Gallop / Walk / Idle (rigenerabili con
# tools/anima-protagonista.py). Qui le cuociamo su uno scheletro "da gioco" senza
# controlli e con i nomi del rig Quaternius (Back, Torso…Torso3, Neck1, Neck2, Head,
# Tail1…Tail4): così HorseActor.shapeTurn() piega schiena, collo, testa e coda in
# curva senza toccare il codice. Niente B-bone: il glTF non le porta.
import bpy, sys

out = sys.argv[-1]
CLIPS = ("Gallop", "Walk", "Idle")
rig = bpy.data.objects["CavalloCartone_rig"]
horse = bpy.data.objects["CavalloCartone"]
scn = bpy.context.scene

MAP = {"DEF-spine": "Back", "DEF-spine.001": "Torso", "DEF-spine.002": "Torso2", "DEF-spine.003": "Torso3",
       "DEF-neck": "Neck1", "DEF-neck.001": "Neck2", "DEF-head": "Head"}
for i, s in enumerate(("", ".001", ".002", ".003")):
    MAP[f"DEF-tail{s}"] = f"Tail{i+1}"
for pre, P in (("front", "Front"), ("rear", "Rear")):
    for lato in ("L", "R"):
        for src, dst, suf in (("thigh", "Thigh", ""), ("thigh", "Thigh2", ".001"), ("shin", "Shin", ""),
                              ("shin", "Shin2", ".001"), ("foot", "Foot", ""), ("toe", "Toe", "")):
            MAP[f"DEF-{src}_{pre}.{lato}{suf}"] = f"{P}{dst}_{lato}"
PARENT = {"Back": "Root", "Torso": "Back", "Torso2": "Torso", "Torso3": "Torso2", "Neck1": "Torso3",
          "Neck2": "Neck1", "Head": "Neck2", "HeadTop": "Head", "Tail1": "Back", "Tail2": "Tail1",
          "Tail3": "Tail2", "Tail4": "Tail3"}
for P, anca in (("Front", "Torso3"), ("Rear", "Back")):       # gambe davanti sul petto, dietro sul bacino
    for lato in ("L", "R"):
        catena = [f"{P}{n}_{lato}" for n in ("Thigh", "Thigh2", "Shin", "Shin2", "Foot", "Toe")]
        PARENT[catena[0]] = anca
        for figlio, padre in zip(catena[1:], catena):
            PARENT[figlio] = padre
SRC = {v: k for k, v in MAP.items()}

# --- scheletro da gioco, in posa di riposo
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
arm = bpy.data.armatures.new("Cavallo_game")
game = bpy.data.objects.new("Cavallo_game", arm)
scn.collection.objects.link(game)
bpy.context.view_layer.objects.active = game
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
root = eb.new("Root"); root.head = (0, 0, 0); root.tail = (0, -0.25, 0)
for src, dst in MAP.items():
    b = rig.data.bones[src]
    e = eb.new(dst); e.head = b.head_local; e.tail = b.tail_local
    e.align_roll(b.matrix_local.to_3x3().col[2])
top = eb.new("HeadTop")              # arriva alla punta delle orecchie: il gioco scala dall'ingombro delle ossa
top.head = (0, -0.62, 1.70); top.tail = (0, -0.63, 1.83)
for b in eb:
    if b.name in PARENT:
        b.parent = eb[PARENT[b.name]]; b.use_connect = False
    b.use_deform = b.name not in ("Root", "HeadTop")
bpy.ops.object.mode_set(mode='OBJECT')
REST = {b.name: b.matrix_local.copy() for b in arm.bones}

# --- cottura a mano: posa locale = (riposo relativo al padre)⁻¹ · (posa relativa al padre).
# Non serve il contesto di nla.bake, quindi gira anche con blender -b.
game.animation_data_create()
cotte = {}
for clip in CLIPS:
    act = bpy.data.actions[clip]
    rig.animation_data.action = act
    f0, f1 = (int(x) for x in act.frame_range)
    game.animation_data.action = None
    for f in range(f0, f1 + 1):
        scn.frame_set(f)
        posa = {dst: rig.pose.bones[src].matrix.copy() for dst, src in SRC.items()}
        posa["Root"] = REST["Root"]
        for pb in game.pose.bones:
            n = pb.name
            if n not in SRC:
                continue
            p = PARENT[n]
            pb.matrix_basis = (REST[p].inverted() @ REST[n]).inverted() @ (posa[p].inverted() @ posa[n])
            pb.keyframe_insert("location", frame=f)
            pb.keyframe_insert("rotation_quaternion", frame=f)
            pb.keyframe_insert("scale", frame=f)
    ga = game.animation_data.action
    ga.name = f"game_{clip}"
    cotte[clip] = (ga, f0)
game.animation_data.action = None
for pb in game.pose.bones:
    pb.matrix_basis.identity()

# una traccia NLA per clip → un'animazione glTF per traccia, col nome della traccia
for clip, (ga, f0) in cotte.items():
    tr = game.animation_data.nla_tracks.new(); tr.name = clip
    st = tr.strips.new(clip, f0, ga)
    if hasattr(st, "action_slot") and len(getattr(ga, "slots", [])):
        st.action_slot = ga.slots[0]

# --- mesh: copia del cavallo legata allo scheletro da gioco, gruppi rinominati
gm = horse.copy(); gm.data = horse.data.copy(); gm.name = "CavalloCartone_game"
scn.collection.objects.link(gm)
gm.parent = game; gm.matrix_parent_inverse.identity(); gm.matrix_world.identity()
for m in list(gm.modifiers):
    gm.modifiers.remove(m)
gm.modifiers.new("Armature", 'ARMATURE').object = game
for vg in list(gm.vertex_groups):
    if vg.name in MAP: vg.name = MAP[vg.name]
    else: gm.vertex_groups.remove(vg)

for o in bpy.data.objects:
    o.select_set(o in (game, gm))
bpy.ops.export_scene.gltf(
    filepath=out, export_format='GLB', use_selection=True,
    export_animations=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True,
    export_anim_slide_to_zero=True, export_optimize_animation_size=False,
    export_def_bones=False, export_leaf_bone=False, export_rest_position_armature=True,
    export_skins=True, export_morph=False, export_apply=False, export_yup=True,
    export_image_format='JPEG', export_jpeg_quality=85)
print('OK', out, {c: int(a.frame_range[1] - a.frame_range[0]) for c, (a, _) in cotte.items()})
