# ANIMATIC del trailer in Blender: un fotogramma per shot (S09 e S13 ne hanno più d'uno), coi modelli veri del gioco,
# a bassa qualità (EEVEE, 1280x536) per decidere inquadrature e ritmo prima dei render veri.
# Le inquadrature seguono trailer/blender/STORYBOARD.md; i numeri di luce sono quelli di LUCE_TAPPE (horse-racing-3d.html).
#
# uso:  blender -b --python tools/trailer3d/animatic.py -- <uscita cartella> [S03 S09a ... | tutti]
#
# CONVENZIONI DEL MONDO: Z su, strada lungo Y, il protagonista sta in (0,0,0) e guarda -Y (la sua manica blu, il braccio
# destro, è a -X). Il coccodrillo ha la testa a +X. Azimut del sole: angolo da +X in senso antiorario, dove sta il sole
# visto dalla scena (270 = sta in direzione -Y). Calibrato: sun_rotation del nodo Sky = 90 - azimut.
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix, noise

QUI = os.path.dirname(os.path.abspath(__file__))
A = os.path.abspath(os.path.join(QUI, '..', '..', 'assets')) + '/'
W, H = 1280, 536                      # 2,39:1

# --- luce per tappa: (elevazione, colore del sole, colore della nebbia) da LUCE_TAPPE ------------------------------------
LUCE = dict(
    kherlen=(4, '#ffb27a', '#e9c3a6'), onon=(14, '#ffd9ae', '#dfe0dc'), burkhan=(28, '#fff1d6', '#cfdde6'),
    tuul=(58, '#ffffff', '#d9e4ea'), elsen=(38, '#fff0cf', '#e8d6b4'), cascate=(19, '#ffd6a0', '#e6d4bb'),
    kharbalgas=(3, '#ff9a5a', '#e0a98c'), erdene=(-2, '#ff8a6a', '#7f84a8'), karakorum=(-5, '#9aa8ff', '#2e3858'))

def hexc(h, k=1.0):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
    return tuple(((x/12.92) if x <= 0.04045 else ((x+0.055)/1.055)**2.4)*k for x in c) + (1.0,)      # sRGB → lineare

def vec(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.cos(a)*math.cos(e), math.sin(a)*math.cos(e), math.sin(e)))

# --- scena ----------------------------------------------------------------------------------------------------------------
def nuovo(esposizione=0.0, campioni=24):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for t in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try: sc.render.engine = t; break
        except TypeError: pass
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    try: sc.eevee.taa_render_samples = campioni
    except Exception: pass
    try: sc.eevee.use_raytracing = False
    except Exception: pass
    sc.view_settings.exposure = esposizione
    try: sc.view_settings.view_transform = 'AgX'
    except TypeError: pass
    return sc

