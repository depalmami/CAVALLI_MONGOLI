# LE POSE per gli shot del trailer: chi si muove e come, in un solo fotogramma.
#   eroe()   il protagonista dal rig del trailer (trailer/blender/rig/protagonista-trailer.blend, fatto da rig.py): una clip di
#            corpo (Gallop/Walk/Idle/Salto) + una clip di braccio (Sciabola_Fendente, Sciabola_Alta, Frusta, Afferra) + uno
#            sguardo (Sguardo_D/S, sommato), e l'arma impugnata nell'osso presa.R. La posa si cuoce in mesh statica.
#   boss()   il coccodrillo: 14 gambe che marciano (all'unisono, come una parata, o sfalsate come nel gioco), la mascella, la
#            testa che si gira o si alza, il corpo che sobbalza a ogni passo.
#   birra()  il bicchiere sui pattini a una fase della spinta (la formula di 3d/birra.js, con l'ampiezza che si può esagerare).
# Tutti prendono `fase` o il fotogramma: per l'animazione vera basta chiamarli fotogramma per fotogramma (o chiavarne i valori).
import bpy, math, os
from mathutils import Vector, Matrix
import animatic as AN

RIG = os.path.abspath(os.path.join(AN.QUI, '..', '..', 'trailer', 'blender', 'rig', 'protagonista-trailer.blend'))
LUNGO = dict(saber=0.85, mace=0.60, whip=1.00, bow=0.95)          # come POSE[k].lungo in 3d/armi.js (m nativi)

def _nla(rig, strati, F=500):
    """strati = [(azione, fotogramma della clip, blend)]: ogni clip si mette nell'NLA in modo che al fotogramma di scena F
    valga il suo fotogramma voluto."""
    ad = rig.animation_data or rig.animation_data_create()
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    ad.action = None
    for act, fr, modo in strati:
        tr = ad.nla_tracks.new(); tr.name = act.name
        st = tr.strips.new(act.name, int(round(F - (fr - act.frame_range[0]))), act)
        st.blend_type = modo; st.extrapolation = 'HOLD'
        if hasattr(st, 'action_slot') and len(getattr(act, 'slots', [])): st.action_slot = act.slots[0]
    bpy.context.scene.frame_set(F); bpy.context.view_layer.update()

def eroe(pos=(0, 0, 0), yaw=0.0, corpo=('Gallop', 6), braccio=None, sguardo=None, arma=None, arma_giro=0.0,
         rot=(0, 0, 0), nome='eroe'):
    """corpo/braccio/sguardo = (clip, fotogramma) o None. arma = saber/mace/whip/bow. Ritorna (radice, info) con
    info['presa'] (matrice mondo dell'impugnatura) e info['punta'] (punta dell'arma, mondo), utili per scintille e luci."""
    sc = bpy.context.scene
    with bpy.data.libraries.load(RIG, link=False) as (src, dst):
        dst.objects = ['CavalloCartone', 'CavalloCartone_rig']
        dst.actions = list(src.actions)
        nomi_azioni = list(src.actions)
    azioni = dict(zip(nomi_azioni, dst.actions))
    horse, rig = dst.objects
    for o in (horse, rig): sc.collection.objects.link(o)
    strati = []
    if corpo: strati.append((azioni[corpo[0]], corpo[1], 'REPLACE'))
    if braccio: strati.append((azioni[braccio[0]], braccio[1], 'REPLACE'))
    if sguardo: strati.append((azioni[sguardo[0]], sguardo[1], 'COMBINE'))
    _nla(rig, strati)
    presa = rig.pose.bones['presa.R'].matrix.copy()            # spazio del modello (rig nell'origine)
    th = rig.pose.bones['DEF-head']; testa = (th.head.copy(), th.tail.copy())     # nuca → muso
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(horse.evaluated_get(dg))
    radice = bpy.data.objects.new(nome, None); sc.collection.objects.link(radice)
    corpo_o = bpy.data.objects.new(nome + '_corpo', me); sc.collection.objects.link(corpo_o); corpo_o.parent = radice
    for o in (horse, rig): bpy.data.objects.remove(o)
    for a in azioni.values():
        if a.users == 0 or a.use_fake_user: a.use_fake_user = False
    AN.metti(radice, pos, yaw, 1.0, rot)
    bpy.context.view_layer.update()
    Wm = radice.matrix_world
    info = {'nuca': Wm @ testa[0], 'muso': Wm @ testa[1]}
    if arma:
        a, _ = AN.importa('models/armi/%s.glb' % arma, nome='arma_' + arma)
        bpy.context.view_layer.update()
        zz = [(a.matrix_world.inverted() @ (o.matrix_world @ Vector(c))).z for o in a.children for c in o.bound_box]
        k = LUNGO[arma] / max(1e-3, max(zz) - min(zz))
        a.parent = radice
        # il GLB ha la lunghezza su +Y glTF = +Z di Blender: Rx(-90°) la porta sulla Y della presa
        a.matrix_parent_inverse = Matrix.Identity(4)
        a.matrix_basis = presa @ Matrix.Rotation(arma_giro, 4, 'Y') @ Matrix.Rotation(-math.pi / 2, 4, 'X') @ Matrix.Scale(k, 4)
        bpy.context.view_layer.update()
        info['presa'] = radice.matrix_world @ presa
        info['punta'] = radice.matrix_world @ (presa @ Vector((0, LUNGO[arma] * 0.92, 0)))
    else:
        info['presa'] = radice.matrix_world @ presa
    return radice, info

