# FUMO PROCEDURALE (24 nov): il fiato del Boss (S23) e la tosse (S26) come VOLUME in EEVEE, senza simulazione.
# Prima erano una dozzina di sfere emissive con l'alfa fissa: dischi piatti, col bordo a poligoni, più chiari della notte intorno.
# Ora un getto di gas: un cono che si allarga, si piega verso l'alto col calore, con dentro un rumore 4D turbolento che scorre
# lungo il getto. Il fronte parte dalla bocca e rallenta, la coda lo insegue quando l'esalazione finisce, e il fumo prende la luce
# di una lampada che illumina SOLO lui (light linking), perché di notte la luna da sola non lo accende.
#
# Perché non Mantaflow: provato (Blender 5.1, `-b`), il bake ignora le animazioni dell'emettitore (posizione, scala, visibilità,
# use_inflow): la sorgente resta dove stava al fotogramma 1 e il gas non si muove. Il volume procedurale invece è deterministico,
# segue la bocca a chiavi e non scalda il Mac con una cottura.
#
#   soffio(origine, direzione, f_on, f_off, n, ...)   crea il volume, ritorna il suo oggetto
#       origine(f) -> posizione mondo della bocca al fotogramma f       (il volume la segue, chiave per chiave)
#       direzione  -> verso del getto in mondo (si normalizza)          (è una sola per tutto lo shot)
#       f_on, f_off -> primo e ultimo fotogramma dell'esalazione
import bpy, math
from mathutils import Vector


def _imposta(obj, nome, val):
    try: setattr(obj, nome, val)
    except Exception as e: print('FUMO: %s non impostabile (%s)' % (nome, str(e)[:60]))


class _Nodi:
    """Un piccolo costruttore di nodi: ogni metodo ritorna il socket di uscita, e accetta numeri o socket."""
    def __init__(s, nt): s.nt = nt

    def _in(s, sock, v):
        if hasattr(v, 'node'): s.nt.links.new(v, sock)
        elif v is not None: sock.default_value = v

    def m(s, op, a, b=None, c=None, clamp=False):
        n = s.nt.nodes.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, b, c)): s._in(n.inputs[i], v)
        return n.outputs[0]

    def v(s, op, a, b=None, scala=None, esci='Vector'):
        n = s.nt.nodes.new('ShaderNodeVectorMath'); n.operation = op
        s._in(n.inputs[0], a)
        if b is not None: s._in(n.inputs[1], b)
        if scala is not None: s._in(n.inputs['Scale'], scala)
        return n.outputs[esci]

    def liscia(s, x, da, a):
        """smoothstep(da, a, x) → 0..1 (da e a possono essere socket)."""
        n = s.nt.nodes.new('ShaderNodeMapRange'); n.interpolation_type = 'SMOOTHSTEP'; n.clamp = True
        s._in(n.inputs['Value'], x); s._in(n.inputs['From Min'], da); s._in(n.inputs['From Max'], a)
        n.inputs['To Min'].default_value = 0.0; n.inputs['To Max'].default_value = 1.0
        return n.outputs['Result']


def materiale_soffio(d, f_on, f_off, velocita, r0, apertura, sale, grana, densita, lunghezza, colore, anisotropia, fps=24.0,
                     deriva=1.6, taglio=0.9, spegni=1.0):
    m = bpy.data.materials.new('fumo'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = _Nodi(nt)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); pv = nt.nodes.new('ShaderNodeVolumePrincipled')
    pv.inputs['Color'].default_value = tuple(colore) + (1,); pv.inputs['Anisotropy'].default_value = anisotropia
    d = Vector(d).normalized(); t_on, t_off = f_on / fps, f_off / fps
    # il tempo, in secondi: un valore che segue il fotogramma
    tv = nt.nodes.new('ShaderNodeValue'); fc = tv.outputs[0].driver_add('default_value')
    fc.driver.type = 'SCRIPTED'; fc.driver.expression = 'frame/%g' % fps; t = tv.outputs[0]
    P = nt.nodes.new('ShaderNodeTexCoord').outputs['Object']                     # coordinate relative alla bocca (il volume non ruota né scala)
    # asse del getto e curvatura verso l'alto (il calore): z -= sale·s²
    s0 = N.v('DOT_PRODUCT', P, tuple(d), esci='Value')
    sp = N.m('MAXIMUM', s0, 0.0)
    dz = N.m('MULTIPLY', N.m('MULTIPLY', sp, sp), sale)
    cz = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(dz, cz.inputs['Z'])
    P2 = N.v('SUBTRACT', P, cz.outputs[0])
    s = N.v('DOT_PRODUCT', P2, tuple(d), esci='Value')
    lat = N.v('SUBTRACT', P2, N.v('SCALE', tuple(d), scala=s))
    rho = N.v('LENGTH', lat, esci='Value')
    # il getto nel tempo: il fronte (rallenta) e la coda (parte quando l'esalazione finisce)
    te = N.m('MAXIMUM', N.m('SUBTRACT', t, t_on), 0.0)
    tb = N.m('MAXIMUM', N.m('SUBTRACT', t, t_off), 0.0)
    fronte = N.m('MULTIPLY', N.m('POWER', te, 0.75), velocita)
    coda = N.m('SUBTRACT', N.m('MULTIPLY', N.m('POWER', tb, 0.75), velocita), 0.25)
    wf = N.m('MULTIPLY', N.liscia(s, coda, N.m('ADD', coda, 0.7)),
             N.m('SUBTRACT', 1.0, N.liscia(s, N.m('SUBTRACT', fronte, 1.0), N.m('ADD', fronte, 0.15))))
    # la sezione: un cono che si allarga con la distanza e con il tempo, denso al centro
    R = N.m('ADD', N.m('ADD', r0, N.m('MULTIPLY', sp, apertura)), N.m('MULTIPLY', te, 0.22))
    radiale = N.m('POWER', N.m('SUBTRACT', 1.0, N.m('DIVIDE', rho, R), clamp=True), 1.3)
    lungo = N.m('POWER', 2.718, N.m('DIVIDE', N.m('MULTIPLY', sp, -1.0), lunghezza))   # si dirada allontanandosi dalla bocca
    # il rumore: scorre lungo il getto e sale, con distorsione propria (i riccioli)
    scorre = N.v('SCALE', tuple(d), scala=N.m('MULTIPLY', t, deriva))
    su = N.v('SCALE', (0, 0, 1), scala=N.m('MULTIPLY', t, 0.35))
    Pn = N.v('SUBTRACT', N.v('SUBTRACT', P2, scorre), su)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'
    nz.inputs['Scale'].default_value = grana; nz.inputs['Detail'].default_value = 8.0; nz.inputs['Roughness'].default_value = 0.6
    nz.inputs['Distortion'].default_value = 0.9
    nt.links.new(Pn, nz.inputs['Vector']); nt.links.new(N.m('MULTIPLY', t, 0.6), nz.inputs['W'])
    nf = N.liscia(nz.outputs['Fac'], 0.32, 0.70)                              # il rumore, stirato a tutto il contrasto
    nucleo = N.m('SUBTRACT', N.m('MULTIPLY', radiale, 1.25), N.m('MULTIPLY', N.m('SUBTRACT', 1.0, nf), taglio), clamp=True)
    sparisci = N.m('SUBTRACT', 1.0, N.liscia(t, t_off + 0.4, t_off + 0.4 + spegni))     # il resto si dissolve dopo la coda
    dens = N.m('MULTIPLY', N.m('MULTIPLY', nucleo, wf), N.m('MULTIPLY', N.m('ADD', 0.35, N.m('MULTIPLY', lungo, 0.65)), sparisci))
    nt.links.new(N.m('MULTIPLY', dens, densita), pv.inputs['Density'])
    nt.links.new(pv.outputs['Volume'], out.inputs['Volume'])
    return m


