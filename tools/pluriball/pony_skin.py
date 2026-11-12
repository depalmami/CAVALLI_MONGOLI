# IL PROTAGONISTA AVVOLTO NEL PLURIBALL — il pony generato (assets/models/pluriball/pony.blend, un mesh statico in posa di
# galoppo) viene legato allo SCHELETRO DA GIOCO del protagonista, così nel gioco galoppa con le sue stesse clip.
#
#  1. Il pony è stato generato dalla posa che il .blend del protagonista aveva salvata: lo si scala e lo si sovrappone a quel
#     protagonista in posa.
#  2. GAMBE: quelle del pony non coincidono con quelle del protagonista (stanno qualche centimetro fuori, e quando si muovono
#     una finisce sull'osso dell'altra: si sfaldano). Quindi del pony si tiene SOLO il busto avvolto (scatola, gonna di
#     pluriball, testa, criniera, coda, braccia) e le gambe sono quelle vere del protagonista, già pesate: le monta il gioco
#     (3d/pluriball.js) estraendo dal protagonista i triangoli delle gambe. Pesi del busto: dai vertici più vicini del
#     protagonista in posa (i suoi pesi dipinti).
#  3. Lo scheletro da gioco viene messo in QUELLA posa e la posa diventa il suo riposo («Apply Pose as Rest»): il pony si lega
#     così com'è, senza deformarlo. Le clip del gioco, che si muovono rispetto al riposo vero, lo animano lo stesso: nel
#     gioco la mesh usa lo scheletro del protagonista ma le matrici di legatura del pony (vedi 3d/pluriball.js).
#  4. Si esporta scheletro + pony legato, SENZA clip. Con un png: anteprima del galoppo (protagonista a sinistra, pony a destra).
#
# uso: blender -b assets/models/protagonista-cartone.blend --python tools/pluriball/pony_skin.py -- <pony.blend> <uscita .glb> [prefisso png anteprima]
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector, kdtree
a = sys.argv[sys.argv.index('--') + 1:]
pony_blend, uscita = os.path.abspath(a[0]), os.path.abspath(a[1]); prefisso = os.path.abspath(a[2]) if len(a) > 2 else None
rig = bpy.data.objects['CavalloCartone_rig']; horse = bpy.data.objects['CavalloCartone']; scn = bpy.context.scene
qui = os.path.dirname(os.path.abspath(__file__))
Z_TAGLIO = 0.45                                                     # sotto questa quota (m) del pony non si tiene niente: là ci sono le gambe
QUOTA_GONNA = 0.62                                                  # fra Z_TAGLIO e questa si tengono solo i vertici che non sono di gamba (la gonna di pluriball)

# ── 1. la posa salvata del protagonista: pesi dipinti e matrici, PRIMA che l'esportazione resetti lo scheletro ──
dg = bpy.context.evaluated_depsgraph_get()
ev = horse.evaluated_get(dg); me_ev = ev.to_mesh()
posato = np.array([(horse.matrix_world @ v.co)[:] for v in me_ev.vertices]); ev.to_mesh_clear()
codice_esp = open(os.path.join(qui, '..', 'esporta-protagonista.py')).read()
exec(codice_esp[codice_esp.index('MAP = {'):codice_esp.index('SRC = ')])          # MAP: nome Rigify → nome da gioco (e PARENT)
vg = {g.index: g.name for g in horse.vertex_groups}
pesi_orig = [{vg[g.group]: g.weight for g in v.groups if vg[g.group] in MAP} for v in horse.data.vertices]
POSA = {dst: (rig.matrix_world @ rig.pose.bones[src_].matrix).copy() for src_, dst in MAP.items()}   # armatura-spazio-mondo, la posa salvata
print('RISULTATO protagonista in posa: z %.3f..%.3f  y %.3f..%.3f  x %.3f..%.3f' % (posato[:, 2].min(), posato[:, 2].max(), posato[:, 1].min(), posato[:, 1].max(), posato[:, 0].min(), posato[:, 0].max()))

# ── lo scheletro da gioco, in riposo (la prima parte dello script di esportazione del protagonista) ──
codice = codice_esp[:codice_esp.index('# --- mesh: copia del cavallo')].replace('out = sys.argv[-1]', 'out = None')
exec(codice)                                                        # crea `game` (l'armatura da gioco), REST, le clip cotte

