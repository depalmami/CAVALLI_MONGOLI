# IL CAVALLO AVVOLTO NEL PLURIBALL per gli shot animati (S13a, S13b).
#   avvolgi()  il pony del gioco (assets/models/pluriball/pony.blend: un mesh statico nella posa salvata del protagonista, che è
#              Gallop al fotogramma 1) legato al RIG VIVO del trailer, così galoppa, gira la testa e muove il braccio con le
#              stesse clip. Sovrapposizione, pesi (dai 5 vertici più vicini del protagonista in posa) e taglio delle gambe sono
#              quelli di tools/pluriball/pony_skin.py; in più il pony viene riportato nel RIPOSO del rig (skinning inverso) e
#              legato con un modificatore Armatura. Le gambe restano quelle vere del protagonista: sul suo corpo una Maschera
#              lascia vedere solo le gambe.
#   bolle()    le bolle VERE (Geometry Nodes, dopo l'Armatura) su una zona del pony, che scoppiano A CATENA da un punto d'urto:
#              ogni bolla scoppia quando il fronte (raggio chiavabile) arriva alla sua distanza, misurata nel riposo, così le
#              bolle non tremolano col galoppo. Prima di scoppiare si gonfia, poi resta un dischetto sgonfio e uno sbuffo bianco.
import bpy, bmesh, math, os
import numpy as np
from mathutils import Matrix, Vector, kdtree
import animatic as AN

PONY = os.path.join(AN.A, 'models', 'pluriball', 'pony.blend')
Z_TAGLIO, QUOTA_GONNA = 0.45, 0.62                  # come pony_skin.py (m, nello spazio del rig)
def _gamba(nome): return any(k in nome for k in ('thigh', 'shin', 'foot', 'toe'))