FOSCHIA = None
def materiale(nome, colore=(0.5, 0.5, 0.5, 1), tex=None, scala=0.1, rough=0.9, metallo=0.0, emissione=None, forza=1.0, alfa=1.0, tinta=None, foschia=False):
    m = bpy.data.materials.new(nome); m.use_nodes = True; nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metallo
    if alfa < 1: b.inputs['Alpha'].default_value = alfa
    if tex:
        tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); im = nt.nodes.new('ShaderNodeTexImage')
        mp.inputs['Scale'].default_value = (scala, scala, scala)
        im.image = bpy.data.images.load(A + tex, check_existing=True)
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], im.inputs['Vector'])
        if tinta:
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
            mx.inputs['B'].default_value = tinta; nt.links.new(im.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
        else:
            nt.links.new(im.outputs['Color'], b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = colore
    if emissione:
        b.inputs['Emission Color'].default_value = emissione; b.inputs['Emission Strength'].default_value = forza
    if foschia and FOSCHIA:                                  # più è lontano, più il colore tende a quello della nebbia
        col, dist, k = FOSCHIA
        cd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange'); mr.clamp = True
        mr.inputs['From Max'].default_value = dist; nt.links.new(cd.outputs['View Distance'], mr.inputs['Value'])
        pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 1.6; nt.links.new(mr.outputs['Result'], pw.inputs[0])
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = col; em.inputs['Strength'].default_value = k
        mx = nt.nodes.new('ShaderNodeMixShader'); out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        nt.links.new(pw.outputs['Value'], mx.inputs['Fac']); nt.links.new(b.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2])
        nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
    return m

def collega(o, mat=None):
    bpy.context.scene.collection.objects.link(o)
    if mat: o.data.materials.append(mat)
    return o

def strato_nuvole(nt, cielo_out, elev, az, copertura=0.40, scala=1.3, colore_sole=(1.0, 0.98, 0.95), ombra=(0.50, 0.57, 0.70), forza=2.2, altezza=0.13, seme=1.3, passo=0.16):
    """Un cielo di CUMULI nel mondo (24 nov): un rumore frattale proiettato su un piano alto, con l'ombra finta che si legge verso il sole
    (dove c'è più nuvola fra il punto e il sole il punto è in ombra: bordi chiari verso il sole, pance scure), sfumato verso l'orizzonte.
    Funziona uguale in EEVEE e in Cycles (è solo un nodo del mondo); le vecchie carte di nuvole (foto del gioco) restano facoltative."""
    import fumo
    N = fumo._Nodi(nt)
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    x, y, z = sep.outputs['X'], sep.outputs['Y'], sep.outputs['Z']
    zz = N.m('ADD', N.m('MAXIMUM', z, 0.0), altezza)
    u = N.m('MULTIPLY', N.m('DIVIDE', x, zz), scala); v = N.m('MULTIPLY', N.m('DIVIDE', y, zz), scala)
    sv = vec(az, max(elev, 10.0)); sz = sv.z + altezza
    su, sw = sv.x / sz * scala, sv.y / sz * scala; ln = max(1e-6, math.hypot(su, sw)); su, sw = su / ln * passo * scala, sw / ln * passo * scala
    lo = 0.68 - 0.50 * copertura
    def densita(du, dv):
        c = nt.nodes.new('ShaderNodeCombineXYZ'); c.inputs['Z'].default_value = seme
        nt.links.new(N.m('ADD', u, du), c.inputs['X']); nt.links.new(N.m('ADD', v, dv), c.inputs['Y'])
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '3D'; nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 6.0
        nz.inputs['Roughness'].default_value = 0.56; nz.inputs['Distortion'].default_value = 0.35; nt.links.new(c.outputs[0], nz.inputs['Vector'])
        return N.liscia(nz.outputs['Fac'], lo, lo + 0.15)
    d1 = densita(0.0, 0.0); d2 = densita(su, sw)
    lit = N.m('SUBTRACT', 1.45, N.m('MULTIPLY', N.m('MAXIMUM', N.m('SUBTRACT', d2, N.m('MULTIPLY', d1, 0.40)), 0.0), 1.15), clamp=True)
    # il colore della nuvola SI MISURA SUL CIELO: la luminosità del cielo in quella direzione × (1,05 in ombra … forza al sole), tinta di ombra o di sole.
    # (i colori assoluti non andavano: la radianza del cielo Nishita è di ordini di grandezza diversa da una stagione all'altra)
    lum = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(cielo_out, lum.inputs['Color'])
    cm = nt.nodes.new('ShaderNodeMix'); cm.data_type = 'RGBA'; nt.links.new(lit, cm.inputs['Factor'])
    cm.inputs['A'].default_value = tuple(ombra) + (1,); cm.inputs['B'].default_value = tuple(colore_sole) + (1,)
    val = N.m('MULTIPLY', lum.outputs['Val'], N.m('ADD', 1.05, N.m('MULTIPLY', lit, forza - 1.05)))
    gr = nt.nodes.new('ShaderNodeCombineColor')
    for q in ('Red', 'Green', 'Blue'): nt.links.new(val, gr.inputs[q])
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'; col.blend_type = 'MULTIPLY'; col.inputs['Factor'].default_value = 1.0
    nt.links.new(cm.outputs['Result'], col.inputs['A']); nt.links.new(gr.outputs['Color'], col.inputs['B'])
    mask = N.m('MULTIPLY', d1, N.liscia(z, 0.015, 0.22))
    fin = nt.nodes.new('ShaderNodeMix'); fin.data_type = 'RGBA'; nt.links.new(mask, fin.inputs['Factor'])
    nt.links.new(cielo_out, fin.inputs['A']); nt.links.new(col.outputs['Result'], fin.inputs['B'])
    return fin.outputs['Result']

def cielo(elev, az, polvere=1.0, aria=1.0, forza=0.45, nebbia=None, sole=None, energia=3.0, disco=2.0, nuvole=None):
    """Cielo Nishita + lampada Sole (fa le ombre). nebbia = (densità, colore hex) → volume nel mondo."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new('mondo'); sc.world = w; nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); sk = nt.nodes.new('ShaderNodeTexSky')
    for t in ('MULTIPLE_SCATTERING', 'NISHITA'):
        try: sk.sky_type = t; break
        except TypeError: pass
    sk.sun_elevation = math.radians(elev); sk.sun_rotation = math.radians(90 - az)
    sk.air_density, sk.aerosol_density = aria, polvere
    sk.sun_disc = True; sk.sun_size = math.radians(disco)
    bg.inputs['Strength'].default_value = forza
    cielo_col = sk.outputs[0]
    if nuvole: cielo_col = strato_nuvole(nt, cielo_col, elev, az, **nuvole)
    nt.links.new(cielo_col, bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs['Surface'])
    for k, v in (('use_sun_shadow', False),):
        try: setattr(w, k, v)
        except Exception: pass
    global FOSCHIA
    FOSCHIA = (hexc(nebbia[1]), min(900.0, 0.9/nebbia[0]), nebbia[2] if len(nebbia) > 2 else 1.0) if nebbia else None
    if energia:
        l = bpy.data.lights.new('sole', 'SUN'); l.energy = energia; l.angle = math.radians(1.2)
        l.color = hexc(sole)[:3] if sole else (1, 1, 1)
        o = bpy.data.objects.new('sole', l); o.rotation_euler = (-vec(az, max(elev, 1))).to_track_quat('-Z', 'Y').to_euler(); sc.collection.objects.link(o)

def notte(az_luna=90, el_luna=24, forza_luna=1.4, ambiente=1.0, grandezza_luna=2.2, orizzonte=(0.035, 0.045, 0.10), stelle=True):
    """Cielo notturno: gradiente scuro con alone all'orizzonte, stelle, luna (disco emissivo + lampada)."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new('notte'); sc.world = w; nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); mr = nt.nodes.new('ShaderNodeMapRange')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.30; mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0; mr.clamp = True
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    mx.inputs['A'].default_value = (0.004, 0.008, 0.026, 1); mx.inputs['B'].default_value = orizzonte + (1,)
    nt.links.new(mr.outputs['Result'], mx.inputs['Factor'])
    col = mx.outputs['Result']
    if stelle:
        vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.voronoi_dimensions = '3D'; vo.inputs['Scale'].default_value = 220
        cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (1, 1, 1, 1)
        cr.color_ramp.elements[1].position = 0.07; cr.color_ramp.elements[1].color = (0, 0, 0, 1)
        nt.links.new(tc.outputs['Generated'], vo.inputs['Vector']); nt.links.new(vo.outputs['Distance'], cr.inputs['Fac'])
        ad = nt.nodes.new('ShaderNodeMix'); ad.data_type = 'RGBA'; ad.blend_type = 'ADD'; ad.inputs['Factor'].default_value = 0.9
        nt.links.new(col, ad.inputs['A']); nt.links.new(cr.outputs['Color'], ad.inputs['B']); col = ad.outputs['Result']
    nt.links.new(col, bg.inputs['Color']); bg.inputs['Strength'].default_value = ambiente
    nt.links.new(bg.outputs[0], out.inputs['Surface'])
    d = vec(az_luna, el_luna)
    l = bpy.data.lights.new('luna', 'SUN'); l.energy = forza_luna; l.color = hexc('#9aa8ff')[:3]; l.angle = math.radians(1.5)
    o = bpy.data.objects.new('luna', l); o.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler(); sc.collection.objects.link(o)
    R = 700.0
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R*math.tan(math.radians(grandezza_luna)), segments=48, ring_count=24, location=d*R)
    m = bpy.context.object
    import luna as LU                                                          # la luna con mari e crateri (la stessa di S27), non più un disco liscio
    mt = LU.materiale_luna(1.5); mt.name = 'luna'; m.data.materials.append(mt)