# ── il pony: lo prendo dal suo .blend, lo giro (davanti = -Y), lo scalo e lo sovrappongo al protagonista in posa ──
with bpy.data.libraries.load(pony_blend) as (da, a_):
    a_.objects = [n for n in da.objects if n == 'Pony']
pony = a_.objects[0]; scn.collection.objects.link(pony)
me = pony.data
me.transform(Matrix.Rotation(math.radians(-90), 4, 'Z'))
v = np.array([w.co[:] for w in me.vertices])
s = (posato[:, 2].max() - posato[:, 2].min()) / (v[:, 2].max() - v[:, 2].min())
cp = (v.min(axis=0) + v.max(axis=0)) / 2; ch = (posato.min(axis=0) + posato.max(axis=0)) / 2
t = Vector((ch[0] - cp[0] * s, ch[1] - cp[1] * s, posato[:, 2].min() - v[:, 2].min() * s))
me.transform(Matrix.Translation(t) @ Matrix.Diagonal((s, s, s, 1)))
v = np.array([w.co[:] for w in me.vertices]); n = len(v)
print('RISULTATO pony sovrapposto: scala %.3f, z %.3f..%.3f y %.3f..%.3f' % (s, v[:, 2].min(), v[:, 2].max(), v[:, 1].min(), v[:, 1].max()))
nomi = list(MAP.keys()); idx = {k: i for i, k in enumerate(nomi)}; gioco_di = {k: MAP[k] for k in nomi}

# ── 2a. pesi dai 5 vertici più vicini del protagonista in posa (busto, testa, criniera, coda, braccia) ──
kd = kdtree.KDTree(len(posato))
for i, p in enumerate(posato): kd.insert(Vector(p), i)
kd.balance()
Wv = np.zeros((n, len(MAP)))
for i, p in enumerate(v):
    for (_, j, d) in kd.find_n(Vector(p), 5):
        w = 1.0 / (d + 1e-3)
        for nome, peso in pesi_orig[j].items(): Wv[i, idx[nome]] += peso * w
Wv /= np.maximum(Wv.sum(axis=1, keepdims=True), 1e-9)

# ── 2b. cosa tengo del pony: il busto. Via le gambe (sotto Z_TAGLIO, e dove i pesi dicono «gamba») ──
gambe = {k for k in nomi if MAP[k].startswith(('Front', 'Rear'))}
gamba = np.array([sum(Wv[i, idx[k]] for k in gambe) for i in range(n)])          # quanto ogni vertice dipende dalle ossa delle gambe
W = Wv
# ── anteprima: il galoppo, protagonista a sinistra e pony (miscela lineare di ossa, come nel gioco) a destra ──
def anteprima(pref, frames):
    """Il galoppo: a sinistra il protagonista, a destra il pony senza gambe (miscela lineare di ossa, come nel gioco) + le gambe vere."""
    sys.path.insert(0, os.path.join(qui, '..', 'boss')); import viste
    rig.animation_data_create(); rig.animation_data.action = bpy.data.actions['Gallop']
    for o in bpy.data.objects:
        if o not in (rig, horse, pony): o.hide_render = True; o.hide_viewport = True
    horse.hide_render = True; pony.hide_render = True
    viste.scena_base(res=(900, 700), fondo=(0.93, 0.93, 0.92))
    Dinv = {k: POSA[MAP[k]].inverted() for k in nomi}
    dom = [max(p_, key=p_.get) if p_ else None for p_ in pesi_orig]                  # osso dominante di ogni vertice del protagonista
    gamba_h = np.array([d_ is not None and MAP[d_].startswith(('Front', 'Rear')) for d_ in dom])
    for f in frames:
        scn.frame_set(f); bpy.context.view_layer.update()
        d_ = bpy.context.evaluated_depsgraph_get(); eh = horse.evaluated_get(d_)
        mh = bpy.data.meshes.new_from_object(eh); mh.transform(horse.matrix_world)
        mg = mh.copy()
        bg = bmesh.new(); bg.from_mesh(mg); bg.faces.ensure_lookup_table()
        bmesh.ops.delete(bg, geom=[fc for fc in bg.faces if not all(gamba_h[vv.index] for vv in fc.verts)], context='FACES')
        bmesh.ops.delete(bg, geom=[vv for vv in bg.verts if not vv.link_faces], context='VERTS'); bg.to_mesh(mg); bg.free()
        mh.transform(Matrix.Translation((0, -1.1, 0))); mg.transform(Matrix.Translation((0, 1.1, 0)))
        Dm = np.array([np.array(rig.matrix_world @ rig.pose.bones[k].matrix @ Dinv[k]) for k in nomi])
        M = np.einsum('vb,bij->vij', W, Dm); vp = np.einsum('vij,vj->vi', M, np.concatenate([v, np.ones((n, 1))], axis=1))[:, :3]
        mp = me.copy(); mp.vertices.foreach_set('co', (vp + np.array([0, 1.1, 0])).ravel()); mp.update()
        oh = bpy.data.objects.new('h', mh); op = bpy.data.objects.new('p', mp); og = bpy.data.objects.new('g', mg)
        for o in (oh, op, og): scn.collection.objects.link(o)
        viste.foglio('%s-%02d.png' % (pref, f), [oh, op, og], viste=((-1, 0, 0.1),), colonne=1, margine=0.62)
        for o in (oh, op, og): bpy.data.objects.remove(o)