def soffio(origine, direzione, f_on, f_off, n, nome='fumo', velocita=5.0, r0=0.25, apertura=0.22, sale=0.10, grana=2.4,
           densita=2.0, lunghezza=4.0, colore=(0.80, 0.85, 0.95), anisotropia=0.35, scatola=(8.0, 6.0, 6.0), deriva=1.6,
           taglio=0.9, spegni=1.0, luce=None):
    """Il volume è una scatola grande `scatola` m centrata davanti alla bocca; ha il materiale e segue `origine(f)` a chiavi."""
    sc = bpy.context.scene; d = Vector(direzione).normalized()
    me = bpy.data.meshes.new(nome); o = bpy.data.objects.new(nome, me); sc.collection.objects.link(o)
    sx, sy, sz = scatola; c = d * (sx * 0.38) + Vector((0, 0, sz * 0.22))                  # la scatola sta davanti alla bocca, un po' in alto
    vv = [(c.x + a * sx / 2, c.y + b * sy / 2, c.z + e * sz / 2) for a in (-1, 1) for b in (-1, 1) for e in (-1, 1)]
    ff = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(vv, [], ff); me.update()
    o.data.materials.append(materiale_soffio(d, f_on, f_off, velocita, r0, apertura, sale, grana, densita, lunghezza, colore,
                                             anisotropia, sc.render.fps, deriva, taglio, spegni))
    prima = sc.frame_current
    for f in range(1, n + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        o.location = origine(f); o.keyframe_insert('location', frame=f)
    sc.frame_set(prima)
    o.visible_shadow = False
    if luce: luce_del_fumo(o, *luce, nome=nome)
    return o


def luce_del_fumo(vol, verso, forza=4.0, colore=(0.75, 0.85, 1.0), nome='fumo'):
    """Una luce che illumina SOLO il fumo (light linking): di notte il fumo preso dalla sola luna è invisibile, ma una luce vera
    sulla scena cambierebbe il resto. `verso` = direzione in cui viaggia la luce (dal retro verso la camera: il fumo si accende
    di controluce, come il fiato nel freddo)."""
    sc = bpy.context.scene
    l = bpy.data.lights.new(nome + '_luce', 'SUN'); l.energy = forza; l.color = colore; l.angle = math.radians(6)
    o = bpy.data.objects.new(nome + '_luce', l); sc.collection.objects.link(o)
    o.rotation_euler = Vector(verso).normalized().to_track_quat('-Z', 'Y').to_euler()
    coll = bpy.data.collections.new(nome + '_riceve'); coll.objects.link(vol)
    o.light_linking.receiver_collection = coll
    return o


def eevee_volume(finale=True):
    """Qualità del volume in EEVEE (celle più grosse in prova: il fumo è morbido e sfocato comunque)."""
    e = bpy.context.scene.eevee
    for nome, val in (('volumetric_tile_size', '4' if finale else '8'), ('volumetric_samples', 64 if finale else 32),
                      ('use_volumetric_shadows', False), ('volumetric_end', 40.0), ('volumetric_sample_distribution', 0.8)):
        _imposta(e, nome, val)
