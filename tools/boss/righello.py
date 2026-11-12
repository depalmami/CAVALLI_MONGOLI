# Vista di lato ORTOGONALE della testa con un righello sopra: per leggere dove passa la linea della bocca.
import bpy, sys, math
out, cx, cz, scala = sys.argv[sys.argv.index('--') + 1:][:4]; cx, cz, scala = float(cx), float(cz), float(scala)
extra = sys.argv[sys.argv.index('--') + 1:][4:]                    # coppie x,z di una linea di prova da disegnare
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o)
for n in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try: sc.render.engine = n; break
    except TypeError: pass
W, H = 1600, 800
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
try: sc.view_settings.view_transform = 'Standard'
except Exception: pass
w = bpy.data.worlds.new('m'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.5, 0.5, 0.5, 1); bg.inputs[1].default_value = 1.6
cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'; cam.ortho_scale = scala
co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
co.location = (cx, -5, cz); co.rotation_euler = (math.pi / 2, 0, 0)
def mat(c):
    m = bpy.data.materials.new('r'); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (0, 0, 0, 1); b.inputs['Emission Color'].default_value = (*c, 1); b.inputs['Emission Strength'].default_value = 1
    return m
ROSSO, GIALLO, BLU, VERDE = mat((1, 0, 0)), mat((1, 0.9, 0)), mat((0, 0.4, 1)), mat((0, 1, 0))
def barra(x0, x1, z0, z1, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, -0.3, (z0 + z1) / 2))
    o = bpy.context.object; o.scale = (max(abs(x1 - x0), 1e-4), 0.001, max(abs(z1 - z0), 1e-4)); o.data.materials.append(m)
t = scala / W * 1.2
for i in range(-5, 6):                                   # verticali ogni 0,1 (gialla a x = 0)
    barra(i * 0.1 - t / 2, i * 0.1 + t / 2, -0.02, 0.45, GIALLO if i == 0 else ROSSO)
for j in range(0, 10):                                   # orizzontali ogni 0,05 (gialla a z = 0,1)
    barra(-0.5, 0.5, j * 0.05 - t / 2, j * 0.05 + t / 2, GIALLO if j == 2 else BLU)
pts = [tuple(map(float, e.split(','))) for e in extra]
for (x0, z0), (x1, z1) in zip(pts, pts[1:]):             # linea di prova, verde
    n = 60
    for k in range(n):
        xa = x0 + (x1 - x0) * k / n; za = z0 + (z1 - z0) * k / n
        barra(xa - t, xa + t, za - t, za + t, VERDE)
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