_TERR = {}
def quota(x, y):
    P = _TERR
    k = min(1.0, max(0.0, (abs(x) - P['piatto'])/60.0)); k = k*k*(3 - 2*k); r = P['rilievo']
    h = (noise.noise(Vector((x*0.0035, y*0.0035, 1.7)))*r + noise.noise(Vector((x*0.011, y*0.011, 8.1)))*r*0.25) * k
    if P['onde']: h += (math.sin(x*0.045 + noise.noise(Vector((x*0.01, y*0.01, 3)))*4) * 0.5 + 0.5) * P['onde'] * (0.3 + 0.7*k)
    return h

def terreno(colore_tex='textures/Grass004/Grass004_1K-JPG_Color.jpg', scala=0.33, tinta=None, rilievo=5.0, strada=True, dim=1400, res=220, onde=0.0, piatto=18.0, larg_strada=9.0):
    """Pianura ondulata, piatta attorno alla strada (lungo Y). onde = dune regolari."""
    _TERR.update(piatto=piatto, rilievo=rilievo, onde=onde)
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=res, y_segments=res, size=dim/2)
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        k = min(1.0, max(0.0, (abs(x) - piatto)/60.0)); k = k*k*(3 - 2*k)
        h = (noise.noise(Vector((x*0.0035, y*0.0035, 1.7)))*rilievo + noise.noise(Vector((x*0.011, y*0.011, 8.1)))*rilievo*0.25) * k
        if onde: h += (math.sin(x*0.045 + noise.noise(Vector((x*0.01, y*0.01, 3)))*4) * 0.5 + 0.5) * onde * (0.3 + 0.7*k)
        v.co.z = h
    me = bpy.data.meshes.new('terreno'); bm.to_mesh(me); bm.free()
    t = collega(bpy.data.objects.new('terreno', me), materiale('erba', tex=colore_tex, scala=scala, tinta=tinta, rough=0.95, foschia=True))
    for p in me.polygons: p.use_smooth = True
    if strada:
        bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=60, size=1)
        for v in bm.verts: v.co.x *= larg_strada/2; v.co.y *= dim/2; v.co.z = 0.03
        me2 = bpy.data.meshes.new('strada'); bm.to_mesh(me2); bm.free()
        collega(bpy.data.objects.new('strada', me2), materiale('asfalto', tex='textures/Asphalt014/Asphalt014_1K-JPG_Color.jpg', scala=0.3, rough=0.8, foschia=True))
    return t

def fiume(larg=16.0, amp=14.0, z=0.25, lung=500, colore=(0.10, 0.17, 0.22, 1)):
    bm = bmesh.new(); n = 80
    pts = [(amp*math.sin(y*0.022) + 0.6*amp*math.sin(y*0.057), y) for y in [(-lung/2) + lung*i/n for i in range(n+1)]]
    vs = []
    for x, y in pts:
        vs.append((bm.verts.new((x - larg/2, y, z)), bm.verts.new((x + larg/2, y, z))))
    for (a, b), (c, d) in zip(vs[:-1], vs[1:]): bm.faces.new((a, b, d, c))
    me = bpy.data.meshes.new('fiume'); bm.to_mesh(me); bm.free()
    return collega(bpy.data.objects.new('fiume', me), materiale('acqua', colore=colore, rough=0.04, metallo=0.0))

# --- modelli --------------------------------------------------------------------------------------------------------------
def importa(file, azione=None, frame=0, tinta=None, nome='m', mano=False):
    """Importa un GLB, lo mette in posa (azione, fotogramma), CUOCE la posa in mesh statiche e butta lo scheletro:
    così si possono avere più copie dello stesso modello in pose diverse. Ritorna la radice (Empty) e, se mano=True,
    il punto-mano del protagonista (da ARMI.mano di 3d/armi.js) già portato nella posa."""
    sc = bpy.context.scene
    prima = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=A + file)
    nuovi = [o for o in bpy.data.objects if o not in prima]
    for o in list(nuovi):
        # via i segnaposto: l'Icosphere dei modelli del gioco e la sferetta di 4 cm (materiale «m») che hanno le armi di Tripo
        piccola = o.type == 'MESH' and o.name.startswith('Sphere') and max(o.dimensions) < 0.05
        if o.name.startswith('Icosphere') or piccola: bpy.data.objects.remove(o); nuovi.remove(o)
    arm = next((o for o in nuovi if o.type == 'ARMATURE'), None)
    info = {}
    if arm and azione:
        ad = arm.animation_data
        tr = next((x for x in ad.nla_tracks if x.name == azione), None) or next(x for x in ad.nla_tracks if x.name.endswith('|' + azione))
        act = tr.strips[0].action
        for x in list(ad.nla_tracks): ad.nla_tracks.remove(x)
        ad.action = act
        try:
            if ad.action_slot is None and act.slots: ad.action_slot = act.slots[0]
        except Exception: pass
        sc.frame_set(frame)
    bpy.context.view_layer.update()
    if mano and arm and 'Torso3' in arm.data.bones:
        Mw = arm.matrix_world
        rest = Mw @ arm.data.bones['Torso3'].matrix_local; pose = Mw @ arm.pose.bones['Torso3'].matrix
        info['mano'] = (pose @ rest.inverted()) @ Vector((-0.24, -0.56, 1.30))
    if tinta:
        for o in nuovi:
            if o.type == 'MESH':
                for m in o.data.materials:
                    b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                    if b and not b.inputs['Base Color'].is_linked:
                        c = b.inputs['Base Color'].default_value; b.inputs['Base Color'].default_value = (c[0]*tinta[0], c[1]*tinta[1], c[2]*tinta[2], 1)
    dg = bpy.context.evaluated_depsgraph_get()
    radice = bpy.data.objects.new(nome, None); sc.collection.objects.link(radice)
    for o in [x for x in nuovi if x.type == 'MESH']:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        n = bpy.data.objects.new(o.name + '_b', me); n.matrix_world = o.matrix_world.copy(); sc.collection.objects.link(n); n.parent = radice
    for o in nuovi:
        if o.name in bpy.data.objects: bpy.data.objects.remove(o)
    return radice, info