def avvolgi(rig, azioni, f_posa=1):
    """Ritorna il pony (figlio del rig, nascosto finché non si chiama mostra). Da chiamare con la radice del cavallo
    nell'origine e PRIMA di mettere le clip nell'NLA."""
    sc = bpy.context.scene
    horse = next(o for o in rig.children if o.type == 'MESH')
    ad = rig.animation_data
    # --- 1. il protagonista nella posa del pony (Gallop al fotogramma 1), nello spazio del rig
    act = azioni['Gallop']; ad.action = act
    try: ad.action_slot = act.slots[0]
    except Exception: pass
    sc.frame_set(f_posa); bpy.context.view_layer.update()
    Ri = rig.matrix_world.inverted()
    dg = bpy.context.evaluated_depsgraph_get(); ev = horse.evaluated_get(dg); me_ev = ev.to_mesh()
    Mh = Ri @ horse.matrix_world
    posato = np.array([(Mh @ v.co)[:] for v in me_ev.vertices]); ev.to_mesh_clear()
    ossa = [b.name for b in rig.data.bones if b.use_deform]
    gr = {g.index: g.name for g in horse.vertex_groups if g.name in ossa}
    nomi = sorted(set(gr.values())); idx = {k: i for i, k in enumerate(nomi)}
    Wh = np.zeros((len(horse.data.vertices), len(nomi)))
    for v in horse.data.vertices:
        for g in v.groups:
            if g.group in gr: Wh[v.index, idx[gr[g.group]]] = g.weight
    Dm = np.array([np.array(rig.pose.bones[k].matrix @ rig.data.bones[k].matrix_local.inverted()) for k in nomi])   # posa ← riposo
    ad.action = None

    # --- 2. il pony sovrapposto (come pony_skin.py: davanti = -Y, scala sull'altezza, centrato, appoggiato)
    with bpy.data.libraries.load(PONY, link=False) as (da, a_):
        a_.objects = ['Pony']
    pony = a_.objects[0]; sc.collection.objects.link(pony); pony.matrix_world = Matrix.Identity(4)
    me = pony.data
    me.transform(Matrix.Rotation(math.radians(-90), 4, 'Z'))
    v = np.array([w.co[:] for w in me.vertices])
    s = (posato[:, 2].max() - posato[:, 2].min()) / (v[:, 2].max() - v[:, 2].min())
    cp = (v.min(axis=0) + v.max(axis=0)) / 2; ch = (posato.min(axis=0) + posato.max(axis=0)) / 2
    me.transform(Matrix.Translation((ch[0] - cp[0] * s, ch[1] - cp[1] * s, posato[:, 2].min() - v[:, 2].min() * s)) @ Matrix.Diagonal((s, s, s, 1)))
    v = np.array([w.co[:] for w in me.vertices]); n = len(v)
    kd = kdtree.KDTree(len(posato))
    for i, p in enumerate(posato): kd.insert(Vector(p), i)
    kd.balance()
    W = np.zeros((n, len(nomi))); dist = np.zeros(n)
    for i, p in enumerate(v):
        vic = kd.find_n(Vector(p), 5); dist[i] = vic[0][2]
        for (_, j, d) in vic: W[i] += Wh[j] / (d + 1e-3)
    W /= np.maximum(W.sum(axis=1, keepdims=True), 1e-9)
    print('AVVOLTO: pony scala %.3f, distanza dal protagonista mediana %.3f m, 95%% %.3f m' % (s, np.median(dist), np.percentile(dist, 95)))
    # --- 3. via le gambe del pony (le gambe sono quelle vere)
    gambe = [idx[k] for k in nomi if _gamba(k)]
    gamba = W[:, gambe].sum(axis=1)
    orig = me.attributes.new('orig', 'INT', 'POINT'); orig.data.foreach_set('value', np.arange(n, dtype=np.int32))
    bm = bmesh.new(); bm.from_mesh(me)
    def tieni(f):
        zc = sum(x.co.z for x in f.verts) / len(f.verts); g = sum(gamba[x.index] for x in f.verts) / len(f.verts)
        return zc >= QUOTA_GONNA or (zc >= Z_TAGLIO and g < 0.5)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not tieni(f)], context='FACES')
    bmesh.ops.delete(bm, geom=[x for x in bm.verts if not x.link_faces], context='VERTS')
    bm.to_mesh(me); bm.free(); me.update()
    quali = np.empty(len(me.vertices), dtype=np.int32); me.attributes['orig'].data.foreach_get('value', quali)
    me.attributes.remove(me.attributes['orig'])
    W = W[quali]; v = v[quali]; n = len(quali)
    W[:, gambe] = 0
    vuoti = W.sum(axis=1) == 0; W[vuoti, idx['DEF-spine']] = 1
    W /= W.sum(axis=1, keepdims=True)
    # --- 4. skinning inverso: il pony torna nel riposo del rig, così l'Armatura lo rimette esattamente dov'era in posa
    M = np.einsum('vb,bij->vij', W, Dm)
    vh = np.concatenate([v, np.ones((n, 1))], axis=1)
    riposo = np.einsum('vij,vj->vi', np.linalg.inv(M), vh)[:, :3]
    me.vertices.foreach_set('co', riposo.ravel()); me.update()
    a = me.attributes.new('riposo', 'FLOAT_VECTOR', 'POINT'); a.data.foreach_set('vector', riposo.astype(np.float32).ravel())
    for k in nomi:
        g = pony.vertex_groups.new(name=k)
        for i in np.nonzero(W[:, idx[k]] > 1e-4)[0]: g.add([int(i)], float(W[i, idx[k]]), 'REPLACE')
    pony.parent = rig; pony.matrix_parent_inverse = Matrix.Identity(4); pony.matrix_basis = Matrix.Identity(4)
    arm = pony.modifiers.new('Armatura', 'ARMATURE'); arm.object = rig; arm.use_vertex_groups = True
    pony.name = 'avvolto'
    # --- 5. sul protagonista una Maschera che lascia solo le gambe (spenta finché non è avvolto)
    gl = horse.vertex_groups.new(name='gambe_vere')
    legs = [i for i in range(len(horse.data.vertices)) if Wh[i, gambe].sum() > 0.5]
    gl.add(legs, 1.0, 'REPLACE')
    mk = horse.modifiers.new('solo_gambe', 'MASK'); mk.vertex_group = 'gambe_vere'
    with bpy.context.temp_override(object=horse): bpy.ops.object.modifier_move_to_index(modifier=mk.name, index=0)
    mk.show_render = mk.show_viewport = False
    pony.hide_render = pony.hide_viewport = True
    print('AVVOLTO: %d vertici del pony (busto), %d vertici di gamba veri' % (n, len(legs)))
    return pony