def eroe_vivo(nome='eroe'):
    """Il protagonista VIVO per gli shot animati: rig + mesh del trailer appesi a una radice (Empty) da chiavare per posizione e
    giro, e le clip pronte. Ritorna (radice, rig, azioni). Le clip si mettono nell'NLA del rig con traccia() e si guidano con
    chiavi sul tempo e sull'influenza delle strisce."""
    sc = bpy.context.scene
    with bpy.data.libraries.load(RIG, link=False) as (src, dst):
        dst.objects = ['CavalloCartone', 'CavalloCartone_rig']
        dst.actions = list(src.actions)
        nomi_azioni = list(src.actions)
    azioni = dict(zip(nomi_azioni, dst.actions))
    horse, rig = dst.objects
    for o in (horse, rig): sc.collection.objects.link(o)
    radice = bpy.data.objects.new(nome, None); sc.collection.objects.link(radice)
    rig.parent = radice
    ad = rig.animation_data or rig.animation_data_create()
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    ad.action = None
    return radice, rig, azioni

def traccia(rig, act, modo='REPLACE', nome=None):
    """Una striscia NLA con tempo e influenza chiavabili (use_animated_time / use_animated_influence)."""
    ad = rig.animation_data
    tr = ad.nla_tracks.new(); tr.name = nome or act.name
    st = tr.strips.new(nome or act.name, int(act.frame_range[0]), act)
    st.blend_type = modo; st.extrapolation = 'HOLD'
    if hasattr(st, 'action_slot') and len(getattr(act, 'slots', [])): st.action_slot = act.slots[0]
    st.use_animated_time = True; st.use_animated_influence = True
    return st

def arma_viva(rig, arma, giro=0.0):
    """L'arma figlia dell'osso presa.R del rig vivo: segue la mano in ogni fotogramma. Ritorna la radice dell'arma."""
    a, _ = AN.importa('models/armi/%s.glb' % arma, nome='arma_' + arma)
    bpy.context.view_layer.update()
    zz = [(a.matrix_world.inverted() @ (o.matrix_world @ Vector(c))).z for o in a.children for c in o.bound_box]
    k = LUNGO[arma] / max(1e-3, max(zz) - min(zz))
    lung = rig.data.bones['presa.R'].length
    a.parent = rig; a.parent_type = 'BONE'; a.parent_bone = 'presa.R'
    # il figlio di un osso parte dalla CODA dell'osso: si torna alla testa e si gira la lunghezza del GLB (+Z) sulla Y dell'osso
    a.matrix_parent_inverse = Matrix.Translation((0, -lung, 0)) @ Matrix.Rotation(giro, 4, 'Y') @ Matrix.Rotation(-math.pi / 2, 4, 'X') @ Matrix.Scale(k, 4)
    a.location = (0, 0, 0); a.rotation_euler = (0, 0, 0); a.scale = (1, 1, 1)
    return a

# ------------------------------------------------------------------------------------------------------------------ il Boss
def boss(pos=(0, 0, 0), yaw=0.0, scala=1.35, **kw):
    """Il Boss in una posa (vedi boss_posa per fase, passo, unisono, mascella, testa, alza, sobbalzo, ginocchio, fuori, alto)."""
    radice, pz, base = boss_crea()
    boss_posa(pz, base, **kw)
    AN.metti(radice, pos, yaw, scala)
    return radice

