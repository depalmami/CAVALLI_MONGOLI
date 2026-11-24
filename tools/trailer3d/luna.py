# LUNA GRANDE (24 nov): il disco della notte di Karakorum era una sfera emissiva liscia di 2,4° di raggio. Per S27 (il cavallo in volo davanti alla
# luna, poi il fermo immagine) serve una luna ENORME con dei dettagli, e che gli stia sempre DIETRO: il cavallo ci resta «inscritto».
#   luna = luna_grande(cam, centro, n, raggio=17.0, su=2.0)
#       cam     la camera (che si muove e gira, come nel bullet time di S27)
#       centro  funzione f → punto del mondo dietro al quale deve stare il centro del disco (il cavallo)
#       raggio  raggio angolare del disco in gradi (la luna vera è 0,25°; il quadro verticale a 26 mm è largo ~42°)
#       su      di quanti gradi il centro del disco sta sopra il punto (il cavallo un po' sotto il centro: più bello)
# Il disco sta a 700 m, lungo la retta camera → cavallo, a chiavi (la luna è all'infinito: ruota con la camera e non si sposta di parallasse),
# e ha una Track To sulla camera: mostra sempre la stessa faccia (il motivo non scivola mentre la camera gira di 30°).
import bpy, math
from mathutils import Vector

R_LUNA = 700.0


def materiale_luna(forza=0.62, caldo=(1.0, 0.95, 0.84), mari=0.60, crateri=0.55):
    """Emissivo con mari scuri (rumore a bassa frequenza), crateri grandi e piccoli (Voronoi: disco scuro e bordo chiaro), bordo del disco un po' più scuro."""
    m = bpy.data.materials.new('luna_grande'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    N = lambda t, **k: nt.nodes.new(t)

    def mat(op, a, b=None, c=None, clamp=False):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if hasattr(v, 'node'): nt.links.new(v, n.inputs[i])
            else: n.inputs[i].default_value = v
        return n.outputs[0]

    def liscia(x, a, b):
        n = nt.nodes.new('ShaderNodeMapRange'); n.interpolation_type = 'SMOOTHSTEP'; n.clamp = True
        nt.links.new(x, n.inputs['Value']); n.inputs['From Min'].default_value = a; n.inputs['From Max'].default_value = b
        return n.outputs['Result']

    gen = nt.nodes.new('ShaderNodeTexCoord').outputs['Generated']
    # mari: rumore a grandi macchie, soglia morbida
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '3D'; nz.inputs['Scale'].default_value = 2.6; nz.inputs['Detail'].default_value = 5.0
    nz.inputs['Roughness'].default_value = 0.55; nt.links.new(gen, nz.inputs['Vector'])
    mare = liscia(nz.outputs['Fac'], 0.46, 0.60)
    # crateri grandi e piccoli: F1 del Voronoi = distanza dal centro del cratere più vicino
    def crateri_(scala, raggio, seme):
        vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.voronoi_dimensions = '3D'; vo.feature = 'F1'
        vo.inputs['Scale'].default_value = scala; vo.inputs['Randomness'].default_value = 1.0
        off = nt.nodes.new('ShaderNodeVectorMath'); off.operation = 'ADD'; off.inputs[1].default_value = (seme, seme * 0.7, seme * 1.3)    # un «seme» diverso per ogni famiglia di crateri
        nt.links.new(gen, off.inputs[0]); nt.links.new(off.outputs['Vector'], vo.inputs['Vector']); d = vo.outputs['Distance']
        buco = mat('SUBTRACT', 1.0, liscia(d, raggio * 0.2, raggio * 0.85))                 # 1 al centro, 0 fuori
        bordo = mat('MULTIPLY', liscia(d, raggio * 0.7, raggio * 0.9), mat('SUBTRACT', 1.0, liscia(d, raggio * 0.9, raggio * 1.25)))
        return buco, bordo
    b1, r1 = crateri_(6.5, 0.20, 0.0); b2, r2 = crateri_(17.0, 0.20, 3.0); b3, r3 = crateri_(40.0, 0.18, 7.0)
    chiaro = mat('MULTIPLY', mat('SUBTRACT', 1.0, mat('MULTIPLY', mare, mari)), 1.0)
    scuro = mat('SUBTRACT', 1.0, mat('ADD', mat('ADD', mat('MULTIPLY', b1, crateri), mat('MULTIPLY', b2, crateri * 0.7)), mat('MULTIPLY', b3, crateri * 0.5)))
    luce = mat('ADD', mat('MULTIPLY', mat('ADD', mat('ADD', r1, mat('MULTIPLY', r2, 0.6)), mat('MULTIPLY', r3, 0.4)), 0.22), 1.0)
    val = mat('MULTIPLY', mat('MULTIPLY', chiaro, scuro), luce)
    # bordo del disco più scuro (la sfera vista di faccia)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    bordo_disco = mat('ADD', 0.80, mat('MULTIPLY', lw.outputs['Facing'], 0.30))
    val = mat('MULTIPLY', val, bordo_disco)
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'
    col.inputs['A'].default_value = (caldo[0] * 0.85, caldo[1] * 0.88, caldo[2] * 1.0, 1); col.inputs['B'].default_value = tuple(caldo) + (1,)
    nt.links.new(val, col.inputs['Factor'])
    nt.links.new(col.outputs['Result'], em.inputs['Color']); mu = mat('MULTIPLY', val, forza); nt.links.new(mu, em.inputs['Strength'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m


def luna_grande(cam, centro, n, raggio=19.0, su=1.0, forza=0.62, vecchia=None):
    """Crea il disco, toglie la luna liscia (`vecchia`, se data) e la chiava lungo la retta camera → centro(f) per f = 1..n."""
    sc = bpy.context.scene
    if vecchia is not None: bpy.data.objects.remove(vecchia, do_unlink=True)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R_LUNA * math.tan(math.radians(raggio)), segments=96, ring_count=48, location=(0, 0, 0))
    o = bpy.context.object; o.name = 'luna_grande'
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(materiale_luna(forza))
    o.visible_shadow = False; o.visible_glossy = False
    k = o.constraints.new('TRACK_TO'); k.target = cam; k.track_axis = 'TRACK_Z'; k.up_axis = 'UP_Y'
    for f in range(1, n + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        c = cam.matrix_world.translation.copy(); d = (Vector(centro(f)) - c).normalized()
        su_v = Vector((0, 0, 1)) - d * d.z; su_v.normalize()                          # «su» sullo schermo = il verticale del mondo, perpendicolare alla visuale
        dd = (d + su_v * math.tan(math.radians(su))).normalized()
        o.location = c + dd * R_LUNA; o.keyframe_insert('location', frame=f)
    return o
