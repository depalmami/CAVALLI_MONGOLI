# PREPARA UN'ARMA GENERATA (Meshy, Tripo...) PER IL GIOCO.
#
# I modelli generati arrivano con ~2 milioni di triangoli, 65 MB, sdraiati a caso e con l'origine nel centro. Questo script li
# porta alla CONVENZIONE di assets/models/armi/LEGGIMI.md: pochi triangoli, texture ridotte, impugnatura nell'ORIGINE,
# lunghezza lungo +Y (punta in su), faccia piatta verso la camera di corsa (che sta DIETRO il cavallo).
#
# Uso (Blender in background):
#   blender -b -P tools/armi/prepara-arma.py -- <entrata.glb> --scegli <cartella>
#       passo 1: salva una vista del pezzo con le due estremità A (rosso) e B (blu): guardala e decidi quale è l'impugnatura
#   blender -b -P tools/armi/prepara-arma.py -- <entrata.glb> <uscita.glb> --grip A|B --lungo 0.85 [--frac 0.2] [--asse impugnatura]
#                                                [--tris 20000] [--tex 1024] [--gira 180] [--anteprima <cartella>]
#       passo 2: decima, riorienta, sposta l'origine sull'impugnatura, riduce le texture, esporta il GLB
#
#   --cassa     per un oggetto senza lunghezza né impugnatura (la cassa-arma): nessun riorientamento, solo decimato, centrato nel suo
#               ingombro e portato a --lungo sul lato maggiore: blender -b -P ... -- cassa.glb <uscita.glb> --cassa --lungo 1 --tris 12000
#   --grip      quale estremità (A = proiezione minima sull'asse principale, B = massima) è l'impugnatura
#   --frac      dove si impugna, come frazione della lunghezza dall'estremità dell'impugnatura (0 = pomolo)
#   --asse      'tutto' (default): la lunghezza è l'asse principale di tutto il pezzo · 'impugnatura': l'asse del solo manico
#               (per le fruste, dove la corda si piega e la direzione estremo-estremo non è quella del manico)
#   --eje       (opzionale) frazione della lunghezza da cui prendere il centro LATERALE dell'impugnatura, quando attorno al manico
#               c'è qualcosa che lo sposta (l'anello della sciabola): una fetta "pulita", p.es. la base della lama
#   --gira      gradi di rotazione attorno alla lunghezza (180 = scambia il lato del filo e quello del dorso)
#   --lungo     altezza finale in m nativi (pomolo→punta): la stessa di POSE[chiave].lungo in 3d/armi.js
#
# Convenzione di uscita (Blender, Z in su; l'esportatore la porta a Y in su): L → +Z (poi +Y glTF), piatto → -Y (poi +Z glTF = verso
# la camera/il bersaglio), dorso/filo → -X.

import bpy, sys, os, argparse, math
import numpy as np
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('entrata'); ap.add_argument('uscita', nargs='?')
ap.add_argument('--tris', type=int, default=20000)
ap.add_argument('--tex', type=int, default=1024)
ap.add_argument('--lungo', type=float, default=1.0)
ap.add_argument('--asse', choices=['tutto', 'impugnatura'], default='tutto')
ap.add_argument('--grip', choices=['A', 'B'])
ap.add_argument('--frac', type=float, default=0.15)
ap.add_argument('--gira', type=float, default=0.0)
ap.add_argument('--eje', type=float, default=None)
ap.add_argument('--cassa', action='store_true')
ap.add_argument('--scegli')
ap.add_argument('--anteprima')
a = ap.parse_args(argv)
nome = os.path.splitext(os.path.basename(a.entrata))[0]


def triangoli(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def posizioni(ob):
    n = len(ob.data.vertices); co = np.empty(n * 3); ob.data.vertices.foreach_get('co', co); return co.reshape(n, 3)

def importa(f):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ob

def decima(ob, tris):
    n = triangoli(ob)
    if n <= tris: return
    m = ob.modifiers.new('d', 'DECIMATE'); m.ratio = tris / n
    m.delimit = {'UV'}                                        # non attraversa le cuciture UV: la texture resta intera
    bpy.ops.object.modifier_apply(modifier='d')

def scena(px=480):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x = sc.render.resolution_y = px
    sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
    w = bpy.data.worlds.new('w'); w.color = (0.55, 0.57, 0.62); sc.world = w
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.clip_end = 100
    return sc, cam

def pallino(pos, colore, r):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=pos, segments=12, ring_count=8)
    o = bpy.context.active_object
    m = bpy.data.materials.new('m'); m.diffuse_color = colore; o.data.materials.append(m)
    return o

def vista(sc, cam, centro, dir_, scala, up_hint=None):
    d = Vector(dir_).normalized(); cam.data.ortho_scale = scala
    cam.location = centro + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    p = os.path.join(bpy.app.tempdir, 'v.png'); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p); px = sc.render.resolution_x
    arr = np.array(im.pixels[:]).reshape(px, px, 4); bpy.data.images.remove(im); return arr

def foglio(arrs, percorso):
    f = np.hstack(arrs); h, w = f.shape[:2]
    im = bpy.data.images.new('foglio', w, h, alpha=True); im.pixels = f.flatten().tolist()
    im.filepath_raw = percorso; im.file_format = 'PNG'; im.save()


ob = importa(a.entrata)
n0 = triangoli(ob)
decima(ob, a.tris if not a.scegli else 40000)
print('ARMA', nome, 'triangoli', n0, '->', triangoli(ob), flush=True)