def metti(r, pos=(0, 0, 0), yaw=0.0, scala=1.0, rot=(0, 0, 0)):
    r.location = pos; r.scale = (scala,)*3
    r.rotation_euler = (math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2] + yaw))
    return r

def mondo_a_locale(pos, yaw, scala, p):                       # punto locale → mondo per una radice con yaw/scala (niente altre rotazioni)
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return Vector((pos[0] + scala*(c*p.x - s*p.y), pos[1] + scala*(s*p.x + c*p.y), pos[2] + scala*p.z))

def eroe(pos=(0, 0, 0), azione='Idle', frame=0, yaw=0.0, rot=(0, 0, 0), arma=None, arma_rot=(50, 0, 0), nome='eroe'):
    r, info = importa('models/protagonista-cartone.glb', azione, frame, nome=nome, mano=True)
    metti(r, pos, yaw, 1.0, rot)
    if arma:
        a, _ = importa('models/armi/%s.glb' % arma, nome='arma')
        # la mano è in coordinate del modello a riposo/posa; con rot≠0 si fa un'approssimazione: l'arma segue la radice
        a.parent = r; a.location = info['mano']; a.rotation_euler = tuple(math.radians(v) for v in arma_rot)
    return r

def predone(pos, tinta, azione='Gallop', frame=0, yaw=0.0, scala=0.46, nome='predone', rot=(0, 0, 0)):
    r, _ = importa('models/horse-quaternius.glb', azione, frame, tinta=tinta, nome=nome)
    return metti(r, pos, yaw, scala, rot)

def animale(file, pos, azione='Idle', frame=0, yaw=0.0, scala=1.0, nome='animale'):
    r, _ = importa('animali/%s.glb' % file, azione, frame, nome=nome)
    return metti(r, pos, yaw, scala)

def oggetto(file, pos, yaw=0.0, scala=1.0, rot=(0, 0, 0), nome='oggetto'):
    r, _ = importa(file, nome=nome); return metti(r, pos, yaw, scala, rot)

def boss(pos=(0, 0, 0), yaw=0.0, scala=1.35, mascella=0.0):
    """Il coccodrillo (testa a +X). mascella in gradi: apre la bocca ruotando la Mascella attorno al suo perno."""
    r, _ = importa('models/boss/coccodrillo.glb', nome='boss')
    metti(r, pos, yaw, scala)
    return r

# --- piccoli oggetti di scena ---------------------------------------------------------------------------------------------
def sfera(pos, raggio, mat, nome='sfera'):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=raggio, segments=16, ring_count=8, location=pos)
    o = bpy.context.object
    for p_ in o.data.polygons: p_.use_smooth = True
    o.data.materials.append(mat); return o

def scatola(pos, dim, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.object
    o.scale = dim; o.rotation_euler = tuple(math.radians(v) for v in rot); o.data.materials.append(mat); return o

def materiale_polvere(colore, alfa):
    m = bpy.data.materials.new('polvere'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    em.inputs['Color'].default_value = colore; em.inputs['Strength'].default_value = 1.0; mx.inputs['Fac'].default_value = alfa
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def polvere(centro, n=70, raggio=3.0, size=(0.25, 0.7), colore=(0.62, 0.50, 0.36, 1), alfa=0.18, schiaccia=0.5, seme=3):
    random.seed(seme); m = materiale_polvere(colore, alfa)
    for i in range(n):
        d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1)*schiaccia)); d.normalize(); d *= raggio*random.random()**0.5
        sfera(Vector(centro) + d, random.uniform(*size), m)

def zolle(centro, n=60, raggio=1.0, size=(0.02, 0.07), seme=9):
    """Terra e fili d'erba lanciati in aria: pezzetti piccoli e opachi."""
    random.seed(seme); m = materiale('terra', colore=(0.22, 0.16, 0.10, 1), rough=1.0)
    for i in range(n):
        d = Vector((random.gauss(0, 1), random.gauss(0, 1), abs(random.gauss(0, 1))*1.3)); d *= raggio*0.5
        sfera(Vector(centro) + d, random.uniform(*size), m)

def scintille(centro, n=25, raggio=0.5, colore='#ffd9a0', forza=40.0, seme=5):
    random.seed(seme); m = materiale('scintilla', colore=(0, 0, 0, 1), emissione=hexc(colore), forza=forza)
    for i in range(n):
        d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))); d.normalize(); d *= raggio*random.random()
        sfera(Vector(centro) + d, random.uniform(0.01, 0.03), m)

def lampada(pos, colore='#ffb060', energia=400, raggio=0.1, tipo='POINT'):
    l = bpy.data.lights.new('luce', tipo); l.energy = energia; l.color = hexc(colore)[:3]; l.shadow_soft_size = raggio
    o = bpy.data.objects.new('luce', l); o.location = pos; bpy.context.scene.collection.objects.link(o); return o

