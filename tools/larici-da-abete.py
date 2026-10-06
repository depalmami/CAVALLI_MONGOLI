# Larici dalle foto dell'abete: il larice siberiano ha aghi più chiari e radi, e d'autunno
# (unica conifera che li perde) diventa d'oro. Si rivirano solo i pixel di chioma (verdi).
# Uso: blender -b --python tools/larici-da-abete.py -- <cartella foto PNG> <cartella uscita>
import bpy, sys, os
import numpy as np
src, dst = sys.argv[-2], sys.argv[-1]
sc = bpy.context.scene; sc.render.image_settings.file_format = 'WEBP'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.quality = 82
for k in 'abc':
    im = bpy.data.images.load(os.path.join(src, f'abete_{k}.png'))
    w, h = im.size; px = np.array(im.pixels[:]).reshape(h, w, 4)
    r, g, b = px[..., 0], px[..., 1], px[..., 2]
    chioma = np.clip((g - np.maximum(r, b)) * 12, 0, 1)            # quanto è "verde ago"
    l = 0.299 * r + 0.587 * g + 0.114 * b
    for nome, colore, luce in (('larice', (0.60, 0.88, 0.32), 1.7), ('larice_oro', (1.0, 0.60, 0.10), 2.6)):
        out = px.copy()
        for c in range(3):
            out[..., c] = px[..., c] * (1 - chioma) + np.clip(l * luce * colore[c], 0, 1) * chioma
        o = bpy.data.images.new(f'{nome}_{k}', w, h, alpha=True); o.pixels = out.ravel()
        o.save_render(os.path.join(dst, f'{nome}_{k}.webp'), scene=sc)
        print('LARICE', nome, k)