def boss_crea(nome='boss'):
    """Importa il coccodrillo tenendo la gerarchia dei pezzi: (radice, pezzi per nome, trasformazioni di riposo)."""
    sc = bpy.context.scene
    prima = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=AN.A + 'models/boss/coccodrillo.glb')
    nuovi = [o for o in bpy.data.objects if o not in prima]
    for o in list(nuovi):
        if o.name.startswith('Icosphere'): bpy.data.objects.remove(o); nuovi.remove(o)
    radice = bpy.data.objects.new(nome, None); sc.collection.objects.link(radice)
    pz = {}
    for o in nuovi:
        if o.parent is None: o.parent = radice
        o.rotation_mode = 'XYZ'; pz[o.name.split('.')[0]] = o
    base = {k: (o.location.copy(), o.rotation_euler.copy(), o.scale.copy()) for k, o in pz.items()}
    return radice, pz, base

def boss_posa(pz, base, fase=0.0, passo=1.0, unisono=True, mascella=0.0, testa=0.0, alza=0.0, sobbalzo=0.0, ginocchio=1.0,
              fuori=None, alto=0.0, saltello=None, chiave=None):
    """fase: 0..1 = un ciclo del passo (sinistre avanti a 0,25, destre a 0,75). passo: ampiezza (1 = come nel gioco).
    unisono=True: tutte le sinistre insieme e tutte le destre insieme (la parata); False: sfalsate come in 3d/boss.js.
    mascella, testa (giro a sinistra +), alza (muso in su): gradi. fuori = {nome coscia: sfasamento in giri}, per la gamba che
    va fuori passo (es. {'Coscia_S2_D': 0.5}); saltello = {nome coscia: m} la alza (il saltello per rientrare in passo).
    alto = impennato (m del modello): come in 3d/boss.js il corpo sale e le cosce si allungano a trampolo, i piedi restano a terra.
    chiave = fotogramma: chiava tutti i pezzi (per gli shot animati)."""
    for k, o in pz.items():
        l, r, s_ = base[k]; o.location = l.copy(); o.rotation_euler = r.copy(); o.scale = s_.copy()
    trova = lambda pref: sorted((o for k, o in pz.items() if k.startswith(pref)), key=lambda o: o.name)
    ph = 2 * math.pi * fase
    for i, c in enumerate(trova('Coscia_')):
        nome = c.name.split('.')[0]
        destra = nome.endswith('_D')
        f = ph + (math.pi if destra else 0.0) + (0.0 if unisono else i * 1.9) + 2 * math.pi * (fuori or {}).get(nome, 0.0)
        s = math.sin(f)
        c.rotation_euler = (0, -0.62 * passo * s, 0)                                   # + = il piede va avanti (+X)
        c.location.z += (saltello or {}).get(nome, 0.0)
        st = next((x for x in c.children if x.name.startswith('Stinco_')), None)
        if st:
            if unisono:
                # passo vero: in appoggio (la coscia va indietro, cos f < 0) la gamba è tesa e il piede resta a terra; in volo il
                # ginocchio si piega e si distende prima di appoggiare. Il gioco invece piega in appoggio: corre, non marcia.
                if math.cos(f) > 0:
                    u = ((f + math.pi / 2) % (2 * math.pi)) / math.pi
                    piega = 0.05 + ginocchio * 1.1 * math.sin(math.pi * u) ** 1.3 * (1 - 0.35 * u)
                else:
                    piega = 0.05
                st.rotation_euler = (0, piega * min(passo, 1.3), 0)
            else:
                st.rotation_euler = (0, (0.12 + ginocchio * max(0.0, math.sin(f - 1.1))) * passo, 0)     # il ginocchio piega indietro
    # sobbalzo: con le gambe aperte l'anca scende (gamba d'appoggio tesa, lunga ~1,2 m nel modello: 1,2·(1 − cos θ)), così i
    # piedi restano a terra; all'unisono tutte le cosce hanno lo stesso |θ|. sobbalzo aggiunge un tonfo sul passo.
    th = 0.62 * passo * abs(math.sin(ph)) if unisono else 0.0
    dz = -1.2 * (1 - math.cos(th)) - sobbalzo * passo * abs(math.sin(ph))
    for o in trova('Spicchio') + trova('Coda') + trova('Testa'):
        o.location.z += dz + alto
    if alto:
        for c in trova('Coscia_'): c.scale.z *= 1 + alto / 1.2
    for o in trova('Spicchio'):
        o.rotation_euler.x += 0.025 * passo * math.sin(ph)                             # rollio del passo
    t = next(o for k, o in pz.items() if k.startswith('Testa'))
    t.rotation_euler = (0, -math.radians(alza), math.radians(testa))
    for o in trova('Mascella'):
        o.rotation_euler = (0, math.radians(mascella), 0)
    if chiave is not None:
        for o in pz.values():
            o.keyframe_insert('location', frame=chiave); o.keyframe_insert('rotation_euler', frame=chiave); o.keyframe_insert('scale', frame=chiave)