def mostra(pony, rig, f):
    """Dal fotogramma f in poi: il pony si vede e del protagonista restano solo le gambe (prima: il protagonista normale)."""
    horse = next(o for o in rig.children if o.type == 'MESH' and 'solo_gambe' in o.modifiers)     # (anche il pony è figlio del rig)
    for val, fr in ((False, f - 1), (True, f)):
        pony.hide_render = pony.hide_viewport = not val
        pony.keyframe_insert('hide_render', frame=fr); pony.keyframe_insert('hide_viewport', frame=fr)
        mk = horse.modifiers['solo_gambe']; mk.show_render = mk.show_viewport = val
        horse.keyframe_insert('modifiers["solo_gambe"].show_render', frame=fr)
        horse.keyframe_insert('modifiers["solo_gambe"].show_viewport', frame=fr)

def punto_riposo(pony, vicino, lato=(-1, 0, 0)):
    """Il vertice del pony (riposo) più vicino a `vicino` fra quelli che guardano verso `lato`: (indice, posizione di riposo)."""
    me = pony.data; me.update()
    rip = np.empty(len(me.vertices) * 3, dtype=np.float32); me.attributes['riposo'].data.foreach_get('vector', rip); rip = rip.reshape(-1, 3)
    nor = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('normal', nor); nor = nor.reshape(-1, 3)
    ok = nor @ np.array(lato, dtype=np.float32) > 0.5
    d = np.linalg.norm(rip - np.array(vicino, dtype=np.float32), axis=1); d[~ok] = 1e9
    i = int(np.argmin(d)); return i, Vector(rip[i].tolist())

def mondo_vertice(pony, i):
    """Dove sta ADESSO (fotogramma corrente, deformato) il vertice i del pony, nel mondo."""
    dg = bpy.context.evaluated_depsgraph_get(); ev = pony.evaluated_get(dg); m = ev.to_mesh()
    p = pony.matrix_world @ m.vertices[i].co; ev.to_mesh_clear(); return p

def _mat_bolla():
    m = bpy.data.materials.new('bolla'); m.use_nodes = True; nt = m.node_tree
    b = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (0.90, 0.95, 1.0, 1); b.inputs['Roughness'].default_value = 0.06
    for nome, val in (('Alpha', 0.45), ('Coat Weight', 1.0), ('Coat Roughness', 0.03)):
        if nome in b.inputs: b.inputs[nome].default_value = val
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    return m

def _mat_sbuffo():
    m = AN.materiale_polvere((0.95, 0.97, 1.0, 1), 0.55); m.name = 'sbuffo_bolla'; return m

def sgonfia(pony, impatto, banda=0.025):
    """Nel materiale del pony: dove il fronte è passato la plastica è sgonfia (più scura e opaca), con un bordo irregolare.
    Ritorna il nodo Valore del fronte (da chiavare insieme alle bolle)."""
    fronte = None
    for mt in pony.data.materials:
        nt = mt.node_tree; N = nt.nodes; L = nt.links.new
        b = next((x for x in N if x.type == 'BSDF_PRINCIPLED'), None)
        if not b: continue
        if fronte is None or fronte.id_data != nt:
            fronte = N.new('ShaderNodeValue'); fronte.label = 'Fronte'; fronte.outputs[0].default_value = 0.0
        at = N.new('ShaderNodeAttribute'); at.attribute_type = 'GEOMETRY'; at.attribute_name = 'riposo'
        cx = N.new('ShaderNodeCombineXYZ'); cx.inputs[0].default_value, cx.inputs[1].default_value, cx.inputs[2].default_value = impatto[:]
        d = N.new('ShaderNodeVectorMath'); d.operation = 'DISTANCE'; L(at.outputs['Vector'], d.inputs[0]); L(cx.outputs[0], d.inputs[1])
        nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 22.0; L(at.outputs['Vector'], nz.inputs['Vector'])
        sp = N.new('ShaderNodeMath'); sp.operation = 'MULTIPLY_ADD'; L(nz.outputs['Fac'], sp.inputs[0]); sp.inputs[1].default_value = 0.05; L(d.outputs['Value'], sp.inputs[2])
        dif = N.new('ShaderNodeMath'); dif.operation = 'SUBTRACT'; L(fronte.outputs[0], dif.inputs[0]); L(sp.outputs[0], dif.inputs[1])
        fac = N.new('ShaderNodeMapRange'); L(dif.outputs[0], fac.inputs['Value']); fac.inputs['From Min'].default_value = 0.0
        fac.inputs['From Max'].default_value = banda; fac.inputs['To Min'].default_value = 0.0; fac.inputs['To Max'].default_value = 1.0
        mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; L(fac.outputs[0], mix.inputs['Factor'])
        col = b.inputs['Base Color']
        if col.is_linked:
            src = col.links[0].from_socket; L(src, mix.inputs[6])
        else: mix.inputs[6].default_value = col.default_value
        mix.inputs[7].default_value = (0.40, 0.43, 0.50, 1)
        L(mix.outputs[2], col)
        if not b.inputs['Roughness'].is_linked:
            r0 = b.inputs['Roughness'].default_value
            rm = N.new('ShaderNodeMapRange'); L(fac.outputs[0], rm.inputs['Value']); rm.inputs['To Min'].default_value = r0; rm.inputs['To Max'].default_value = 0.75
            L(rm.outputs[0], b.inputs['Roughness'])
    return fronte