def duna(pos, raggio, altezza, yaw=0.0, colore=(0.72, 0.55, 0.30, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24, location=(pos[0], pos[1], pos[2]))
    o = bpy.context.object; o.scale = (raggio, raggio*0.55, altezza); o.rotation_euler.z = math.radians(yaw)
    for q in o.data.polygons: q.use_smooth = True
    o.data.materials.append(materiale('sabbia', colore=colore, rough=1.0, foschia=True)); return o

def stupa(pos, scala=1.0, yaw=0.0):
    """Stupa bianca a rivoluzione (profilo: base a gradini, cupola, guglia). Non esiste in assets: modellata qui."""
    prof = [(0.0, 0.0), (1.6, 0.0), (1.6, 0.35), (1.3, 0.35), (1.3, 0.7), (1.0, 0.7), (1.0, 1.0), (0.95, 1.2), (0.8, 1.9), (0.5, 2.5), (0.2, 2.85), (0.16, 3.1), (0.1, 3.6), (0.0, 3.9)]
    bm = bmesh.new(); ring = []
    for r, z in prof: ring.append(bm.verts.new((r, 0, z)))
    for a, b in zip(ring[:-1], ring[1:]): bm.edges.new((a, b))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=20)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    me = bpy.data.meshes.new('stupa'); bm.to_mesh(me); bm.free()
    o = collega(bpy.data.objects.new('stupa', me), materiale('calce', colore=(0.82, 0.80, 0.74, 1), rough=0.9))
    o.location = pos; o.scale = (scala,)*3; o.rotation_euler.z = math.radians(yaw)
    for p in me.polygons: p.use_smooth = True
    return o

def camera(pos, mira, lens=35, fuoco=None, fstop=None, rollio=0.0):
    sc = bpy.context.scene
    c = bpy.data.cameras.new('cam'); c.lens = lens; c.sensor_width = 36; c.clip_end = 30000
    o = bpy.data.objects.new('cam', c); sc.collection.objects.link(o); sc.camera = o
    o.location = pos; d = Vector(mira) - Vector(pos)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if rollio: o.rotation_euler.rotate_axis('Z', math.radians(rollio))
    if fstop:
        c.dof.use_dof = True; c.dof.aperture_fstop = fstop
        c.dof.focus_distance = d.length if fuoco is None else (Vector(fuoco) - Vector(pos)).length
    return o

def scatta(uscita):
    sc = bpy.context.scene
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92
    sc.render.filepath = uscita
    bpy.ops.render.render(write_still=True)
    print('FATTO', uscita)

# =============================================================================================================================
# GLI SHOT. Ogni funzione costruisce la scena da zero (nuovo()) e lascia pronta la camera. Numeri = STORYBOARD.md.
# =============================================================================================================================
S = {}
def shot(*nomi):
    def d(f):
        for n in nomi: S[n] = f
        return f
    return d

@shot('S01')
def s01():
    nuovo(); e, sole, neb = LUCE['kherlen']
    cielo(e, 270, polvere=2.0, aria=1.4, sole=sole, energia=3.0, nebbia=(0.0016, neb))
    terreno(strada=False, tinta=hexc('#d8d0a0'), rilievo=9.0)
    fiume()
    for i, (x, y) in enumerate([(22, -60), (27, -64), (30, -58)]): animale('pecora', (x, y, 0.0), frame=i*20, yaw=70+i*30, nome='pecora%d' % i)
    animale('mucca', (-26, -80, 0.0), yaw=20, nome='mucca')
    camera((70, 170, 52), (0, -40, 0), 24)

@shot('S02')
def s02():
    nuovo(); e, sole, neb = LUCE['kherlen']
    cielo(e, 90, polvere=2.0, aria=1.4, sole=sole, energia=3.2, nebbia=(0.0012, neb))
    terreno(strada=False, tinta=hexc('#d8d0a0'), rilievo=4.0)
    random.seed(11); toni = [(0.9, 0.62, 0.42), (0.38, 0.30, 0.26), (0.95, 0.9, 0.8), (0.55, 0.40, 0.30), (0.28, 0.22, 0.2), (0.8, 0.6, 0.4)]
    for i in range(11):
        predone((random.uniform(-9, 8) + (i % 3)*0.8, random.uniform(-5, 4), 0), toni[i % len(toni)], frame=(i*5) % 14, yaw=90, scala=0.47, nome='cavallo%d' % i)
    polvere((-1, 3, 0.9), n=70, raggio=9, size=(0.5, 1.2), colore=(0.9, 0.65, 0.4, 1), alfa=0.06)
    camera((0, -64, 1.4), (0, 0, 1.9), 135, fstop=4.0, fuoco=(0, 0, 1.7))

@shot('S03')
def s03():
    nuovo(); e, sole, neb = LUCE['kherlen']
    cielo(e, 255, polvere=2.2, aria=1.3, sole=sole, energia=3.4, nebbia=(0.0014, neb))
    terreno(tinta=hexc('#d8d0a0'), rilievo=4.0)
    eroe((0, 0, 0), 'Idle', 20)
    random.seed(4)
    for i in range(6): predone((-60 - i*6, -150 - random.uniform(0, 14), 0), (0.45, 0.33, 0.26), frame=i*2, yaw=95, scala=0.47, nome='lontano%d' % i)
    camera((1.0, 8.5, 1.0), (-4, -30, 2.4), 50)

@shot('S04')
def s04():
    nuovo(); e, sole, neb = LUCE['kherlen']
    cielo(e, 225, polvere=2.2, aria=1.3, sole=sole, energia=3.4, nebbia=(0.0008, neb))
    terreno(tinta=hexc('#c8d0a0'), rilievo=3.0)
    eroe((0, 0, 0), 'Idle', 30)
    camera((-0.9, -1.6, 0.16), (0.0, -0.45, 0.85), 32, fstop=3.2, fuoco=(0, -0.45, 0.3))

@shot('S05')
def s05():
    nuovo(); e, sole, neb = LUCE['kherlen']
    cielo(e, 250, polvere=2.2, aria=1.3, sole=sole, energia=3.6, nebbia=(0.0008, neb))
    terreno(tinta=hexc('#c8d0a0'), rilievo=3.0)
    eroe((0, 0, 0), 'Idle', 12)
    camera((-1.9, -2.7, 1.5), (-0.1, -0.65, 1.42), 100, fstop=3.2, fuoco=(-0.15, -0.65, 1.42))

