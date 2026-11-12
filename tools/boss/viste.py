# Utilità condivise: luci, camera e foglio di viste (più render affiancati in un PNG solo).
import bpy, math, os
import numpy as np
from mathutils import Vector

VISTE = {
    'lato':     (0.0, -1.0, 0.12),
    'fronte':   (1.0, 0.0, 0.10),
    'trequarti': (0.8, -0.75, 0.45),
    'alto':     (0.001, -0.02, 1.0),
    'dietro34': (-0.8, -0.75, 0.45),
    'sotto34':  (0.8, -0.75, -0.25),
}

def motore(scene):
    for nome in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'):
        try:
            scene.render.engine = nome
            return nome
        except TypeError:
            continue

def scena_base(res=(640, 480), fondo=(0.30, 0.34, 0.40)):
    sc = bpy.context.scene
    motore(sc)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.film_transparent = False
    try: sc.view_settings.view_transform = 'Standard'
    except Exception: pass
    w = bpy.data.worlds.new('mondo'); sc.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (*fondo, 1); bg.inputs[1].default_value = 1.0
    for nome, rot, forza in (('sole', (math.radians(50), 0, math.radians(35)), 3.5),
                             ('contro', (math.radians(60), 0, math.radians(215)), 1.2)):
        l = bpy.data.lights.new(nome, 'SUN'); l.energy = forza
        o = bpy.data.objects.new(nome, l); o.rotation_euler = rot; sc.collection.objects.link(o)
    cam = bpy.data.cameras.new('cam'); cam.lens = 60
    co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
    return sc

def ingombro(objs):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.type != 'MESH': continue
        e = o.evaluated_get(dg)
        for c in e.bound_box:
            p = e.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p))
    return lo, hi

def inquadra(objs, direzione, margine=1.25):
    sc = bpy.context.scene; co = sc.camera
    co.data.sensor_fit = 'AUTO'; co.data.lens = 60
    lo, hi = ingombro(objs)
    centro = (lo + hi) / 2; raggio = (hi - lo).length / 2
    d = Vector(direzione).normalized()
    fov = 2 * math.atan(min(co.data.sensor_width, co.data.sensor_width * sc.render.resolution_y / sc.render.resolution_x) / (2 * co.data.lens))
    dist = raggio * margine / math.sin(fov / 2)
    co.location = centro + d * dist
    co.rotation_euler = (centro - co.location).to_track_quat('-Z', 'Y').to_euler()
    co.data.clip_start = dist * 0.01; co.data.clip_end = dist * 10

def foglio(percorso, objs, viste=('trequarti', 'lato', 'fronte', 'alto'), colonne=2, tmp=None, margine=0.8):
    sc = bpy.context.scene
    tmp = tmp or os.path.dirname(percorso)
    tessere = []
    for n, v in enumerate(viste):
        if callable(v): v()
        else: inquadra(objs, VISTE[v] if isinstance(v, str) else v, margine)
        et = bpy.data.objects.get('etichetta')
        if et:                                           # scritta in alto a sinistra, a 1 m dall'obiettivo
            bpy.context.view_layer.update()
            cam = sc.camera.data; asp = sc.render.resolution_y / sc.render.resolution_x
            mezza = math.tan(cam.angle_x / 2); et.location = (-mezza * 0.94, mezza * asp * 0.86, -1.0)
            et.scale = (mezza / 0.3,) * 3
        f = os.path.join(tmp, '_v_%d.png' % n)
        sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(f)
        w, h = im.size
        a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        tessere.append(a); bpy.data.images.remove(im); os.remove(f)
    h, w = tessere[0].shape[:2]
    righe = math.ceil(len(tessere) / colonne)
    tela = np.zeros((righe * h, colonne * w, 4), dtype=np.float32); tela[..., 3] = 1
    for i, a in enumerate(tessere):
        r, c = divmod(i, colonne)
        y0 = (righe - 1 - r) * h                      # i pixel di Blender partono dal basso
        tela[y0:y0 + h, c * w:(c + 1) * w] = a
    out = bpy.data.images.new('foglio', colonne * w, righe * h, alpha=True)
    out.pixels = tela.ravel(); out.filepath_raw = percorso; out.file_format = 'PNG'; out.save()
    bpy.data.images.remove(out)
    print('foglio:', percorso)