import bmesh
orig = me.attributes.new('orig', 'INT', 'POINT'); orig.data.foreach_set('value', np.arange(n, dtype=np.int32))   # l'indice di partenza viaggia col vertice
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
def tieni(f):
    zs = [vv.co.z for vv in f.verts]; zc = sum(zs) / len(zs); g = sum(gamba[vv.index] for vv in f.verts) / len(f.verts)
    return zc >= QUOTA_GONNA or (zc >= Z_TAGLIO and g < 0.5)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not tieni(f)], context='FACES')
bmesh.ops.delete(bm, geom=[vv for vv in bm.verts if not vv.link_faces], context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
quali = np.empty(len(me.vertices), dtype=np.int32); me.attributes['orig'].data.foreach_get('value', quali)   # dopo il taglio: chi è chi
me.attributes.remove(me.attributes['orig'])
W = W[quali]; v = v[quali]; n = len(quali)
# il busto avvolto non segue MAI le gambe (le gambe sono quelle vere): via i pesi delle ossa delle gambe, il resto si rinormalizza
for k in gambe: W[:, idx[k]] = 0
vuoti = W.sum(axis=1) == 0; W[vuoti, idx['DEF-spine']] = 1
W /= W.sum(axis=1, keepdims=True)
for i in range(n):                                                  # al massimo 4 influenze (glTF), normalizzate
    r = W[i]
    if np.count_nonzero(r) > 4: r[np.argsort(r)[:-4]] = 0
    W[i] = r / r.sum()
print('RISULTATO pony senza gambe: %d vertici' % n)

# ── 3. lo scheletro da gioco nella posa salvata, e quella posa diventa il suo riposo ──
game.animation_data_clear()
POSA['Root'] = REST['Root']
POSA['HeadTop'] = POSA['Head'] @ (REST['Head'].inverted() @ REST['HeadTop'])     # la punta delle orecchie segue la testa
for pb in game.pose.bones:
    nm = pb.name
    if nm not in PARENT: continue
    pb.matrix_basis = (REST[PARENT[nm]].inverted() @ REST[nm]).inverted() @ (POSA[PARENT[nm]].inverted() @ POSA[nm])
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = game
bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT'); bpy.ops.pose.armature_apply(selected=False); bpy.ops.object.mode_set(mode='OBJECT')
me.update()

# ── gruppi di vertici coi nomi da gioco, legatura allo scheletro da gioco, esportazione ──
for k in nomi:
    gr = pony.vertex_groups.new(name=MAP[k])
    for i in np.nonzero(W[:, idx[k]] > 1e-4)[0]: gr.add([int(i)], float(W[i, idx[k]]), 'REPLACE')
pony.name = 'Pony_game'
pony.parent = game; pony.matrix_parent_inverse.identity(); pony.matrix_world.identity()
pony.modifiers.new('Armature', 'ARMATURE').object = game
for o in bpy.data.objects: o.select_set(o in (game, pony))
bpy.ops.export_scene.gltf(filepath=uscita, export_format='GLB', use_selection=True, export_animations=False, export_def_bones=False, export_leaf_bone=False,
                          export_rest_position_armature=True, export_skins=True, export_morph=False, export_apply=False, export_yup=True,
                          export_image_format='JPEG', export_jpeg_quality=85)
print('RISULTATO glb %.2f MB' % (os.path.getsize(uscita) / 1e6))

# ── controlli (dopo l'esportazione, perché nascondono gli oggetti) ──
if prefisso:
    anteprima(prefisso, (1, 6, 11, 16))