@shot('S06')
def s06():
    nuovo(); e, sole, neb = LUCE['onon']
    cielo(e, 285, polvere=1.5, sole=sole, energia=3.6, nebbia=(0.0006, neb))
    terreno(tinta=hexc('#cfd8a8'), rilievo=3.0)
    eroe((0, 1.0, 0.0), 'Gallop', 6)
    zolle((0, 0.2, 0.2), n=220, raggio=1.3, size=(0.004, 0.014)); polvere((0, 1.0, 0.5), n=40, raggio=1.8, size=(0.2, 0.6), alfa=0.10)
    camera((0.35, -2.4, 0.22), (0, 0.6, 0.5), 24, fstop=4, fuoco=(0, 0.6, 0.4))

@shot('S07')
def s07():
    nuovo(); e, sole, neb = LUCE['onon']
    cielo(e, 150, polvere=1.5, sole=sole, energia=3.6, nebbia=(0.0006, neb))
    terreno(tinta=hexc('#cfd8a8'), rilievo=3.5)
    eroe((0, 0, 0), 'Gallop', 10)
    polvere((0, 2.4, 0.3), n=60, raggio=1.4, size=(0.1, 0.35), alfa=0.4)
    camera((6.8, 0.2, 1.05), (0, -0.1, 0.95), 35, fstop=2.8, fuoco=(0, 0, 0.9))

@shot('S08')
def s08():
    nuovo(); e, sole, neb = LUCE['onon']
    cielo(e, 80, polvere=1.5, sole=sole, energia=3.4, nebbia=(0.0006, neb))
    terreno(tinta=hexc('#cfd8a8'), rilievo=3.5)
    eroe((0, -1.0, 0), 'Gallop', 14)
    oggetto('models/armi/cassa.glb', (0, -4.4, 0.0), yaw=15, scala=1.0, nome='cassa')
    lampada((0, -4.4, 1.0), colore='#ffb060', energia=500, raggio=0.4)
    oggetto('models/armi/saber.glb', (0, -4.4, 1.5), rot=(30, 10, 35), scala=1.2, nome='sciabola')
    scintille((0, -4.4, 1.2), n=40, raggio=1.2, colore='#c8955a', forza=3)
    camera((1.5, -8.6, 1.1), (0, -3.6, 1.0), 35)

@shot('S09a', 'S09b', 'S09c', 'S09d')
def s09(nome):
    nuovo(); e, sole, neb = LUCE['onon']
    cielo(e, 300, polvere=1.5, sole=sole, energia=4.0, nebbia=(0.0004, neb))
    terreno(tinta=hexc('#cfd8a8'), rilievo=3.5)
    f, rot, lung = dict(S09a=('saber', (14, 0, 12), 0.85), S09b=('mace', (12, 0, -18), 0.60), S09c=('whip', (6, 0, 12), 1.0), S09d=('bow', (0, 0, 14), 0.95))[nome]
    k = 1.5; pos = (0, 0, 1.0)
    oggetto('models/armi/%s.glb' % f, pos, rot=rot, scala=k, nome='arma')
    if nome == 'S09d': oggetto('models/armi/freccia.glb', (0.12, 0.05, 1.0), rot=(0, 0, 14), scala=1.3, nome='freccia')
    cz = 1.0 if nome == 'S09d' else 1.0 + 0.5*lung*k
    camera((-1.5, -2.3, cz + 0.1), (0, 0, cz), 70, fstop=2.0, fuoco=(0, 0, cz))

@shot('S10')
def s10():
    nuovo(); e, sole, neb = LUCE['onon']
    cielo(e, 140, polvere=1.5, sole=sole, energia=3.6, nebbia=(0.0006, neb))
    terreno(tinta=hexc('#cfd8a8'), rilievo=3.5)
    eroe((0, -1.5, 0), 'Gallop', 8)
    predone((-3.4, 1.4, 0), hexc('#ffc9a3')[:3], frame=2, nome='p1')
    predone((3.4, 2.4, 0), hexc('#a9c8ff')[:3], frame=9, nome='p2')
    predone((-0.4, 6.0, 0), hexc('#d6ffb3')[:3], frame=5, nome='p3')
    polvere((0, 8.5, 0.6), n=120, raggio=5, size=(0.4, 1.0), alfa=0.08)
    camera((7.5, -8.5, 2.3), (-0.3, 1.6, 1.2), 32)

@shot('S11')
def s11():
    nuovo(); e, sole, neb = LUCE['burkhan']
    cielo(e, 60, polvere=1.2, sole=sole, energia=3.6, nebbia=(0.0005, neb))
    terreno(tinta=hexc('#cfd8a8'), rilievo=3.5)
    eroe((0, 0, 0), 'Gallop', 14, arma='saber', arma_rot=(62, 0, 18))
    predone((-3.0, -0.4, 0), hexc('#a9c8ff')[:3], azione='Attack_Headbutt', frame=12, yaw=90, nome='rivale')
    scintille((-1.5, -0.55, 1.5), n=60, raggio=0.7, forza=80)
    lampada((-1.5, -0.55, 1.5), colore='#ffe0b0', energia=300, raggio=0.15)
    polvere((-1.5, 0.5, 0.5), n=90, raggio=2.2, size=(0.05, 0.2), alfa=0.35)
    camera((-1.6, -6.0, 1.5), (-1.5, -0.3, 1.5), 40)

@shot('S12')
def s12():
    nuovo(); e, sole, neb = LUCE['burkhan']
    cielo(e, 200, polvere=1.2, sole=sole, energia=3.6, nebbia=(0.0005, neb))
    terreno(tinta=hexc('#cfd8a8'), rilievo=3.5)
    eroe((0.0, 0, 0), 'Gallop', 20, rot=(0, 0, 0), yaw=8)
    predone((3.3, 0.8, 0), hexc('#ffc9a3')[:3], azione='Attack_Kick', frame=10, yaw=-90, nome='rivale')
    polvere((1.5, 1.0, 0.4), n=70, raggio=2.0, size=(0.05, 0.25), alfa=0.35)
    camera((-0.5, -7.5, 1.3), (1.4, 0.2, 1.2), 35)