V = posizioni(ob); c = V.mean(0)
w, E = np.linalg.eigh(np.cov((V - c).T)); e1, e2, e3 = E[:, 2], E[:, 1], np.cross(E[:, 2], E[:, 1])
s = (V - c) @ e1; iA, iB = s.argmin(), s.argmax(); PA, PB = V[iA], V[iB]
dim = V.max(0) - V.min(0)

def chiudi(ctr, scala):
    """Texture ridotte, anteprima (se richiesta), rapporto ed esportazione del GLB."""
    for im in bpy.data.images:
        if im.size[0] > a.tex or im.size[1] > a.tex:
            f = a.tex / max(im.size); im.scale(max(1, int(im.size[0] * f)), max(1, int(im.size[1] * f)))
    if a.anteprima:
        sc, cam = scena(); pallino((0, 0, 0), (1, 0.1, 0.1, 1), 0.02)
        foglio([vista(sc, cam, ctr, (0, 1, 0), scala), vista(sc, cam, ctr, (1, 0, 0), scala), vista(sc, cam, ctr, (1, 1, 0.4), scala)],
               os.path.join(a.anteprima, nome + '-pronta.png'))
    V2 = posizioni(ob); mn, mx = V2.min(0), V2.max(0)
    print('   finale: triangoli', triangoli(ob), 'bbox Blender x,y,z', (mx - mn).round(3), 'min', mn.round(3), 'max', mx.round(3), flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.uscita)), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=a.uscita, export_format='GLB', export_image_format='AUTO', export_yup=True)
    print('   scritto', a.uscita, round(os.path.getsize(a.uscita) / 1048576, 2), 'MB')

if a.cassa:                                                    # un oggetto che non ha lunghezza né impugnatura (la cassa-arma): niente
    if not a.uscita: sys.exit('serve il file di uscita')       # riorientamento, resta com'è; solo centrato nel suo ingombro e portato
    mn, mx = V.min(0), V.max(0)                                # a "lungo" sul lato più grande (il gioco poi la scala in unità sue)
    ob.matrix_world = Matrix.Scale(a.lungo / (mx - mn).max(), 4) @ Matrix.Translation(Vector(-(mn + mx) / 2))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    chiudi(Vector((0, 0, 0)), a.lungo * 1.6)
    sys.exit(0)

if a.scegli:
    sc, cam = scena()
    pallino(PA, (1, 0.1, 0.1, 1), 0.035); pallino(PB, (0.1, 0.2, 1, 1), 0.035)
    # la vista guarda il pezzo lungo il suo "piatto" (e3): si vede la faccia larga e la curvatura
    d = Vector(e3);
    arr = vista(sc, cam, Vector(c), d, float(dim.max()) * 1.3)
    foglio([arr], os.path.join(a.scegli, nome + '-scegli.png'))
    print('   asse principale e1', e1.round(3), 'piatto e3', e3.round(3), 'A (rosso)', PA.round(3), 'B (blu)', PB.round(3), 'varianze', w.round(4))
    sys.exit(0)

if not a.grip or not a.uscita: sys.exit('serve --grip A|B e il file di uscita (prima fai --scegli)')
L = e1 if a.grip == 'A' else -e1                              # dall'impugnatura verso la punta
sL = (V - c) @ L
if a.asse == 'impugnatura':
    lung = sL.max() - sL.min()
    P = V[sL < sL.min() + 0.12 * lung]
    l2 = np.linalg.eigh(np.cov((P - P.mean(0)).T))[1][:, 2]
    L = l2 if l2 @ L > 0 else -l2
    sL = (V - c) @ L
T = e3 - (e3 @ L) * L; T /= np.linalg.norm(T)                 # normale del piatto, ortogonale alla lunghezza
Wv = np.cross(T, L)                                            # dal dorso al filo
th = math.radians(a.gira)
Wv, T = Wv * math.cos(th) + T * math.sin(th), -Wv * math.sin(th) + T * math.cos(th)
lung = sL.max() - sL.min()
sg = sL.min() + a.frac * lung
fetta = V[np.abs(sL - sg) < 0.03 * lung]                       # il punto d'impugnatura: nell'asse, a frac dalla fine
o = np.median(fetta, axis=0)                                   # ma la fetta prende anche l'anello della guardia, il cinturino...:
for _ in range(4):                                             # si cerca il centro del manico con una media che scarta chi sta lontano
    vicini = fetta[np.linalg.norm(fetta - o, axis=1) < 0.035 * lung / 0.85]
    if len(vicini): o = vicini.mean(0)
if a.eje is not None:                                          # se l'impugnatura è accompagnata da qualcosa che sporge (l'anello della
    ce = V[np.abs(sL - (sL.min() + a.eje * lung)) < 0.02 * lung].mean(0)   # sciabola), il centro si prende da una fetta pulita (la
    o = ce + L * (sg - (ce - c) @ L)                           # base della lama) e poi si porta alla quota giusta lungo la lunghezza
S = np.stack([Wv, T, L], axis=1)                               # colonne: W, T, L
R = np.diag([-1.0, -1.0, 1.0]) @ S.T                           # W→-X, T→-Y, L→+Z
k = a.lungo / lung
M = Matrix.Translation(Vector((0, 0, 0))) @ Matrix(((k, 0, 0, 0), (0, k, 0, 0), (0, 0, k, 0), (0, 0, 0, 1)))
R4 = Matrix([list(R[i]) + [0] for i in range(3)] + [[0, 0, 0, 1]])
tr = Matrix.Translation(Vector(-o))
ob.matrix_world = M @ R4 @ tr
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

chiudi(Vector((0, 0, a.lungo * 0.4)), a.lungo * 1.45)
