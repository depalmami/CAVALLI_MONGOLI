# NUVOLE volumetriche: cumuli di vapore generati in Blender (Cycles), fotografati su fondo
# trasparente e montati in un atlante 3×2 per le sagome-nuvola del gioco.
# Uso: blender -b --python tools/nuvole-blender.py -- <file uscita .webp>
import bpy, sys, os, math
import numpy as np
out = sys.argv[-1]
W, H, N = 640, 400, 6
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
try:
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'METAL'; pr.get_devices()
    for d in pr.devices: d.use = True
    sc.cycles.device = 'GPU'
except Exception as e: print('niente GPU', e)
sc.cycles.samples = 128; sc.cycles.use_denoising = True; sc.cycles.volume_bounces = 2; sc.cycles.volume_step_rate = 1.5
sc.render.film_transparent = True; sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('m'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.45, 0.6, 0.85, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.6
sole = bpy.data.objects.new('sole', bpy.data.lights.new('sole', 'SUN')); sole.data.energy = 7.0; sole.data.angle = 0.1
sole.rotation_euler = (math.radians(35), 0, math.radians(20)); sc.collection.objects.link(sole)
bpy.ops.mesh.primitive_cube_add(size=2); cubo = bpy.context.object; cubo.scale = (5, 3, 3.2)
mat = bpy.data.materials.new('vapore'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
o = nt.nodes.new('ShaderNodeOutputMaterial'); vol = nt.nodes.new('ShaderNodeVolumePrincipled')
vol.inputs['Color'].default_value = (1, 1, 1, 1); vol.inputs['Anisotropy'].default_value = 0.3
tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 2.1; nz.inputs['Detail'].default_value = 12; nz.inputs['Roughness'].default_value = 0.68
# forma a cumulo: ellissoide schiacciato, base piatta in basso
sc_ = nt.nodes.new('ShaderNodeVectorMath'); sc_.operation = 'MULTIPLY'; sc_.inputs[1].default_value = (1.0, 1.0, 1.05)
ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
fall = nt.nodes.new('ShaderNodeMath'); fall.operation = 'SUBTRACT'; fall.inputs[0].default_value = 1.0
sep = nt.nodes.new('ShaderNodeSeparateXYZ'); base = nt.nodes.new('ShaderNodeMath'); base.operation = 'GREATER_THAN'; base.inputs[1].default_value = -0.4
m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'
m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'ADD'
m3 = nt.nodes.new('ShaderNodeMath'); m3.operation = 'SUBTRACT'; m3.inputs[1].default_value = 1.55
m4 = nt.nodes.new('ShaderNodeMath'); m4.operation = 'MULTIPLY'; m4.inputs[1].default_value = 9.0; m4.use_clamp = False
m5 = nt.nodes.new('ShaderNodeMath'); m5.operation = 'MULTIPLY'
L = nt.links.new
L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs['Vector'], nz.inputs['Vector'])
L(tc.outputs['Object'], sc_.inputs[0]); L(sc_.outputs['Vector'], ln.inputs[0]); L(ln.outputs['Value'], fall.inputs[1])
amp = nt.nodes.new('ShaderNodeMath'); amp.operation = 'MULTIPLY'; amp.inputs[1].default_value = 2.0
L(nz.outputs['Fac'], amp.inputs[0]); L(amp.outputs['Value'], m2.inputs[0]); L(fall.outputs['Value'], m2.inputs[1])          # rumore + forma
L(m2.outputs['Value'], m3.inputs[0]); L(m3.outputs['Value'], m4.inputs[0])          # soglia → densità
L(tc.outputs['Object'], sep.inputs[0]); L(sep.outputs['Z'], base.inputs[0])
L(m4.outputs['Value'], m5.inputs[0]); L(base.outputs['Value'], m5.inputs[1])       # base piatta
cl = nt.nodes.new('ShaderNodeMath'); cl.operation = 'MAXIMUM'; cl.inputs[1].default_value = 0.0
L(m5.outputs['Value'], cl.inputs[0]); L(cl.outputs['Value'], vol.inputs['Density']); L(vol.outputs['Volume'], o.inputs['Volume'])
cubo.data.materials.append(mat)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); cam.data.type = 'ORTHO'; cam.data.ortho_scale = 10.5
cam.location = (0, -30, 0.6); cam.rotation_euler = (math.pi / 2, 0, 0); sc.collection.objects.link(cam); sc.camera = cam
fogli = []
for i in range(N):
    nz.inputs['W'].default_value = i * 3.7
    mp.inputs['Location'].default_value = (i * 1.3, i * 0.7, 0)
    f = os.path.join(os.path.dirname(out), f'_nuvola_{i}.png'); sc.render.filepath = f
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(f); fogli.append(np.array(im.pixels[:]).reshape(H, W, 4)); bpy.data.images.remove(im)
    print('NUVOLA', i)
righe = [np.concatenate(fogli[r * 3:(r + 1) * 3], axis=1) for r in range(2)]
atl = np.concatenate(righe[::-1], axis=0)          # Blender: la prima riga di pixel è in basso
img = bpy.data.images.new('nuvole', W * 3, H * 2, alpha=True); img.pixels = atl.ravel()
sc.render.image_settings.file_format = 'WEBP'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.quality = 85
img.save_render(out, scene=sc)
