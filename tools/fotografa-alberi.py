# "fotografa" ogni albero del modello Poly Haven da 8 lati, sfondo trasparente, luce neutra dall'alto;
# monta le 8 vedute in un'immagine sola (atlante orizzontale) per gli impostori del gioco
import bpy, sys, math, os
import numpy as np
from mathutils import Vector
src, out, pref = sys.argv[-3], sys.argv[-2], sys.argv[-1]
VISTE, W, H = 8, 384, 1024
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
for e in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try: sc.render.engine = e; break
    except Exception: pass
sc.render.film_transparent = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
try: sc.eevee.taa_render_samples = 32
except Exception: pass
sc.view_settings.view_transform = 'Standard'          # colori "piatti": il tone mapping lo fa il gioco
w = bpy.data.worlds.new('mondo'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.62, 0.68, 0.74, 1); bg.inputs[1].default_value = 0.9
sole = bpy.data.objects.new('sole', bpy.data.lights.new('sole', 'SUN')); sole.data.energy = 2.4
sole.rotation_euler = (0, 0, 0); sc.collection.objects.link(sole)   # dritto dall'alto: uguale da ogni lato
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); cam.data.type = 'ORTHO'; sc.collection.objects.link(cam); sc.camera = cam
os.makedirs(out, exist_ok=True)
alberi = [o for o in bpy.data.objects if o.type == 'MESH']
for o in alberi:
    for p in alberi: p.hide_render = (p is not o)
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (mn + mx) / 2; alto = mx.z - mn.z; largo = max(mx.x - mn.x, mx.y - mn.y)
    cam.data.ortho_scale = max(alto, largo * H / W) * 1.04
    fogli = []
    for k in range(VISTE):
        a = k / VISTE * 2 * math.pi
        cam.location = (c.x + math.sin(a) * 60, c.y - math.cos(a) * 60, c.z)
        cam.rotation_euler = (math.pi / 2, 0, a)
        f = os.path.join(out, f'_{pref}_{o.name}_{k}.png'); sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(f); fogli.append(np.array(im.pixels[:]).reshape(H, W, 4)); bpy.data.images.remove(im)
    atl = np.concatenate(fogli, axis=1)
    img = bpy.data.images.new(f'{pref}_{o.name}', W * VISTE, H, alpha=True)
    img.pixels = atl.ravel(); img.filepath_raw = os.path.join(out, f'{pref}_{o.name[-6]}.png'); img.file_format = 'PNG'; img.save()
    # quanto è alto davvero e dove sta la base nell'immagine: servono al gioco per poggiarlo a terra
    print('ATLANTE', o.name, 'alto_m', round(alto, 2), 'scala_ortho', round(cam.data.ortho_scale, 2), 'base_z', round(mn.z - (c.z - cam.data.ortho_scale / 2), 3))
