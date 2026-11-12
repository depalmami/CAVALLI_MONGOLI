import bpy, sys, numpy as np
args = sys.argv[sys.argv.index('--') + 1:]
out, files = args[0], args[1:]
tess = []
for f in files:
    im = bpy.data.images.load(f); w, h = im.size
    tess.append(np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4))
tela = np.concatenate(tess[::-1], axis=0)
o = bpy.data.images.new('c', tela.shape[1], tela.shape[0], alpha=True)
o.pixels = tela.ravel(); o.filepath_raw = out; o.file_format = 'PNG'; o.save()