def boss_velocita(passo=1.0, ciclo=24, scala=1.35):
    """m per fotogramma a cui deve avanzare la radice perché i piedi in appoggio non scivolino (un appoggio = mezzo ciclo)."""
    return 2 * 1.2 * math.sin(0.62 * passo) * scala / (ciclo / 2)

# ------------------------------------------------------------------------------------------------------------------ la Birra
def birra(pos=(0, 0, 0), yaw=0.0, scala=2.0, fase=0.0, forza=1.6, piega=0.0):
    """fase 0..1 = una spinta a destra e una a sinistra. forza esagera il passo del gioco; piega = inclinazione nella curva
    (gradi, + verso sinistra). Assi del modello in Blender: +X davanti, Z su, -Y destra."""
    radice, pezzo, base = birra_crea()
    birra_posa(pezzo, base, fase, forza, piega)
    AN.metti(radice, pos, yaw, scala)
    return radice

def birra_crea(nome='birra'):
    """Importa la birra: (radice, pezzi, posizioni di riposo dei pezzi)."""
    sc = bpy.context.scene
    prima = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=AN.A + 'models/birra/birra.glb')
    nuovi = [o for o in bpy.data.objects if o not in prima]
    radice = bpy.data.objects.new(nome, None); sc.collection.objects.link(radice)
    pezzo = {}
    for o in nuovi:
        if o.parent is None: o.parent = radice
        pezzo[o.name.split('.')[0]] = o; o.rotation_mode = 'XYZ'
    return radice, pezzo, {k: o.location.copy() for k, o in pezzo.items()}

def birra_posa(pezzo, base, fase, forza=1.6, piega=0.0, chiave=None):
    """Mette i tre pezzi nella fase della spinta (dalle posizioni di riposo `base`); chiave = fotogramma per chiavarli."""
    ph = 2 * math.pi * fase; s, c = math.sin(ph), math.cos(ph); F = forza
    for nome, segno in (('PattinoS', 1), ('PattinoD', -1)):
        o = pezzo[nome]; su = max(0.0, segno * c)
        o.location = base[nome] + Vector((0.075 * segno * s * F, segno * 0.02 * max(0.0, -segno * s) * F, 0.03 * su * F))   # in spinta va appena in fuori
        o.rotation_euler = (0, -(0.2 * segno * s + 0.12 * su) * min(F, 1.3), 0)
    b = pezzo['Bicchiere']
    b.location = base['Bicchiere'] + Vector((0, 0, 0.007 * math.sin(2 * ph) * F))
    b.rotation_euler = (0.05 * s * F + math.radians(piega), 0.07 + 0.015 * abs(c) * F, 0.06 * c)
    if chiave is not None:
        for o in pezzo.values():
            o.keyframe_insert('location', frame=chiave); o.keyframe_insert('rotation_euler', frame=chiave)

def bocca(radice):
    """Punto davanti alla bocca del Boss (mondo): la punta della mascella, per polvere, vapore, luci."""
    bpy.context.view_layer.update()
    m = next(o for o in radice.children_recursive if o.name.startswith('Mascella'))
    pts = [m.matrix_world @ Vector(c) for c in m.bound_box]
    asse = (radice.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()          # la testa guarda +X
    return max(pts, key=lambda p: p.dot(asse))

def tinta_smorzata(h, quanto=0.5):
    """Le tinte dei predoni del gioco, smorzate per il trailer: metà saturazione, più scure e un velo di polvere."""
    c = AN.hexc(h)[:3]; l = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    polv = (0.42, 0.35, 0.27)
    return tuple(((x + (l - x) * quanto) * 0.72) * 0.8 + p * 0.2 for x, p in zip(c, polv))