@shot('S13a')
def s13a():
    nuovo(); e, sole, neb = LUCE['burkhan']
    cielo(e, 80, polvere=1.2, sole=sole, energia=3.6, nebbia=(0.0005, neb))
    terreno(tinta=hexc('#cfd8a8'), rilievo=3.5)
    oggetto('models/pluriball/rotolo.glb', (0, -5.5, 0.0), yaw=30, scala=1.6, nome='rotolo')
    eroe((0, -1.0, 0), 'Gallop', 4)
    camera((2.2, -9.5, 0.9), (0, -4.0, 0.7), 28)

@shot('S13b')
def s13b():
    nuovo(); e, sole, neb = LUCE['burkhan']
    cielo(e, 40, polvere=1.2, sole=sole, energia=3.6, nebbia=(0.0005, neb))
    terreno(tinta=hexc('#cfd8a8'), rilievo=3.5)
    p, _ = importa('models/pluriball/pony-skin.glb', nome='pony'); metti(p)
    oggetto('models/armi/mace.glb', (-0.95, -0.7, 1.0), rot=(0, 0, -62), scala=1.2, nome='mazza')
    scintille((-0.4, -0.45, 1.1), n=40, raggio=0.4, colore='#ffffff', forza=20)
    camera((-1.9, -2.5, 1.2), (-0.45, -0.45, 1.1), 85, fstop=3.0, fuoco=(-0.4, -0.45, 1.1))

@shot('S14')
def s14():
    nuovo(); e, sole, neb = LUCE['burkhan']
    cielo(e, 120, polvere=1.2, sole=sole, energia=3.6, nebbia=(0.0005, neb))
    terreno(tinta=hexc('#cfd8a8'), rilievo=3.5)
    oggetto('models/birra/birra.glb', (-0.6, -2.4, 0.0), yaw=65, scala=2.0, nome='birra')
    eroe((0.8, 2.6, 0), 'Gallop', 16)
    camera((-5.6, -3.2, 0.45), (0, -0.5, 0.6), 35)

@shot('S15')
def s15():
    nuovo(); e, sole, neb = LUCE['tuul']
    cielo(e, 150, polvere=1.0, sole=sole, energia=4.2, nebbia=(0.0002, neb))
    terreno(tinta=hexc('#bfe0a0'), rilievo=1.5)
    eroe((0, 0, 0), 'Gallop', 2)
    camera((7.2, 0.3, 1.1), (0, -0.2, 1.0), 35, fstop=4, fuoco=(0, 0, 1.0))

@shot('S16')
def s16():
    nuovo(); e, sole, neb = LUCE['elsen']
    cielo(e, 200, polvere=10.0, aria=1.0, sole=sole, energia=3.8, nebbia=(0.0012, neb))
    terreno(tinta=hexc('#e8c98a'), rilievo=1.5)
    duna((-22, -34, -0.5), 30, 7.5, yaw=12); duna((30, -60, -0.5), 40, 10, yaw=-10); duna((-70, -80, -0.5), 55, 16, yaw=0)
    animale('lama', (-20, -33, 6.3), frame=40, yaw=10, scala=1.1, nome='lama')
    eroe((3.5, -6.0, 0.0), 'Gallop', 9, yaw=0)
    camera((10, 6, 1.5), (-14, -30, 5.0), 50)

@shot('S17')
def s17():
    nuovo(); e, sole, neb = LUCE['cascate']
    cielo(e, 240, polvere=1.5, sole=sole, energia=3.6, nebbia=(0.0014, neb))
    terreno(tinta=hexc('#b8a878'), rilievo=2.0, strada=False)
    roccia = materiale('roccia', colore=(0.34, 0.22, 0.16, 1), rough=0.95)
    scatola((-26, 10, 9), (24, 200, 18), roccia); scatola((26, 10, 9), (24, 200, 18), roccia)         # le due pareti della gola
    scatola((0, 10, 0.15), (28, 200, 0.6), materiale('fiume_rosso', colore=(0.34, 0.05, 0.025, 1), rough=0.75))   # il fiume rosso
    scatola((0, -92, -14), (28, 0.6, 28), materiale('cascata', colore=(0.40, 0.07, 0.04, 1), rough=0.75))      # la cascata
    scatola((0, -100, -29), (60, 24, 1), roccia)
    polvere((0, -96, -12), n=90, raggio=14, size=(2.0, 4.0), colore=(0.85, 0.75, 0.7, 1), alfa=0.06, schiaccia=0.8)
    eroe((-13.5, 30.0, 18.0), 'Gallop', 12, yaw=0)
    camera((6, 74, 26), (-2, -60, -4), 28)

@shot('S18')
def s18():
    nuovo(); e, sole, neb = LUCE['kharbalgas']
    cielo(e, 255, polvere=2.5, aria=1.6, sole=sole, energia=3.4, nebbia=(0.0012, neb))
    terreno(tinta=hexc('#c9a870'), rilievo=3.0)
    muro = materiale('muro', colore=(0.40, 0.30, 0.22, 1), rough=1.0)
    for i, (x, y, w_, h_) in enumerate([(-16, -60, 14, 7), (-4, -62, 8, 11), (10, -66, 16, 6), (24, -58, 6, 9), (-30, -70, 10, 5)]):
        scatola((x, y, h_/2), (w_, 2.2, h_), muro)
    eroe((0.5, -16.0, 0), 'Gallop', 6, yaw=0)
    animale('aquila', (-2.0, -7.0, 2.2), azione='Flying', frame=12, yaw=-35, scala=1.2, nome='aquila')
    camera((-1.0, 3.0, 2.6), (2.0, -40, 3.0), 45)

