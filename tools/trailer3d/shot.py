# ATTREZZI COMUNI AGLI SHOT ANIMATI (il primo è stato shot-s14.py): curve di tempo, camera a chiavi, sbuffi di polvere a chiavi,
# preparazione della scena (risoluzione, motore, campioni, mosso), render dei fotogrammi, video e salvataggio del .blend.
#   prova   540×960, pochi campioni, senza mosso: per giudicare i tempi
#   finale  1080×1920, campioni pieni, mosso, e salva trailer/blender/shot/<shot>.blend
#
# RENDER CALMO (di norma acceso, 23 nov: il MacBook scaldava troppo): Cycles solo sulla GPU (niente CPU accanto: misurato su S04, la
# CPU passa da ~1110% a ~35% e il fotogramma è perfino più veloce, 13 s invece di 17), al massimo FILI fili di CPU per il resto, e
# una pausa dopo ogni fotogramma lunga RIPOSO volte il fotogramma (0,5 = la GPU lavora due terzi del tempo e riposa un terzo).
# Si regola con variabili d'ambiente:  CALMO=0 (tutto a pieno, come prima)  RIPOSO=0.5  PAUSA=6 (secondi fissi, al posto di RIPOSO)
# FILI=4  TRATTO=10-13 (solo quei fotogrammi, per le prove: non salva il .blend).
import bpy, os, math, random, subprocess, time
from mathutils import Vector
import animatic as AN
import animatic2 as A2

CALMO = os.environ.get('CALMO', '1') != '0'
RIPOSO = float(os.environ.get('RIPOSO', '0.5'))
PAUSA = float(os.environ['PAUSA']) if 'PAUSA' in os.environ else None
FILI = int(os.environ.get('FILI', '4'))
TRATTO = os.environ.get('TRATTO')
SHOT_DIR = os.path.abspath(os.path.join(AN.QUI, '..', '..', 'trailer', 'blender', 'shot'))

def sm(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)

def curva(chiavi, f):
    """chiavi = [(fotogramma, valore)]: fra una chiave e l'altra in smoothstep (attacchi e arrivi morbidi)."""
    if f <= chiavi[0][0]: return chiavi[0][1]
    for (f0, v0), (f1, v1) in zip(chiavi, chiavi[1:]):
        if f <= f1: return v0 + (v1 - v0) * sm((f - f0) / (f1 - f0))
    return chiavi[-1][1]

def prima(modo, motore):
    """Da chiamare PRIMA di costruire il mondo: risoluzione e motore (mondo() li legge)."""
    AN.W, AN.H = (1080, 1920) if modo == 'finale' else (540, 960)
    A2.MOTORE = motore

def dopo(modo, motore, n):
    """Da chiamare DOPO il mondo (che riparte dalle impostazioni di fabbrica): fotogrammi, campioni, mosso, chiavi lineari."""
    sc = bpy.context.scene; finale = modo == 'finale'
    sc.frame_start, sc.frame_end = 1, n; sc.render.fps = 24
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
    if motore == 'CYCLES': A2.usa_cycles(48 if finale else 12, cpu=not CALMO)
    if CALMO: sc.render.threads_mode = 'FIXED'; sc.render.threads = FILI
    # (fino al 24 nov questa riga stava in un «else» del modo calmo: l'atto 4 e la coda sono stati girati a 24 campioni, non 64)
    try: sc.eevee.taa_render_samples = 64 if finale else 16
    except Exception: pass
    sc.render.use_motion_blur = finale
    try: sc.render.motion_blur_shutter = 0.5
    except Exception: pass

def punta(cam, pos, mira):
    cam.location = pos; cam.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()

def chiave_camera(cam, f, pos, mira, lens=None, fuoco=None):
    punta(cam, pos, mira)
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    if lens is not None: cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    if fuoco is not None: cam.data.dof.focus_distance = fuoco; cam.data.dof.keyframe_insert('focus_distance', frame=f)

def sbuffo(q, f, mat, r, deriva, vita=14, n=None, nome='sbuffo'):
    """Uno sbuffo di polvere che nasce al fotogramma f in q, cresce in 3 fotogrammi, poi si allarga e va alla deriva."""
    o = AN.sfera(q, 1.0, mat, nome)
    o.scale = (0.001,) * 3; o.keyframe_insert('scale', frame=max(1, f - 1))
    o.scale = (r,) * 3; o.location = q; o.keyframe_insert('scale', frame=f + 3); o.keyframe_insert('location', frame=f + 3)
    fine = f + vita if n is None else min(n, f + vita)
    o.scale = (r * 1.8,) * 3; o.keyframe_insert('scale', frame=fine)
    o.location = Vector(q) + Vector(deriva); o.keyframe_insert('location', frame=fine)
    return o

def nascondi_da(o, f):
    """Visibile fino a f-1, sparisce da f (render e vista)."""
    for v, fr in ((False, f - 1), (True, f)):
        o.hide_render = v; o.hide_viewport = v
        o.keyframe_insert('hide_render', frame=fr); o.keyframe_insert('hide_viewport', frame=fr)

def appari_da(o, f):
    for v, fr in ((True, f - 1), (False, f)):
        o.hide_render = v; o.hide_viewport = v
        o.keyframe_insert('hide_render', frame=fr); o.keyframe_insert('hide_viewport', frame=fr)

def salva(nome):
    if TRATTO: print('NON SALVATO (prova di un tratto)'); return
    p = os.path.join(SHOT_DIR, nome + '.blend'); os.makedirs(SHOT_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=p, relative_remap=True); print('SALVATO', p)

def gira(cartella, nome, modo):
    sc = bpy.context.scene
    os.makedirs(cartella, exist_ok=True)
    for f in os.listdir(cartella):
        if f.startswith('f_') and f.endswith('.png'): os.remove(os.path.join(cartella, f))
    sc.render.image_settings.file_format = 'PNG'
    a, b = (int(x) for x in TRATTO.split('-')) if TRATTO else (sc.frame_start, sc.frame_end)
    if CALMO or TRATTO:
        t0 = time.time()
        for f in range(a, b + 1):                      # un fotogramma alla volta, con la pausa per raffreddare
            sc.frame_set(f); sc.render.filepath = os.path.join(cartella, 'f_%04d' % f)
            t, c = time.time(), time.process_time(); bpy.ops.render.render(write_still=True)
            dt = time.time() - t
            print('FOTOGRAMMA %d  %.1f s  CPU %.0f%%' % (f, dt, 100 * (time.process_time() - c) / max(dt, 1e-3)), flush=True)
            if CALMO and f < b: time.sleep(PAUSA if PAUSA is not None else max(0.5, RIPOSO * dt))
        print('TRATTO %d-%d  %.1f s in tutto' % (a, b, time.time() - t0), flush=True)
        if TRATTO: return None
    else:
        sc.render.filepath = os.path.join(cartella, 'f_####')
        bpy.ops.render.render(animation=True)
    mp4 = os.path.join(cartella, '%s-%s.mp4' % (nome, modo))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(cartella, 'f_%04d.png'),
                    '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4], check=True)
    print('VIDEO', mp4)
    return mp4
