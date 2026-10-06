# Fotografa piante Poly Haven per il gioco (vedi assets/alberi/CREDITI.md). Due modi:
#
#   impostore  — ogni oggetto scelto da 8 lati, un atlante orizzontale per oggetto (come
#                tools/fotografa-alberi.py, ma con la misura del fotogramma a scelta: le
#                latifoglie sono larghe quanto alte, i cespugli più larghi che alti)
#      blender -b --python tools/fotografa-piante.py -- impostore <modello.gltf> <uscita> <prefisso> <W> <H> <oggetto,oggetto,...>
#
#   ciuffi     — un fotogramma di fianco per ogni oggetto, tutti in un atlante a griglia
#                (erba e fiori del prato: nel gioco sono rettangoli incrociati)
#      blender -b --python tools/fotografa-piante.py -- ciuffi <uscita.png> <lato cella> <colonne> <modello.gltf:oggetto> ...
#
# Stampa ATLANTE/CELLA con le misure (metri) che servono al gioco per poggiarli a terra.
import bpy, sys, math, os
import numpy as np
from mathutils import Vector

arg = sys.argv[sys.argv.index('--') + 1:]
modo = arg[0]

def scena():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for e in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try: sc.render.engine = e; break
        except Exception: pass
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    try: sc.eevee.taa_render_samples = 32
    except Exception: pass
    sc.view_settings.view_transform = 'Standard'      # colori "piatti": il tone mapping lo fa il gioco
    w = bpy.data.worlds.new('mondo'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.62, 0.68, 0.74, 1); bg.inputs[1].default_value = 0.9
    sole = bpy.data.objects.new('sole', bpy.data.lights.new('sole', 'SUN')); sole.data.energy = 2.4
    sc.collection.objects.link(sole)                  # dritto dall'alto: uguale da ogni lato
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); cam.data.type = 'ORTHO'
    sc.collection.objects.link(cam); sc.camera = cam
    return sc, cam

def scatola(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx

def scatta(sc, cam, c, a, W, H, f):
    cam.location = (c.x + math.sin(a) * 60, c.y - math.cos(a) * 60, c.z)
    cam.rotation_euler = (math.pi / 2, 0, a)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    sc.render.filepath = f; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(f); px = np.array(im.pixels[:]).reshape(H, W, 4); bpy.data.images.remove(im)
    return px

def salva(px, f):
    H, W = px.shape[:2]
    img = bpy.data.images.new(os.path.basename(f), W, H, alpha=True)
    img.pixels = px.ravel(); img.filepath_raw = f; img.file_format = 'PNG'; img.save()

if modo == 'impostore':
    src, out, pref, W, H, nomi = arg[1], arg[2], arg[3], int(arg[4]), int(arg[5]), arg[6].split(',')
    VISTE = 8
    sc, cam = scena()
    bpy.ops.import_scene.gltf(filepath=src)
    os.makedirs(out, exist_ok=True)
    tutti = [o for o in bpy.data.objects if o.type == 'MESH']
    for lettera, nome in zip('abcdefgh', nomi):
        o = bpy.data.objects[nome]
        for p in tutti: p.hide_render = (p is not o)
        mn, mx = scatola(o)
        c = (mn + mx) / 2; alto = mx.z - mn.z; largo = math.hypot(mx.x - mn.x, mx.y - mn.y) * 0.85
        # Blender misura l'ortografica sul lato lungo del fotogramma
        if H >= W: cam.data.ortho_scale = max(alto, largo * H / W) * 1.04; orto_v = cam.data.ortho_scale
        else: cam.data.ortho_scale = max(largo, alto * W / H) * 1.04; orto_v = cam.data.ortho_scale * H / W
        fogli = [scatta(sc, cam, c, k / VISTE * 2 * math.pi, W, H, os.path.join(out, f'_{pref}_{lettera}_{k}.png')) for k in range(VISTE)]
        salva(np.concatenate(fogli, axis=1), os.path.join(out, f'{pref}_{lettera}.png'))
        print('ATLANTE', pref, lettera, nome, 'alto_m', round(alto, 3), 'ortho', round(orto_v, 3),
              'base', round(mn.z - (c.z - orto_v / 2), 3))

elif modo == 'ciuffi':
    out, L, COL, voci = arg[1], int(arg[2]), int(arg[3]), arg[4:]
    righe = math.ceil(len(voci) / COL)
    atl = np.zeros((righe * L, COL * L, 4))
    sc, cam = scena()
    caricati = {}
    for n, voce in enumerate(voci):
        src, nome = voce.split(':')
        if src not in caricati:
            bpy.ops.import_scene.gltf(filepath=src)
            caricati[src] = True
        tutti = [o for o in bpy.data.objects if o.type == 'MESH']
        o = bpy.data.objects[nome]
        for p in tutti: p.hide_render = (p is not o)
        mn, mx = scatola(o)
        c = (mn + mx) / 2; alto = mx.z - mn.z; largo = max(mx.x - mn.x, mx.y - mn.y)
        cam.data.ortho_scale = max(alto, largo) * 1.04
        px = scatta(sc, cam, c, 0.0, L, L, os.path.join(os.path.dirname(out) or '.', f'_ciuffo_{n}.png'))
        # pixels di Blender partono dal basso: la riga 0 della griglia va in alto nell'immagine
        r, k = n // COL, n % COL
        atl[(righe - 1 - r) * L:(righe - r) * L, k * L:(k + 1) * L] = px
        print('CELLA', n, nome, 'alto_m', round(alto, 3), 'ortho', round(cam.data.ortho_scale, 3),
              'base', round(mn.z - (c.z - cam.data.ortho_scale / 2), 3))
    salva(atl, out)