@shot('S19')
def s19():
    nuovo(esposizione=0.6); e, sole, neb = LUCE['erdene']
    cielo(e, 270, polvere=2.0, aria=1.2, sole='#7f84a8', energia=0.6, nebbia=(0.0014, neb), forza=1.2)
    terreno(tinta=hexc('#8a9a80'), rilievo=2.5)
    for i in range(7):
        for lato in (-1, 1): stupa((lato*(9 + (i % 2)*1.5), -4 - i*8.0, 0), scala=1.25, yaw=i*30)
    for i in range(7):
        for lato in (-1, 1): sfera((lato*(6.6), -4 - i*8.0, 1.2), 0.18, materiale('lant', colore=(0, 0, 0, 1), emissione=hexc('#ffa860'), forza=25.0))
    lampada((5.8, -4, 1.4), energia=300); lampada((-5.8, -12, 1.4), energia=300); lampada((5.8, -20, 1.4), energia=300)
    eroe((0, -5.5, 0), 'Gallop', 4)
    camera((4.4, 3.5, 1.2), (-1.0, -10.0, 1.6), 35)

@shot('S20')
def s20():
    nuovo(esposizione=1.0)
    notte(az_luna=300, el_luna=38, forza_luna=1.6, grandezza_luna=2.4)
    terreno(tinta=hexc('#4a5a55'), rilievo=3.0)
    random.seed(7)
    lant = materiale('luce_citta', colore=(0, 0, 0, 1), emissione=hexc('#ffb868'), forza=60.0)
    for i in range(70): sfera((random.uniform(-90, 90), random.uniform(-420, -380), random.uniform(0.5, 4)), 0.9, lant)
    pozza = materiale('pozza', colore=(0.02, 0.03, 0.05, 1), rough=0.02)
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, radius=2.2, segments=48)
    me = bpy.data.meshes.new('pozza'); bm.to_mesh(me); bm.free(); p = collega(bpy.data.objects.new('pozza', me), pozza); p.location = (3.0, -3.5, 0.06)
    for r in (0.5, 1.0, 1.5, 2.0):                                          # i cerchi concentrici
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.018, location=(3.0, -3.5, 0.08), major_segments=48, minor_segments=6)
        t = bpy.context.object; t.data.materials.append(materiale('cerchio', colore=(0.7, 0.8, 1, 1), emissione=hexc('#9aa8ff'), forza=3.0))
    eroe((0, 0, 0), 'Walk', 20)
    camera((-4.8, 7.0, 1.0), (1.5, -6.0, 1.7), 28)

def _luna_boss(az=90, el=22, forza=1.7, **k):
    notte(az_luna=az, el_luna=el, forza_luna=forza, grandezza_luna=2.6, **k)
    terreno(tinta=hexc('#3c4a50'), rilievo=3.0, strada=True)

@shot('S21')
def s21():
    nuovo(esposizione=1.4); _luna_boss(90, 9, 1.8)
    boss((-3, 0, 0))
    camera((1.0, -24, 1.0), (-1.0, 0, 3.4), 40)

@shot('S22')
def s22():
    nuovo(esposizione=1.6); _luna_boss(90, 28, 2.0)
    boss((0, 0, 0), scala=1.35)
    camera((-10.5, -2.6, 0.4), (4.0, -0.4, 1.0), 24)

@shot('S23')
def s23():
    nuovo(esposizione=1.0); _luna_boss(120, 24, 1.7)
    r = boss((0, 0, 0), scala=1.35)
    for o in r.children:
        if o.name.startswith('Mascella'): o.rotation_euler = (0, math.radians(38), 0); o.rotation_mode = 'XYZ'
    camera((7.8, -8.2, 2.6), (3.0, 0, 1.9), 70, fstop=2.8, fuoco=(3.0, 0, 1.9))

@shot('S24')
def s24():
    nuovo(esposizione=1.0); _luna_boss(150, 26, 1.8)
    boss((-8.5, -3.6, 0), scala=1.35)
    eroe((14, 0, 0), 'Idle', 10, yaw=-90, arma='saber', arma_rot=(18, 0, 0))
    camera((-13.0, -7.2, 1.5), (14, 0, 1.6), 50, fstop=2.8, fuoco=(14, 0, 1.6))

@shot('S25')
def s25():
    nuovo(esposizione=0.9); _luna_boss(90, 18, 1.6)
    boss((-9, 0, 0), scala=1.35)
    eroe((10, 0, 0), 'Gallop', 8, yaw=-90, arma='saber', arma_rot=(18, 0, 0))
    polvere((0, 0, 0.5), n=60, raggio=6, size=(0.3, 0.8), colore=(0.05, 0.06, 0.09, 1), alfa=0.25)
    camera((2.5, -48, 1.8), (2.5, 0, 2.4), 85)

@shot('S26')
def s26():
    nuovo(esposizione=1.0); _luna_boss(60, 22, 1.7)
    r = boss((0, 0, 0), scala=1.35)
    for o in r.children:
        if o.name.startswith('Mascella'): o.rotation_euler = (0, math.radians(30), 0)
    polvere((6.2, 0, 0.8), n=130, raggio=2.8, size=(0.3, 0.9), colore=(0.05, 0.06, 0.09, 1), alfa=0.30)
    camera((4.0, -9.5, 1.3), (5.0, 0, 1.8), 40)

@shot('S27')
def s27():
    nuovo(esposizione=0.8); _luna_boss(118, 27, 1.6)
    boss((0, 0, 0), scala=1.35)
    eroe((-1.5, 0, 5.4), 'Gallop', 18, yaw=90, rot=(-12, 0, 0), arma='saber', arma_rot=(18, 0, 0))
    camera((3.0, -6.8, 1.3), (-1.2, 0, 5.0), 35)

STORIA = ['S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08', 'S09a', 'S09b', 'S09c', 'S09d', 'S10', 'S11', 'S12', 'S13a', 'S13b', 'S14',
          'S15', 'S16', 'S17', 'S18', 'S19', 'S20', 'S21', 'S22', 'S23', 'S24', 'S25', 'S26', 'S27']

if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    cartella = os.path.abspath(a[0]); os.makedirs(cartella, exist_ok=True)
    lista = STORIA if len(a) < 2 or a[1] == 'tutti' else a[1:]
    for nome in lista:
        f = S[nome]
        f(nome) if f.__code__.co_argcount else f()
        scatta(os.path.join(cartella, nome + '.jpg'))
