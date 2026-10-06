import bpy, sys
out = sys.argv[-1]
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_animations=True, export_animation_mode='ACTIONS',
    export_apply=True, export_yup=True, export_cameras=False, export_lights=False, export_image_format='AUTO')
print('OK', out)