def bolle(pony, impatto, zona=0.38, lato=(-1, 0, 0), passo=0.03, raggio=0.015, banda=0.03):
    """Bolle vere sul pony attorno a `impatto` (riposo), su chi guarda verso `lato`, fino a `zona` m (sfumando), e la plastica
    che si sgonfia dietro il fronte. Ritorna chiave(f, raggio_del_fronte): raggio 0 = tutte intere."""
    me = pony.data
    rip = np.empty(len(me.vertices) * 3, dtype=np.float32); me.attributes['riposo'].data.foreach_get('vector', rip); rip = rip.reshape(-1, 3)
    nor = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('normal', nor); nor = nor.reshape(-1, 3)
    d = np.linalg.norm(rip - np.array(impatto[:], dtype=np.float32), axis=1)
    peso = np.clip((zona - d) / (zona * 0.35), 0, 1) * np.clip((nor @ np.array(lato, dtype=np.float32) - 0.25) / 0.35, 0, 1)
    a = me.attributes.new('zona_bolle', 'FLOAT', 'POINT'); a.data.foreach_set('value', peso.astype(np.float32))
    print('BOLLE: %d vertici nella zona' % int((peso > 0).sum()))

    ng = bpy.data.node_groups.new('Bolle', 'GeometryNodeTree')
    io = ng.interface
    io.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    s_r = io.new_socket('Fronte', in_out='INPUT', socket_type='NodeSocketFloat')
    s_i = io.new_socket('Impatto', in_out='INPUT', socket_type='NodeSocketVector')
    io.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L = ng.links.new
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    def nodo(tipo, **kw):
        x = N.new(tipo)
        for k, val in kw.items(): setattr(x, k, val)
        return x
    def mat(op, a=None, b=None, c=None):
        x = nodo('ShaderNodeMath', operation=op)
        for i, val in enumerate((a, b, c)):
            if val is None: continue
            if isinstance(val, (int, float)): x.inputs[i].default_value = val
            else: L(val, x.inputs[i])
        return x.outputs[0]
    zona_a = nodo('GeometryNodeInputNamedAttribute', data_type='FLOAT'); zona_a.inputs['Name'].default_value = 'zona_bolle'
    dist = nodo('GeometryNodeDistributePointsOnFaces', distribute_method='POISSON')
    L(gi.outputs[0], dist.inputs['Mesh'])
    dist.inputs['Distance Min'].default_value = passo
    dist.inputs['Density Max'].default_value = 1.6 / (passo * passo)
    L(zona_a.outputs[0], dist.inputs['Density Factor'])
    dist.inputs['Seed'].default_value = 13
    # distanza (nel riposo) dal punto d'urto, con un po' di disordine: il fronte non è un cerchio perfetto
    rip_a = nodo('GeometryNodeInputNamedAttribute', data_type='FLOAT_VECTOR'); rip_a.inputs['Name'].default_value = 'riposo'
    vd = nodo('ShaderNodeVectorMath', operation='DISTANCE'); L(rip_a.outputs[0], vd.inputs[0]); L(gi.outputs[s_i.identifier], vd.inputs[1])
    rnd = nodo('FunctionNodeRandomValue', data_type='FLOAT')
    fmin = next(s for s in rnd.inputs if s.name == 'Min' and s.type == 'VALUE'); fmax = next(s for s in rnd.inputs if s.name == 'Max' and s.type == 'VALUE')
    fmin.default_value = 0.0; fmax.default_value = 0.035
    rnd_out = next(s for s in rnd.outputs if s.type == 'VALUE')
    dd = mat('ADD', vd.outputs['Value'], rnd_out)
    u = mat('DIVIDE', mat('SUBTRACT', gi.outputs[s_r.identifier], dd), banda)          # <0 intera, 0..1 si gonfia, >1 scoppiata
    c = mat('MINIMUM', mat('MAXIMUM', u, 0.0), 1.0)
    gonfia = mat('ADD', mat('MULTIPLY', mat('SINE', mat('MULTIPLY', c, math.pi)), 0.4), 1.0)
    scoppiata = mat('GREATER_THAN', u, 0.999)
    sxy = mat('MULTIPLY', gonfia, mat('ADD', mat('MULTIPLY', scoppiata, 0.2), 1.0))
    sz = mat('ADD', gonfia, mat('MULTIPLY', mat('SUBTRACT', 0.15, gonfia), scoppiata))
    sc_v = nodo('ShaderNodeCombineXYZ'); L(sxy, sc_v.inputs[0]); L(sxy, sc_v.inputs[1]); L(sz, sc_v.inputs[2])
    # la bolla: mezza sfera schiacciata, appoggiata sulla superficie
    sfera = nodo('GeometryNodeMeshUVSphere'); sfera.inputs['Segments'].default_value = 12; sfera.inputs['Rings'].default_value = 6
    sfera.inputs['Radius'].default_value = raggio
    tr = nodo('GeometryNodeTransform'); L(sfera.outputs['Mesh'], tr.inputs['Geometry']); tr.inputs['Scale'].default_value = (1, 1, 0.6)
    sm_ = nodo('GeometryNodeSetMaterial'); L(tr.outputs[0], sm_.inputs['Geometry']); sm_.inputs['Material'].default_value = _mat_bolla()
    iop = nodo('GeometryNodeInstanceOnPoints'); L(dist.outputs['Points'], iop.inputs['Points']); L(sm_.outputs[0], iop.inputs['Instance'])
    L(dist.outputs['Rotation'], iop.inputs['Rotation']); L(sc_v.outputs[0], iop.inputs['Scale'])
    # lo sbuffo dello scoppio: compare sul fronte e svanisce subito dietro
    w = mat('MINIMUM', mat('MAXIMUM', mat('DIVIDE', mat('SUBTRACT', u, 0.6), 2.6), 0.0), 1.0)
    s_sb = mat('SINE', mat('MULTIPLY', w, math.pi))
    sfera2 = nodo('GeometryNodeMeshIcoSphere'); sfera2.inputs['Radius'].default_value = raggio * 1.9; sfera2.inputs['Subdivisions'].default_value = 1
    sm2 = nodo('GeometryNodeSetMaterial'); L(sfera2.outputs['Mesh'], sm2.inputs['Geometry']); sm2.inputs['Material'].default_value = _mat_sbuffo()
    iop2 = nodo('GeometryNodeInstanceOnPoints'); L(dist.outputs['Points'], iop2.inputs['Points']); L(sm2.outputs[0], iop2.inputs['Instance'])
    L(mat('GREATER_THAN', s_sb, 0.02), iop2.inputs['Selection']); L(s_sb, iop2.inputs['Scale'])
    j = nodo('GeometryNodeJoinGeometry')
    for x in (iop2.outputs[0], iop.outputs[0], gi.outputs[0]): L(x, j.inputs[0])
    L(j.outputs[0], go.inputs[0])
    mod = pony.modifiers.new('Bolle', 'NODES'); mod.node_group = ng
    mod[s_i.identifier] = tuple(impatto); mod[s_r.identifier] = 0.0
    nodo_fronte = sgonfia(pony, impatto)
    def chiave(f, r):
        mod[s_r.identifier] = r; pony.keyframe_insert('modifiers["Bolle"]["%s"]' % s_r.identifier, frame=f)
        if nodo_fronte: nodo_fronte.outputs[0].default_value = r; nodo_fronte.outputs[0].keyframe_insert('default_value', frame=f)
    return chiave
