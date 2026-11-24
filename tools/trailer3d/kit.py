# IL KIT DI SET del trailer in Blender: il mondo del gioco rifatto per le macchine da presa vere.
# Stesse ricette di horse-racing-3d.html e 3d/mondo.js: pista di TERRA (non asfalto) con due solchi, ghiaia sui bordi, banchina
# erbosa, suolo per bioma (erba / steppa secca / sabbia / roccia), rilievo per tappa, luce per tappa (LUCE_TAPPE), alberi e
# cespugli = le stesse foto del gioco (assets/alberi), un fiume dove il gioco lo mette. In più, per la macchina da presa:
# ciuffi d'erba veri vicino all'azione, nuvole, catena di montagne all'orizzonte, ger, rovine, stupa, gola e cascata.
#
# uso (da un altro script di Blender):   sys.path.insert(0, 'tools/trailer3d'); import kit
#   m = kit.Mondo(tappa=3, curva=1.0, colline=1.0)        # il tracciato e il terreno di quella tappa
#   kit.luce(m, az=250)                                   # cielo, sole/luna, nebbia della tappa
#   m.vegetazione(); m.erba_vicino(s=0, raggio=30); m.nuvole(); m.montagne()
#   eroe = kit.eroe_su(m, s=0, lat=0)                      # il protagonista sulla strada, orientato come la strada
# prova da riga di comando:  blender -b --python tools/trailer3d/kit.py -- <cartella uscita> griglia|beauty|tempi|<tappa 0-11>
#
# CONVENZIONI: s = metri lungo la strada (si va nel verso crescente), lat = metri a DESTRA della mezzeria (come nel gioco:
# lat + = destra). Il protagonista a yaw 0 guarda -Y; quando la strada è dritta va verso -Y.
import bpy, bmesh, sys, os, math, random, time
from mathutils import Vector, noise, kdtree

QUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, QUI)
import animatic as AN
from animatic import hexc, vec, importa, metti, eroe, predone, animale, oggetto, boss, camera, scatta, nuovo, sfera, scatola, lampada, A

# --- numeri del gioco ----------------------------------------------------------------------------------------------------
M = 1 / 765.0                                   # unità di gioco → metri (il protagonista è 1,83 m nativi, ×765 nel gioco)
LARG = 3000 * M * 2                             # la pista: 7,8 m
GHIAIA = 3720 * M                               # fine della banchina di ghiaia (4,9 m dalla mezzeria)
BANCHINA = 7200 * M                             # fine della banchina erbosa (9,4 m)
TERRA_BORDO = 3000 * M                          # fine dello sterrato (3,9 m)

TAPPE = ['Fiume Kherlen', "Guado dell'Onon", 'Burkhan Khaldun', 'Piana del Tuul', 'Colline di Khustai', 'Dune di Elsen Tasarkhai',
         "Valle dell'Orkhon", 'Cascate di Ulaan Tsutgalan', 'Monti Khangai', 'Rovine di Khar Balgas', 'Erdene Zuu', 'Karakorum']
SIGLE = ['kherlen', 'onon', 'burkhan', 'tuul', 'khustai', 'elsen', 'orkhon', 'ulaan', 'khangai', 'kharbalgas', 'erdene', 'karakorum']
SUOLO = [(0.55, 0.45, 0, 0), (0.85, 0.15, 0, 0), (0.85, 0.05, 0, 0.10), (0.20, 0.80, 0, 0), (0.40, 0.60, 0, 0), (0, 0.12, 0.88, 0),
         (0.80, 0.20, 0, 0), (0.45, 0.10, 0, 0.45), (0.70, 0.25, 0, 0.05), (0, 0.80, 0.20, 0), (0.40, 0.60, 0, 0), (0.40, 0.60, 0, 0)]
RILIEVO = [(3000, 0, .30), (5000, .2, .40), (13000, .8, .90), (2200, 0, .25), (7500, .3, .60), (1500, 0, .30), (6000, .3, .50),
           (11000, .7, .80), (16000, .9, 1.0), (3500, .1, .30), (4000, .1, .35), (5000, .2, .40)]
# elev, azim, turbidità, rayleigh, sole, nebbia, esposizione  (LUCE_TAPPE)
LUCE_T = [(4, 95, 6, 3.2, '#ffb27a', '#e9c3a6', .95), (14, 120, 5, 2.4, '#ffd9ae', '#dfe0dc', .90), (28, 135, 3, 1.6, '#fff1d6', '#cfdde6', .85),
          (58, 170, 4, 1.2, '#ffffff', '#d9e4ea', .80), (44, 200, 6, 1.8, '#fff3dd', '#dbe0dc', .82), (38, 215, 14, 1.4, '#fff0cf', '#e8d6b4', .85),
          (28, 230, 7, 2.0, '#ffe2b8', '#e2dccb', .85), (19, 240, 8, 2.4, '#ffd6a0', '#e6d4bb', .85), (10, 250, 9, 2.8, '#ffc27a', '#e8c9a2', .90),
          (3, 258, 10, 3.5, '#ff9a5a', '#e0a98c', 1.0), (-2, 265, 6, 3.0, '#ff8a6a', '#7f84a8', 1.35), (-5, 270, 4, 2.0, '#9aa8ff', '#2e3858', 1.6)]
# densità, gruppi, profondità, mix di specie (3d/alberi.js BIOMI)
BIOMI = [(.22, {'latifoglia': .6, 'cespuglio': .4}), (.45, {'latifoglia': .5, 'larice': .3, 'pino': .1, 'cespuglio': .1}),
         (.9, {'abete': .45, 'pino': .25, 'larice': .22, 'latifoglia': .08}), (.07, {'cespuglio': .7, 'latifoglia': .3}),
         (.2, {'latifoglia': .5, 'cespuglio': .5}), (.06, {'cespuglio': 1}), (.4, {'larice': .4, 'latifoglia': .45, 'cespuglio': .15}),
         (.6, {'pino': .35, 'abete': .3, 'larice': .25, 'cespuglio': .1}), (.85, {'larice': .45, 'abete': .3, 'pino': .25}),
         (.1, {'cespuglio': .6, 'latifoglia': .4}), (.25, {'latifoglia': .7, 'pino': .3}), (.15, {'latifoglia': .5, 'cespuglio': .5})]
FIUMI = {0: (-1, 1.0), 1: (1, 1.0), 2: (-1, .55), 3: (-1, 1.0), 6: (1, 1.0), 8: (1, .6)}     # tappa → (lato, larghezza relativa)
# foto degli alberi: (file, viste, larghezza/altezza di una vista, altezza in m = ortho × scala, base)
CARTE = {'abete': (['abete_a', 'abete_b', 'abete_c'], 8, 0.375, [19.68, 16.8, 17.49], [0.379, 1.371, 1.484]),
         'pino': (['pino_a', 'pino_b', 'pino_c'], 8, 0.375, [23.06, 21.07, 21.79], [1.342, 3.094, 2.121]),
         'larice': (['larice_a', 'larice_b', 'larice_c'], 8, 0.375, [19.68, 16.8, 17.49], [0.379, 1.371, 1.484]),
         'latifoglia': (['latifoglia_a', 'latifoglia_b', 'latifoglia_c'], 8, 1.0, [5.984*2.0, 5.175*2.3, 3.679*2.6], [0.478*2.0, 0.884*2.3, 0.532*2.6]),
         'cespuglio': (['cespuglio_a', 'cespuglio_b', 'cespuglio_c'], 8, 2.0, [0.589*4.5, 0.514*4.5, 0.365*5.5], [0.081*4.5, 0.082*4.5, 0.039*5.5])}

def sm(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if a != b else float(x > a)
    return t * t * (3 - 2 * t)

_MATCARTE = {}
FOS = None                                      # (colore lineare, distanza m, massimo) della nebbia della scena

# =====================================================================================================================
#  IL TRACCIATO
# =====================================================================================================================
class Tracciato:
    """La strada: una linea (x,y) con quota. s=0 è l'origine, il protagonista a s=0 guarda -Y."""
    def __init__(self, curva=0.0, colline=0.0, lung=1400.0, pre=250.0, seme=0.0):
        self.s0, self.s1, self.seme = -int(pre), int(lung), seme
        n = self.s1 - self.s0 + 1; P = []; th = 0.0; x = y = 0.0
        for i in range(n):
            s = self.s0 + i
            P.append((x, y, th))
            k = curva * (math.sin(s * 0.0087 + seme) * 0.0015 + math.sin(s * 0.0231 + seme * 2) * 0.0007)
            th += k; x += math.cos(th); y += math.sin(th)
        i0 = -self.s0; x0, y0, t0 = P[i0]; rot = -math.pi / 2 - t0; c, sn = math.cos(rot), math.sin(rot)
        self.P = []; self.T = []; self.Z = []
        z0 = colline * (2.4 * math.sin(seme) + 1.2 * math.sin(1 + seme))
        for i, (x, y, th) in enumerate(P):
            dx, dy = x - x0, y - y0; s = self.s0 + i
            self.P.append(Vector((dx * c - dy * sn, dx * sn + dy * c)))
            a = th + rot; self.T.append(Vector((math.cos(a), math.sin(a))))
            self.Z.append(colline * (2.4 * math.sin(s * 0.0061 + seme) + 1.2 * math.sin(s * 0.0167 + 1 + seme)) - z0)
        self.kd = kdtree.KDTree(len(self.P))
        for i, p in enumerate(self.P): self.kd.insert((p.x, p.y, 0), i)
        self.kd.balance()
    def _i(self, s):
        f = min(max(s - self.s0, 0.0), len(self.P) - 1.001); i = int(f); return i, f - i
    def tang(self, s):
        i, f = self._i(s); t = self.T[i] * (1 - f) + self.T[i + 1] * f; return t.normalized()
    def dx(self, s):                            # destra (lat +) della direzione di marcia
        t = self.tang(s); return Vector((t.y, -t.x))
    def pos(self, s, lat=0.0, dz=0.0):
        i, f = self._i(s); p = self.P[i] * (1 - f) + self.P[i + 1] * f; z = self.Z[i] * (1 - f) + self.Z[i + 1] * f
        r = self.dx(s); return Vector((p.x + r.x * lat, p.y + r.y * lat, z + dz))
    def yaw(self, s):                           # yaw del modello (0 = guarda -Y) che segue la strada
        t = self.tang(s); return math.degrees(math.atan2(t.x, -t.y))
    def vicino(self, x, y):                     # (s, lat, quota strada) del punto più vicino
        co, i, d = self.kd.find((x, y, 0)); T = self.T[i]; p = Vector((x, y)) - self.P[i]
        s = self.s0 + i + p.dot(T); lat = p.dot(Vector((T.y, -T.x))); return s, lat, self.Z[i]

# =====================================================================================================================
#  IL MONDO (terreno, strada, fiume)
# =====================================================================================================================
class Mondo:
    def __init__(self, tappa=3, curva=0.6, colline=1.0, lung=1400.0, pre=250.0, seme=3.0, suolo=None, rilievo=None, fiume=None, nome=None, gola=None):
        global FOS
        self.k = tappa; self.seme = seme
        _MATCARTE.clear()
        fissa_nebbia(tappa)
        self.suolo = suolo or SUOLO[tappa]; r = rilievo or RILIEVO[tappa]
        self.amp, self.creste, self.pend = r[0] * M, r[1], r[2]
        f = FIUMI.get(tappa) if fiume is None else fiume
        self.fiume = f
        self.gola = gola                        # (s0, s1, lat centro, mezza larghezza, profondità): una gola scavata accanto alla strada
        self.tr = Tracciato(curva, colline, lung, pre, seme)
        self.mat = None
        random.seed(seme)
        self.costruisci()
    # --- l'altezza ---
    def hn(self, x, y):                         # rilievo naturale, lontano dalla strada
        sd = self.seme
        n1 = noise.fractal(Vector((x * 0.0042, y * 0.0042, sd)), 0.55, 2.0, 5)
        n2 = 1.0 - abs(noise.noise(Vector((x * 0.0055, y * 0.0055, sd + 7)))) * 2.0
        return self.amp * ((1 - self.creste) * n1 + self.creste * (n2 * 0.9 - 0.1)) + noise.noise(Vector((x * 0.05, y * 0.05, sd + 3))) * 0.18
    def lat_fiume(self, s):
        lato, w = self.fiume; return lato * -1 * (22 + 3 * math.sin(s / 90) + 1.3 * math.sin(s / 31) + 0.0)
    def larg_fiume(self, s):
        lato, w = self.fiume; return 6.5 * w * sm(self.tr.s0, self.tr.s0 + 150, s) * sm(self.tr.s1, self.tr.s1 - 150, s)
    def fattore(self, t):                       # quanto del rilievo naturale c'è a t metri dalla strada: poco vicino, tutto lontano
        t = abs(t); return 0.18 + 0.4 * sm(100, 480, t) + 1.1 * sm(500, 3500, t)
    def quota_sl(self, s, t, x, y, zr, fiume=True):
        k = sm(BANCHINA, BANCHINA + 30 + self.amp * 3.0 + (1.1 - self.pend) * 40, abs(t))
        z = zr * (1 - k) + (self.hn(x, y) * self.fattore(t) + zr * 0.5) * k
        if self.fiume and fiume:
            lr = self.lat_fiume(s); w = self.larg_fiume(s)
            if w > 0.2:
                prof = 1.0 - sm(w * 0.5, w * 1.9, abs(t - lr))
                z = min(z, z * (1 - prof) + (zr - 2.6) * prof)
        if self.gola and fiume:
            g0, g1, gl, gw, gp = self.gola
            z -= gp * (1 - sm(gw * 0.55, gw, abs(t - gl))) * sm(g0, g0 + 6, s) * sm(g1, g1 - 40, s)
        return z
    def quota(self, x, y):
        s, t, zr = self.tr.vicino(x, y); return self.quota_sl(s, t, x, y, zr)
    def punto(self, s, lat=0.0, dz=0.0):        # un punto sul terreno (non solo sulla strada)
        p = self.tr.pos(s, lat); return Vector((p.x, p.y, self.quota(p.x, p.y) + dz))
    # --- le mesh ---
    def costruisci(self):
        tr = self.tr; ds = 2.0
        lati = [0, .9, 1.8, 2.7, 3.5, TERRA_BORDO, 4.4, GHIAIA, 5.8, 7.5, BANCHINA, 12, 15, 19, 24, 30, 38, 48, 60, 75, 95, 120, 150, 190, 240, 300, 380]
        T = [-x for x in reversed(lati[1:])] + lati
        # una riga di vertici per ogni sezione, due fiumi inclusi: aggiungo colonne attorno al letto
        n_s = int((tr.s1 - tr.s0) / ds) + 1
        bm = bmesh.new(); vs = []; Tv = []; Sv = []; W = []; Wv = []
        sw = lambda t: self.suolo
        for i in range(n_s):
            s = tr.s0 + i * ds; row = []
            T_row = list(T)
            if self.fiume:
                lr = self.lat_fiume(s); w = self.larg_fiume(s)
                if w > 0.2: T_row = sorted(T_row + [lr + d * w for d in (-1.9, -1.0, -0.5, 0, 0.5, 1.0, 1.9)])
            if self.gola and self.gola[0] - 12 <= s <= self.gola[1] + 12:
                g0, g1, gl, gw, gp = self.gola; T_row = sorted(T_row + [gl + gw * d for d in (-1.15, -0.9, -0.7, -0.5, -0.3, -0.1, 0.1, 0.3, 0.5, 0.7, 0.9, 1.15)])
            for t in T_row:
                p = tr.pos(s, t); zr = tr.pos(s, 0).z
                z = self.quota_sl(s, t, p.x, p.y, zr)
                row.append(bm.verts.new((p.x, p.y, z))); Tv.append(t); Sv.append(s); Wv.extend(self.suolo_in(s, t))
            vs.append(row)
        # quad fra righe con numero di colonne diverso: collego per posizione di t (le righe senza fiume hanno meno colonne)
        for a, b in zip(vs[:-1], vs[1:]):
            if len(a) == len(b):
                for j in range(len(a) - 1): bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
            else:                                # raccordo: rifaccio la riga corta con i vertici fantasma del letto
                ta = [v for v in a]; tb = [v for v in b]
                # triangoli a ventaglio sul bordo (rari, solo dove nasce il fiume)
                i = j = 0
                while i < len(a) - 1 or j < len(b) - 1:
                    if i < len(a) - 1 and (j >= len(b) - 1 or (i + 1) / (len(a) - 1) <= (j + 1) / (len(b) - 1)):
                        bm.faces.new((a[i], b[j], a[i + 1])); i += 1
                    else:
                        bm.faces.new((a[i], b[j], b[j + 1])); j += 1
        me = bpy.data.meshes.new('terreno'); bm.to_mesh(me); bm.free()
        n = len(me.vertices)
        at = me.attributes.new('t', 'FLOAT', 'POINT'); at.data.foreach_set('value', Tv)
        asv = me.attributes.new('s', 'FLOAT', 'POINT'); asv.data.foreach_set('value', Sv)
        ca = me.color_attributes.new('suolo', 'FLOAT_COLOR', 'POINT'); ca.data.foreach_set('color', Wv)
        for p in me.polygons: p.use_smooth = True
        self.mat = mat_terreno(self.tinta_strada())
        self.terreno = AN.collega(bpy.data.objects.new('terreno', me), self.mat)
        # l'anello di orizzonte: griglia larga e rada, stessa altezza naturale (abbassata: la copre il terreno vero)
        self.orizzonte()
    def suolo_in(self, s, t):
        if self.gola:
            g0, g1, gl, gw, gp = self.gola
            r = (1 - sm(gw * 0.95, gw * 1.15, abs(t - gl))) * sm(g0 - 3, g0 + 2, s) * sm(g1 + 3, g1 - 30, s)
            if r > 0: return tuple(self.suolo[q] * (1 - r) + (0.04, 0.10, 0.0, 0.86)[q] * r for q in range(4))
        return self.suolo
    def tinta_strada(self):
        TP = [(0.86, 0.84, 0.78), (1.06, 0.98, 0.84), (1.18, 1.02, 0.74), (0.92, 0.92, 0.92)]
        return tuple(sum(self.suolo[q] * TP[q][r] for q in range(4)) for r in range(3))
    def orizzonte(self, R=9000, res=70):
        bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=res, y_segments=res, size=R)
        for v in bm.verts:
            s_, t_, zr = self.tr.vicino(v.co.x, v.co.y)
            v.co.z = self.quota_sl(s_, t_, v.co.x, v.co.y, zr, fiume=False) - 0.6
            if abs(t_) < 330 and self.tr.s0 + 20 < s_ < self.tr.s1 - 20: v.co.z -= 25.0      # sotto al nastro di terreno: tanto non si vede
        me = bpy.data.meshes.new('orizzonte'); bm.to_mesh(me); bm.free()
        n = len(me.vertices)
        at = me.attributes.new('t', 'FLOAT', 'POINT'); at.data.foreach_set('value', [200.0] * n)
        asv = me.attributes.new('s', 'FLOAT', 'POINT'); asv.data.foreach_set('value', [0.0] * n)
        ca = me.color_attributes.new('suolo', 'FLOAT_COLOR', 'POINT'); ca.data.foreach_set('color', [c for _ in range(n) for c in self.suolo])
        for p in me.polygons: p.use_smooth = True
        AN.collega(bpy.data.objects.new('orizzonte', me), self.mat)
    def acqua(self):
        if not self.fiume: return None
        tr = self.tr; bm = bmesh.new(); prev = None; ds = 3.0
        for i in range(int((tr.s1 - tr.s0) / ds) + 1):
            s = tr.s0 + i * ds; w = self.larg_fiume(s)
            if w < 0.3: prev = None; continue
            lr = self.lat_fiume(s); a = tr.pos(s, lr - w * 1.05); b = tr.pos(s, lr + w * 1.05); z = tr.pos(s, 0).z - 1.35
            r = (bm.verts.new((a.x, a.y, z)), bm.verts.new((b.x, b.y, z)))
            if prev: bm.faces.new((prev[0], prev[1], r[1], r[0]))
            prev = r
        me = bpy.data.meshes.new('fiume'); bm.to_mesh(me); bm.free()
        m = materiale_acqua(); return AN.collega(bpy.data.objects.new('fiume', me), m)

# =====================================================================================================================
#  MATERIALI
# =====================================================================================================================
def _n(nt, tipo, **kw):
    n = nt.nodes.new(tipo)
    for k, v in kw.items():
        if k in ('ds', 'dim'): continue
        try: setattr(n, k, v)
        except Exception: pass
    return n

def _lin(nt, a, b): nt.links.new(a, b)

def foschia(m, massimo=0.9):
    """La nebbia di distanza della scena, aggiunta in coda a un materiale (il volume del mondo in background dà nero)."""
    if not FOS: return
    nt = m.node_tree; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); src = out.inputs['Surface'].links[0].from_socket
    col, dist, k = FOS
    cd = _n(nt, 'ShaderNodeCameraData'); mr = _n(nt, 'ShaderNodeMapRange', clamp=True); mr.inputs['From Max'].default_value = dist; mr.inputs['To Max'].default_value = massimo
    _lin(nt, cd.outputs['View Distance'], mr.inputs['Value'])
    pw = _n(nt, 'ShaderNodeMath', operation='POWER'); pw.inputs[1].default_value = 1.5; _lin(nt, mr.outputs['Result'], pw.inputs[0])
    em = _n(nt, 'ShaderNodeEmission'); em.inputs['Color'].default_value = col; em.inputs['Strength'].default_value = k
    mx = _n(nt, 'ShaderNodeMixShader'); _lin(nt, pw.outputs['Value'], mx.inputs['Fac']); _lin(nt, src, mx.inputs[1]); _lin(nt, em.outputs['Emission'], mx.inputs[2])
    _lin(nt, mx.outputs['Shader'], out.inputs['Surface'])

def mat_terreno(tinta_strada):
    """Suolo per bioma + pista di terra: le ricette di 3d/mondo.js (patchTerreno e patchStrada)."""
    m = bpy.data.materials.new('suolo'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = _n(nt, 'ShaderNodeOutputMaterial'); b = _n(nt, 'ShaderNodeBsdfPrincipled')
    b.inputs['Roughness'].default_value = 0.95
    try: b.inputs['Specular IOR Level'].default_value = 0.05
    except KeyError: pass
    geo = _n(nt, 'ShaderNodeNewGeometry')
    asu = _n(nt, 'ShaderNodeAttribute', attribute_name='suolo'); at = _n(nt, 'ShaderNodeAttribute', attribute_name='t'); asv = _n(nt, 'ShaderNodeAttribute', attribute_name='s')
    sep = _n(nt, 'ShaderNodeSeparateColor'); _lin(nt, asu.outputs['Color'], sep.inputs['Color'])
    wE, wS, wA = sep.outputs['Red'], sep.outputs['Green'], sep.outputs['Blue']; wR = asu.outputs['Alpha']
    # coordinate: posizione di mondo
    def mapping(scala, off=(0, 0, 0)):
        mp = _n(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scala, scala, scala); mp.inputs['Location'].default_value = off
        _lin(nt, geo.outputs['Position'], mp.inputs['Vector']); return mp.outputs['Vector']
    def rumore(scala, det=6, off=(0, 0, 0), vettore=None):
        nz = _n(nt, 'ShaderNodeTexNoise', noise_dimensions='3D'); nz.inputs['Scale'].default_value = scala; nz.inputs['Detail'].default_value = det
        _lin(nt, vettore or geo.outputs['Position'], nz.inputs['Vector']); return nz.outputs['Fac']
    def mix(a, bb, f, tipo='RGBA', blend='MIX'):
        mx = _n(nt, 'ShaderNodeMix', data_type=tipo, blend_type=blend)
        if isinstance(a, tuple): mx.inputs['A'].default_value = a
        else: _lin(nt, a, mx.inputs['A'])
        if isinstance(bb, tuple): mx.inputs['B'].default_value = bb
        else: _lin(nt, bb, mx.inputs['B'])
        if isinstance(f, (int, float)): mx.inputs['Factor'].default_value = f
        else: _lin(nt, f, mx.inputs['Factor'])
        return mx.outputs['Result']
    def mat_(op, a, bb=None, **kw):
        n = _n(nt, 'ShaderNodeMath', operation=op, **kw)
        for i, v in enumerate((a, bb)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: _lin(nt, v, n.inputs[i])
        return n.outputs['Value']
    def rampa(x, a, bb):                          # smoothstep(a,b,x) con una rampa
        mr = _n(nt, 'ShaderNodeMapRange', clamp=True, interpolation_type='SMOOTHSTEP'); mr.inputs['From Min'].default_value = a; mr.inputs['From Max'].default_value = bb
        _lin(nt, x, mr.inputs['Value']); return mr.outputs['Result']
    # --- erba: la texture del gioco, due scale per nascondere la ripetizione, tinta
    def immagine(path, scala, dati=False):
        im = _n(nt, 'ShaderNodeTexImage'); im.image = bpy.data.images.load(A + path, check_existing=True)
        if dati: im.image.colorspace_settings.name = 'Non-Color'
        _lin(nt, mapping(scala), im.inputs['Vector']); return im.outputs['Color']
    g1 = immagine('textures/Grass004/Grass004_1K-JPG_Color.jpg', 1 / 4.6); g2 = immagine('textures/Grass004/Grass004_1K-JPG_Color.jpg', 1 / 31.0)
    erba = mix(g1, g2, 0.45, blend='MIX')
    erba = mix(erba, (0.95, 0.98, 0.9, 1), 0.0)
    lum = _n(nt, 'ShaderNodeRGBToBW'); _lin(nt, erba, lum.inputs['Color'])
    paglia = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); paglia.inputs['Factor'].default_value = 1.0
    _lin(nt, lum.outputs['Val'], paglia.inputs['A']); paglia.inputs['B'].default_value = (2.0, 1.62, 0.85, 1)
    secca = mix(paglia.outputs['Result'], (0.8, 0.8, 0.8, 1), 0.0)
    var = mat_('MULTIPLY_ADD', rumore(0.7), 0.3, use_clamp=False); nt.nodes[-1].inputs[2].default_value = 0.85
    secca = mix(secca, secca, 1.0)
    sm_ = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); sm_.inputs['Factor'].default_value = 1.0
    _lin(nt, secca, sm_.inputs['A']); _lin(nt, var, sm_.inputs['B']); secca = sm_.outputs['Result']
    # --- sabbia: increspature del vento
    wv = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL'); wv.inputs['Scale'].default_value = 2.6; wv.inputs['Distortion'].default_value = 7.0
    wv.inputs['Detail'].default_value = 1.0; _lin(nt, geo.outputs['Position'], wv.inputs['Vector'])
    sabbia = mix((0.30, 0.18, 0.085, 1), (0.46, 0.32, 0.18, 1), wv.outputs['Fac'])
    s2 = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); s2.inputs['Factor'].default_value = 1.0
    _lin(nt, sabbia, s2.inputs['A']); _lin(nt, mat_('MULTIPLY_ADD', rumore(40, 2), 0.2, use_clamp=False), s2.inputs['B']); nt.nodes[-1].inputs[2].default_value = 0.9; sabbia = s2.outputs['Result']
    # --- roccia
    roccia = mix((0.12, 0.105, 0.10, 1), (0.30, 0.27, 0.24, 1), rumore(0.9, 7))
    # --- il suolo: somma pesata dei quattro
    def pesa(col, w):
        sc = _n(nt, 'ShaderNodeVectorMath', operation='SCALE'); _lin(nt, col, sc.inputs[0]); _lin(nt, w, sc.inputs['Scale']); return sc.outputs['Vector']
    def somma(a, bb):
        n = _n(nt, 'ShaderNodeVectorMath', operation='ADD'); _lin(nt, a, n.inputs[0]); _lin(nt, bb, n.inputs[1]); return n.outputs['Vector']
    suolo = somma(somma(pesa(erba, wE), pesa(secca, wS)), somma(pesa(sabbia, wA), pesa(roccia, wR)))
    # --- la pista di terra (patchStrada): L = −1…1 da ciglio a ciglio, s lungo la strada
    L = mat_('DIVIDE', at.outputs['Fac'], TERRA_BORDO); Labs = mat_('ABSOLUTE', L)
    tv = _n(nt, 'ShaderNodeCombineXYZ'); _lin(nt, at.outputs['Fac'], tv.inputs['X']); _lin(nt, asv.outputs['Fac'], tv.inputs['Y'])
    def rumoreTS(scala, det=5, off=0.0):
        nz = _n(nt, 'ShaderNodeTexNoise', noise_dimensions='3D'); nz.inputs['Scale'].default_value = scala; nz.inputs['Detail'].default_value = det
        v = _n(nt, 'ShaderNodeVectorMath', operation='ADD'); _lin(nt, tv.outputs['Vector'], v.inputs[0]); v.inputs[1].default_value = (0, 0, off)
        _lin(nt, v.outputs['Vector'], nz.inputs['Vector']); return nz.outputs['Fac']
    chiazze = rumoreTS(0.7)
    terra = mix((0.34, 0.235, 0.135, 1), (0.54, 0.40, 0.24, 1), chiazze)
    cs = mat_('ADD', 0.38, mat_('MULTIPLY', mat_('SINE', mat_('MULTIPLY', asv.outputs['Fac'], 0.54)), 0.05))      # centro del solco
    solco = mat_('SUBTRACT', 1.0, rampa(mat_('ABSOLUTE', mat_('SUBTRACT', Labs, cs)), 0.06, 0.16))
    terra = mix(terra, terra, 1.0)
    ts = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); ts.inputs['Factor'].default_value = 1.0
    _lin(nt, terra, ts.inputs['A']); _lin(nt, mat_('SUBTRACT', 1.0, mat_('MULTIPLY', solco, 0.28)), ts.inputs['B']); terra = ts.outputs['Result']
    mezzo = mat_('MULTIPLY', mat_('SUBTRACT', 1.0, rampa(Labs, 0.08, 0.2)), rampa(rumoreTS(0.25, 4, 3.0), 0.45, 0.7))
    verde = mix((0.16, 0.20, 0.08, 1), (0.22, 0.27, 0.11, 1), rumoreTS(18, 2))
    terra = mix(terra, verde, mat_('MULTIPLY', mezzo, 0.85))
    sasso = mat_('MULTIPLY', rampa(rumoreTS(26, 2), 0.82, 0.9), mat_('SUBTRACT', 1.0, solco))
    terra = mix(terra, (0.45, 0.42, 0.38, 1), mat_('MULTIPLY', sasso, 0.7))
    bordi = mat_('SUBTRACT', 1.0, mat_('MULTIPLY', rampa(Labs, 0.85, 1.0), 0.25))
    t3 = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); t3.inputs['Factor'].default_value = 1.0
    _lin(nt, terra, t3.inputs['A']); _lin(nt, bordi, t3.inputs['B']); terra = t3.outputs['Result']
    # ghiaia (banchina) più scura: ×0,68 oltre il bordo dello sterrato
    ghi = rampa(mat_('ABSOLUTE', at.outputs['Fac']), TERRA_BORDO, TERRA_BORDO + 0.15)
    t4 = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); t4.inputs['Factor'].default_value = 1.0
    _lin(nt, terra, t4.inputs['A']); _lin(nt, mat_('SUBTRACT', 1.0, mat_('MULTIPLY', ghi, 0.32)), t4.inputs['B'])
    t5 = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); t5.inputs['Factor'].default_value = 1.0
    _lin(nt, t4.outputs['Result'], t5.inputs['A']); t5.inputs['B'].default_value = tuple(0.9 * c for c in tinta_strada) + (1,)
    pista = t5.outputs['Result']
    # fuori dalla ghiaia comincia l'erba: passaggio netto ma morbido a 4,9 m
    fuori = rampa(mat_('ABSOLUTE', at.outputs['Fac']), GHIAIA - 0.12, GHIAIA + 0.35)
    col = mix(pista, suolo, fuori)
    _lin(nt, col, b.inputs['Base Color'])
    # grana: la normale dell'erba del gioco
    nm = _n(nt, 'ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.6
    im = _n(nt, 'ShaderNodeTexImage'); im.image = bpy.data.images.load(A + 'textures/Grass004/Grass004_1K-JPG_NormalGL.jpg', check_existing=True); im.image.colorspace_settings.name = 'Non-Color'
    _lin(nt, mapping(1 / 3.0), im.inputs['Vector']); _lin(nt, im.outputs['Color'], nm.inputs['Color']); _lin(nt, nm.outputs['Normal'], b.inputs['Normal'])
    _lin(nt, b.outputs['BSDF'], out.inputs['Surface'])
    foschia(m)
    return m

def materiale_acqua(colore=(0.012, 0.03, 0.035, 1), rosso=False):
    m = bpy.data.materials.new('acqua'); m.use_nodes = True; nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (0.30, 0.04, 0.02, 1) if rosso else colore; b.inputs['Roughness'].default_value = 0.10 if not rosso else 0.5
    try: b.inputs['Specular IOR Level'].default_value = 0.35 if not rosso else 0.08
    except KeyError: pass
    try: b.inputs['IOR'].default_value = 1.33
    except KeyError: pass
    foschia(m, 0.7); return m


# =====================================================================================================================
#  CIELO E LUCE PER TAPPA
# =====================================================================================================================
def fissa_nebbia(k):
    global FOS
    el, az, turb, rayl, sole, neb, espo = LUCE_T[k]
    FOS = (hexc(neb), 520.0 if k == 11 else (700.0 if k in (9, 10) else 900.0), 1.0 if k < 10 else (0.55 if k == 10 else 0.12))
    AN.FOSCHIA = FOS

# copertura dei cumuli del cielo per tappa (None = niente: all'alba restano le carte di nuvole, la notte ci sono le stelle)
NUV = {1: 0.42, 2: 0.50, 3: 0.48, 4: 0.46, 5: 0.26, 6: 0.42, 7: 0.38, 8: 0.38, 9: 0.44, 10: 0.38}
def nuvole_cielo(k, sole_hex):
    c = NUV.get(k)
    if not c: return None
    sc_ = hexc(sole_hex)[:3]; tram = k in (9, 10)
    return dict(copertura=c, colore_sole=tuple(0.55 + 0.45 * q for q in sc_), ombra=(0.80, 0.68, 0.78) if tram else (0.80, 0.86, 0.96), forza=2.2, seme=k * 1.7 + 0.3)

def luce(m, az=250.0, esposizione=0.0, energia=None, luna_az=None, luna_el=24.0):
    """Cielo + sole (o luna) della tappa del mondo m, con l'esposizione del gioco. az = dove sta il sole/la luna (da +X, antiorario)."""
    k = m.k; el, az0, turb, rayl, sole, neb, espo = LUCE_T[k]
    sc = bpy.context.scene
    sc.view_settings.exposure = math.log2(espo) + esposizione - 1.1 * sm(8, 50, el)
    if k == 11:                                                         # Karakorum: notte vera, con stelle e luna
        AN.notte(az_luna=az if luna_az is None else luna_az, el_luna=luna_el, forza_luna=2.6, grandezza_luna=2.4, orizzonte=(0.030, 0.040, 0.095))
        sc.view_settings.exposure += 1.1
    else:
        en = energia if energia is not None else (0.5 if el <= 0 else 1.6 + 2.2 * math.sin(math.radians(el)))
        AN.cielo(el, az, polvere=max(0.4, turb / 4.0), aria=rayl * 0.8, forza=0.16 + 0.34 * (1 - math.sin(math.radians(max(el, 0)))), nebbia=None, sole=sole, energia=en, disco=1.6, nuvole=nuvole_cielo(k, sole))
    AN.FOSCHIA = FOS

def eroe_su(m, s=0.0, lat=0.0, azione='Gallop', frame=6, arma=None, arma_rot=(50, 0, 0), yaw_extra=0.0, dz=0.0):
    p = m.punto(s, lat, dz); return AN.eroe((p.x, p.y, p.z), azione, frame, yaw=m.tr.yaw(s) + yaw_extra, arma=arma, arma_rot=arma_rot)

def cam_su(m, s, lat, h, mira_s, mira_lat, mira_h, lens=35, **kw):
    a = m.punto(s, lat); b = m.punto(mira_s, mira_lat)
    return camera((a.x, a.y, a.z + h), (b.x, b.y, b.z + mira_h), lens, **kw)


# =====================================================================================================================
#  ERBA, ALBERI, NUVOLE, MONTAGNE, GER
# =====================================================================================================================
def _tuft(secca):
    bm = bmesh.new(); random.seed(5)
    for i in range(11):
        a = random.random() * math.tau; r = random.uniform(0.0, 0.07); h = random.uniform(0.20, 0.50); w = random.uniform(0.010, 0.017); cv = random.uniform(0.03, 0.16)
        d = Vector((math.cos(a), math.sin(a), 0)); base = d * r; side = Vector((-d.y, d.x, 0)); rows = []
        for j in range(4):
            u = j / 3; c = base + d * (cv * u * u); c.z = h * u; wd = w * (1 - u * 0.93)
            rows.append((bm.verts.new(c - side * wd), bm.verts.new(c + side * wd)))
        for q in range(3): bm.faces.new((rows[q][0], rows[q][1], rows[q + 1][1], rows[q + 1][0]))
    me = bpy.data.meshes.new('tuft'); bm.to_mesh(me); bm.free()
    m = bpy.data.materials.new('erba_ciuffo'); m.use_nodes = True; nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Roughness'].default_value = 0.7
    try: b.inputs['Specular IOR Level'].default_value = 0.1
    except KeyError: pass
    tc = _n(nt, 'ShaderNodeTexCoord'); sepz = _n(nt, 'ShaderNodeSeparateXYZ'); _lin(nt, tc.outputs['Object'], sepz.inputs[0])
    oi = _n(nt, 'ShaderNodeObjectInfo')
    gr = _n(nt, 'ShaderNodeMapRange', clamp=True); gr.inputs['From Max'].default_value = 0.4; _lin(nt, sepz.outputs['Z'], gr.inputs['Value'])
    def duecolori(a, c):
        mx = _n(nt, 'ShaderNodeMix', data_type='RGBA'); mx.inputs['A'].default_value = a; mx.inputs['B'].default_value = c; _lin(nt, gr.outputs['Result'], mx.inputs['Factor']); return mx.outputs['Result']
    verde = duecolori((0.030, 0.060, 0.012, 1), (0.20, 0.30, 0.07, 1)); paglia = duecolori((0.13, 0.09, 0.03, 1), (0.50, 0.40, 0.17, 1))
    cmp_ = _n(nt, 'ShaderNodeMath', operation='LESS_THAN'); _lin(nt, oi.outputs['Random'], cmp_.inputs[0]); cmp_.inputs[1].default_value = secca
    fin = _n(nt, 'ShaderNodeMix', data_type='RGBA'); _lin(nt, cmp_.outputs['Value'], fin.inputs['Factor']); _lin(nt, verde, fin.inputs['A']); _lin(nt, paglia, fin.inputs['B'])
    _lin(nt, fin.outputs['Result'], b.inputs['Base Color'])
    foschia(m)
    o = bpy.data.objects.new('ciuffo', me); o.location = (0, 0, -800); bpy.context.scene.collection.objects.link(o); o.data.materials.append(m)
    return o

def erba_vicino(self, s=0.0, lat=0.0, raggio=14.0, densita=70.0, n=None, secca=None, cella=1.2, seme=11):
    """Ciuffi d'erba veri attorno a un punto (fuori dalla pista): sistema di particelle con un ciuffo istanziato."""
    if secca is None: secca = min(1.0, self.suolo[1] + self.suolo[2] * 0.6)
    c = self.tr.pos(s, lat); R = raggio; bm = bmesh.new(); k = int(2 * R / cella)
    for i in range(k):
        for j in range(k):
            x0 = c.x - R + i * cella; y0 = c.y - R + j * cella; cx, cy = x0 + cella / 2, y0 + cella / 2
            if (cx - c.x) ** 2 + (cy - c.y) ** 2 > R * R: continue
            ss, tt, zr = self.tr.vicino(cx, cy)
            if abs(tt) < GHIAIA + 0.25: continue
            if self.fiume and abs(tt - self.lat_fiume(ss)) < self.larg_fiume(ss) * 1.2 + 0.5: continue
            vs = [bm.verts.new((x, y, self.quota(x, y) - 0.03)) for x, y in ((x0, y0), (x0 + cella, y0), (x0 + cella, y0 + cella), (x0, y0 + cella))]
            bm.faces.new(vs)
    me = bpy.data.meshes.new('erba_emettitore'); bm.to_mesh(me); bm.free()
    em = AN.collega(bpy.data.objects.new('erba_emettitore', me))
    ps = em.modifiers.new('erba', 'PARTICLE_SYSTEM').particle_system; st = ps.settings
    if n is None: n = int(min(160000, math.pi * R * R * densita * 0.8))
    st.type = 'EMITTER'; st.count = n; st.frame_start = 1; st.frame_end = 1; st.lifetime = 100000; st.emit_from = 'FACE'; st.use_even_distribution = True
    st.physics_type = 'NO'; st.render_type = 'OBJECT'; st.instance_object = _tuft(secca); st.particle_size = 1.25; st.size_random = 0.6
    st.normal_factor = 0.0; st.use_rotations = True; st.rotation_mode = 'GLOB_Z'; st.phase_factor = 0.0; st.phase_factor_random = 2.0; st.rotation_factor_random = 0.0
    st.use_modifier_stack = False
    em.show_instancer_for_render = False; em.show_instancer_for_viewport = False
    random.seed(seme); ps.seed = seme
    return em
Mondo.erba_vicino = erba_vicino

def _carta(file, vista, nviste, asp, alt):
    me = bpy.data.meshes.new('carta'); bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    w = alt * asp; vs = [bm.verts.new((-w / 2, 0, 0)), bm.verts.new((w / 2, 0, 0)), bm.verts.new((w / 2, 0, alt)), bm.verts.new((-w / 2, 0, alt))]
    f = bm.faces.new(vs); u0, u1 = vista / nviste, (vista + 1) / nviste
    for l, (u, v) in zip(f.loops, ((u0, 0), (u1, 0), (u1, 1), (u0, 1))): l[uv].uv = (u, v)
    bm.to_mesh(me); bm.free(); return me

def mat_carta(file, luminosita=1.0, emiss=0.35):
    if file in _MATCARTE: return _MATCARTE[file]
    m = bpy.data.materials.new(file); m.use_nodes = True; nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    im = _n(nt, 'ShaderNodeTexImage'); im.image = bpy.data.images.load(A + 'alberi/%s.webp' % file, check_existing=True); im.interpolation = 'Linear'
    b.inputs['Roughness'].default_value = 1.0
    try: b.inputs['Specular IOR Level'].default_value = 0.0
    except KeyError: pass
    mul = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mul.inputs['Factor'].default_value = 1.0; _lin(nt, im.outputs['Color'], mul.inputs['A']); mul.inputs['B'].default_value = (luminosita,) * 3 + (1,)
    _lin(nt, mul.outputs['Result'], b.inputs['Base Color'])
    _lin(nt, mul.outputs['Result'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emiss
    foschia(m)                                                           # la nebbia colora il materiale; l'alfa si applica DOPO (Transparent) così fuori dalla chioma non resta un rettangolo
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); src = out.inputs['Surface'].links[0].from_socket
    tr = _n(nt, 'ShaderNodeBsdfTransparent'); mx = _n(nt, 'ShaderNodeMixShader'); _lin(nt, im.outputs['Alpha'], mx.inputs['Fac']); _lin(nt, tr.outputs[0], mx.inputs[1]); _lin(nt, src, mx.inputs[2]); _lin(nt, mx.outputs[0], out.inputs['Surface'])
    _MATCARTE[file] = m; return m

def vegetazione(self, s0=-100.0, s1=320.0, densita=1.0, vicino=11.0, lontano=230.0, seme=21, luminosita=1.15):
    """Alberi e cespugli = le foto del gioco (assets/alberi) su carte incrociate, con le specie e la densità del bioma."""
    dens, mix = BIOMI[self.k]; random.seed(seme); cache = {}; n_tot = 0
    nomi = list(mix); pesi = [mix[x] for x in nomi]
    for lato in (-1, 1):
        s = s0
        while s < s1:
            s += 10.0
            for banda, quanti, t0, t1 in (('v', dens * 7.5 * densita, vicino, 85.0), ('l', dens * 5.0 * densita, 85.0, lontano)):
                n = int(quanti) + (1 if random.random() < quanti - int(quanti) else 0)
                for _ in range(n):
                    ss = s + random.uniform(-5, 5); tt = lato * (t0 + (t1 - t0) * random.random() ** 1.4)
                    if self.fiume and abs(tt - self.lat_fiume(ss)) < self.larg_fiume(ss) * 2.2 + 1.0: continue
                    if self.gola and self.gola[0] - 8 <= ss <= self.gola[1] + 8 and abs(tt - self.gola[2]) < self.gola[3] * 1.2: continue
                    sp = random.choices(nomi, pesi)[0]; files, nv, asp, alts, _ = CARTE[sp]; q = random.randrange(3)
                    conif = sp in ('abete', 'pino', 'larice')
                    if conif and abs(tt) < 26: tt = lato * (26 + random.random() * 40)
                    alt = alts[q] * (0.7 + random.random() * 0.6 if sp != 'cespuglio' else 0.7 + random.random() * 0.8) * (0.62 if conif else 1.0)
                    key = (files[q], random.randrange(nv), round(alt, 1))
                    if key not in cache: cache[key] = _carta(files[q], key[1], nv, asp, alt)
                    p = self.tr.pos(ss, tt); z = self.quota(p.x, p.y) - CARTE[sp][4][q] * (alt / alts[q]) + 0.15
                    lum = {'pino': 2.0, 'abete': 1.35, 'larice': 1.25, 'latifoglia': 1.45, 'cespuglio': 1.5}[sp] * luminosita / 1.15
                    for yaw in (random.uniform(0, 90), random.uniform(0, 90) + 90):
                        o = bpy.data.objects.new('albero', cache[key]); o.location = (p.x, p.y, z); o.rotation_euler.z = math.radians(yaw); o.scale = (1, 1, 1)
                        bpy.context.scene.collection.objects.link(o); o.data.materials.clear() if False else None
                        if not o.data.materials: o.data.materials.append(mat_carta(files[q], lum, 0.03 if self.k == 11 else (0.12 if self.k == 10 else 0.35)))
                    n_tot += 1
    return n_tot
Mondo.vegetazione = vegetazione

def nuvole(self, n=16, colore=None, forza=2.6, quota=(5.0, 34.0), seme=31, dimensione=1700.0, solo_settore=None):
    random.seed(seme); m = bpy.data.materials.new('nuvola'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = _n(nt, 'ShaderNodeOutputMaterial'); em = _n(nt, 'ShaderNodeEmission'); tr = _n(nt, 'ShaderNodeBsdfTransparent'); mx = _n(nt, 'ShaderNodeMixShader')
    im = _n(nt, 'ShaderNodeTexImage'); im.image = bpy.data.images.load(A + 'alberi/nuvole.webp', check_existing=True)
    tc = _n(nt, 'ShaderNodeTexCoord'); mp = _n(nt, 'ShaderNodeMapping'); _lin(nt, tc.outputs['UV'], mp.inputs['Vector']); _lin(nt, mp.outputs['Vector'], im.inputs['Vector'])
    col = colore or (1, 1, 1)
    tint = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); tint.inputs['Factor'].default_value = 1.0; _lin(nt, im.outputs['Color'], tint.inputs['A']); tint.inputs['B'].default_value = tuple(col) + (1,)
    _lin(nt, tint.outputs['Result'], em.inputs['Color']); em.inputs['Strength'].default_value = forza
    _lin(nt, im.outputs['Alpha'], mx.inputs['Fac']); _lin(nt, tr.outputs[0], mx.inputs[1]); _lin(nt, em.outputs[0], mx.inputs[2]); _lin(nt, mx.outputs[0], out.inputs['Surface'])
    for i in range(n):
        az = random.uniform(0, math.tau) if not solo_settore else math.radians(random.uniform(*solo_settore)); el = math.radians(random.uniform(*quota)); R = random.uniform(3000, 5500)
        p = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * R
        tile = random.randrange(6); u0, v0 = (tile % 3) / 3, 0.5 - (tile // 3) * 0.5
        w = dimensione * random.uniform(0.7, 1.5)
        bm = bmesh.new(); uv = bm.loops.layers.uv.new(); h = w * 0.625
        vs = [bm.verts.new(v) for v in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]; f = bm.faces.new(vs)
        for l, (u, v) in zip(f.loops, ((u0, v0), (u0 + 1 / 3, v0), (u0 + 1 / 3, v0 + 0.5), (u0, v0 + 0.5))): l[uv].uv = (u, v)
        me = bpy.data.meshes.new('nuvola'); bm.to_mesh(me); bm.free(); o = AN.collega(bpy.data.objects.new('nuvola', me), m)
        o.location = p; o.rotation_euler = (-p).to_track_quat('Y', 'Z').to_euler(); o.visible_shadow = False
Mondo.nuvole = nuvole

def montagne(self, colore='#8795ab', altezza=330.0, raggio=6200.0, settore=(0, 360), seme=41, massimo=0.80, righe=5):
    random.seed(seme); a0, a1 = settore; cols = int(abs(a1 - a0) / 1.0) + 1; bm = bmesh.new(); rows = []
    for i in range(cols):
        th = math.radians(a0 + (a1 - a0) * i / (cols - 1)); x, y = math.cos(th) * raggio, math.sin(th) * raggio
        r = 1 - abs(noise.noise(Vector((x * 0.0006, y * 0.0006, seme))) * 1.6); r2 = noise.noise(Vector((x * 0.004, y * 0.004, seme + 4))) * 0.16 + noise.noise(Vector((x * 0.012, y * 0.012, seme + 9))) * 0.05
        h = altezza * max(0.10, 0.15 + 0.85 * r * r * r + r2)
        rows.append([bm.verts.new((x, y, -60 + (h + 60) * q / (righe - 1))) for q in range(righe)])
    for a, b in zip(rows[:-1], rows[1:]):
        for q in range(righe - 1): bm.faces.new((a[q], b[q], b[q + 1], a[q + 1]))
    me = bpy.data.meshes.new('montagne'); bm.to_mesh(me); bm.free()
    m = bpy.data.materials.new('montagne'); m.use_nodes = True; b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = hexc(colore); b.inputs['Roughness'].default_value = 1.0
    try: b.inputs['Specular IOR Level'].default_value = 0.0
    except KeyError: pass
    foschia(m, massimo); o = AN.collega(bpy.data.objects.new('montagne', me), m); o.visible_shadow = False
    for p_ in me.polygons: p_.use_smooth = True
    return o
Mondo.montagne = montagne

def ger(pos, yaw=0.0, scala=1.0):
    """La tenda mongola: parete di feltro, tetto conico, anello, porta dipinta."""
    bm = bmesh.new(); R, Hw, Hc = 2.7, 1.55, 1.25
    bmesh.ops.create_cone(bm, cap_ends=True, segments=28, radius1=R, radius2=R, depth=Hw); bmesh.ops.translate(bm, vec=(0, 0, Hw / 2), verts=bm.verts)
    me = bpy.data.meshes.new('ger_parete'); bm.to_mesh(me); bm.free()
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=28, radius1=R * 1.06, radius2=0.45, depth=Hc); bmesh.ops.translate(bm, vec=(0, 0, Hw + Hc / 2 - 0.02), verts=bm.verts)
    me2 = bpy.data.meshes.new('ger_tetto'); bm.to_mesh(me2); bm.free()
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = (v.co.x * 0.95, v.co.y * 0.12 - R, v.co.z * 1.25 + 0.62)
    me3 = bpy.data.meshes.new('ger_porta'); bm.to_mesh(me3); bm.free()
    def mm(nome, c, r=1.0): 
        m = bpy.data.materials.new(nome); m.use_nodes = True; b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); b.inputs['Base Color'].default_value = c; b.inputs['Roughness'].default_value = r
        try: b.inputs['Specular IOR Level'].default_value = 0.0
        except KeyError: pass
        foschia(m); return m
    root = bpy.data.objects.new('ger', None); bpy.context.scene.collection.objects.link(root)
    for me_, mat in ((me, mm('feltro', (0.55, 0.52, 0.45, 1))), (me2, mm('tela_tetto', (0.62, 0.60, 0.55, 1))), (me3, mm('porta_ger', (0.30, 0.05, 0.02, 1), 0.6))):
        for p_ in me_.polygons: p_.use_smooth = me_ is not me3
        o = bpy.data.objects.new(me_.name, me_); bpy.context.scene.collection.objects.link(o); o.data.materials.append(mat); o.parent = root
    root.location = pos; root.rotation_euler.z = math.radians(yaw); root.scale = (scala,) * 3
    return root


# =====================================================================================================================
#  PEZZI DI SET: rocce, rovine, stupa, luci della città, pozza — e il vestito di ogni tappa
# =====================================================================================================================
def mat_semplice(nome, colore, rough=1.0, nebbia=True, emissione=None, forza=1.0):
    m = bpy.data.materials.new(nome); m.use_nodes = True; b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = colore; b.inputs['Roughness'].default_value = rough
    try: b.inputs['Specular IOR Level'].default_value = 0.05
    except KeyError: pass
    if emissione: b.inputs['Emission Color'].default_value = emissione; b.inputs['Emission Strength'].default_value = forza
    if nebbia: foschia(m)
    return m

def mat_roccia(nome='roccia', rosso=False):
    m = bpy.data.materials.new(nome); m.use_nodes = True; nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); b.inputs['Roughness'].default_value = 0.95
    geo = _n(nt, 'ShaderNodeNewGeometry'); nz = _n(nt, 'ShaderNodeTexNoise', noise_dimensions='3D'); nz.inputs['Scale'].default_value = 0.7; nz.inputs['Detail'].default_value = 8
    _lin(nt, geo.outputs['Position'], nz.inputs['Vector'])
    wv = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z'); wv.inputs['Scale'].default_value = 0.35; wv.inputs['Distortion'].default_value = 6.0; _lin(nt, geo.outputs['Position'], wv.inputs['Vector'])
    c1, c2 = ((0.10, 0.045, 0.035, 1), (0.26, 0.12, 0.08, 1)) if rosso else ((0.11, 0.10, 0.095, 1), (0.30, 0.26, 0.22, 1))
    mx = _n(nt, 'ShaderNodeMix', data_type='RGBA'); mx.inputs['A'].default_value = c1; mx.inputs['B'].default_value = c2; _lin(nt, nz.outputs['Fac'], mx.inputs['Factor'])
    st = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); st.inputs['Factor'].default_value = 0.6; _lin(nt, mx.outputs['Result'], st.inputs['A']); _lin(nt, wv.outputs['Fac'], st.inputs['B'])
    _lin(nt, st.outputs['Result'], b.inputs['Base Color']); foschia(m); return m

def masso(pos, dim, seme=1, yaw=0.0, rosso=False, subd=3):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=subd, radius=1.0)
    for v in bm.verts:
        n = noise.noise(v.co * 1.6 + Vector((seme, seme * 2, seme * 3))); n2 = noise.noise(v.co * 4.5 + Vector((seme, 0, 0)))
        v.co = v.co * (1 + 0.38 * n + 0.08 * n2); v.co.z = max(v.co.z, -0.35)
    me = bpy.data.meshes.new('masso'); bm.to_mesh(me); bm.free()
    o = AN.collega(bpy.data.objects.new('masso', me), mat_roccia(rosso=rosso)); o.location = pos; o.scale = dim; o.rotation_euler.z = math.radians(yaw)
    for p_ in me.polygons: p_.use_smooth = True
    return o

def muro(a, b, h, sp=0.9, seme=1, z=0.0):
    """Muro di mattoni crudi (rovine di Khar Balgas): da a a b (x,y), alto h, cima spezzata."""
    a, b = Vector(a), Vector(b); L = (b - a).length; d = (b - a).normalized(); n = Vector((-d.y, d.x))
    bm = bmesh.new(); k = max(2, int(L / 0.8)); rows = []
    for i in range(k + 1):
        u = i / k; c = a + (b - a) * u; hh = h * (0.45 + 0.55 * abs(noise.noise(Vector((c.x * 0.4, c.y * 0.4, seme)))) * 1.6)
        hh = min(h, hh)
        rows.append([bm.verts.new((c.x + n.x * s_, c.y + n.y * s_, zz)) for s_, zz in ((-sp / 2, z - 0.4), (sp / 2, z - 0.4), (sp / 2, z + hh), (-sp / 2, z + hh))])
    for r0, r1 in zip(rows[:-1], rows[1:]):
        for q in range(4): bm.faces.new((r0[q], r0[(q + 1) % 4], r1[(q + 1) % 4], r1[q]))
    bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1])
    me = bpy.data.meshes.new('muro'); bm.to_mesh(me); bm.free()
    m = bpy.data.materials.new('terra_cruda'); m.use_nodes = True; nt = m.node_tree; bs = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'); bs.inputs['Roughness'].default_value = 1.0
    geo = _n(nt, 'ShaderNodeNewGeometry'); nz = _n(nt, 'ShaderNodeTexNoise', noise_dimensions='3D'); nz.inputs['Scale'].default_value = 1.4; nz.inputs['Detail'].default_value = 9; _lin(nt, geo.outputs['Position'], nz.inputs['Vector'])
    wv = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z'); wv.inputs['Scale'].default_value = 2.2; wv.inputs['Distortion'].default_value = 4.0; _lin(nt, geo.outputs['Position'], wv.inputs['Vector'])
    mx = _n(nt, 'ShaderNodeMix', data_type='RGBA'); mx.inputs['A'].default_value = (0.20, 0.125, 0.075, 1); mx.inputs['B'].default_value = (0.34, 0.23, 0.14, 1); _lin(nt, nz.outputs['Fac'], mx.inputs['Factor'])
    st = _n(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); st.inputs['Factor'].default_value = 0.35; _lin(nt, mx.outputs['Result'], st.inputs['A']); _lin(nt, wv.outputs['Fac'], st.inputs['B'])
    _lin(nt, st.outputs['Result'], bs.inputs['Base Color']); foschia(m)
    return AN.collega(bpy.data.objects.new('muro', me), m)

def rovine(self, s=40.0, lato=1, lat0=22.0, seme=5):
    random.seed(seme)
    for i in range(7):
        c = self.tr.pos(s + i * 7.0 + random.uniform(-3, 3), lato * (lat0 + random.uniform(0, 24))); ang = random.uniform(0, math.pi); L = random.uniform(5, 14)
        a = (c.x - math.cos(ang) * L / 2, c.y - math.sin(ang) * L / 2); b = (c.x + math.cos(ang) * L / 2, c.y + math.sin(ang) * L / 2)
        muro(a, b, random.uniform(2.2, 5.5), seme=i + seme, z=self.quota(c.x, c.y))
Mondo.rovine = rovine

def stupe(self, s0=-30.0, s1=140.0, lat=15.5, passo=11.0, lanterne=True):
    s = s0; i = 0
    while s < s1:
        for lato in (-1, 1):
            p = self.punto(s + (passo / 2 if lato > 0 else 0), lato * (lat + (i % 2) * 1.8)); st = AN.stupa((p.x, p.y, p.z), scala=1.15 + 0.15 * (i % 3), yaw=i * 37 + lato * 11)
            for q in st.data.materials: foschia(q)
            if lanterne:
                q = self.punto(s, lato * 6.0); AN.sfera((q.x, q.y, q.z + 1.25), 0.16, mat_semplice('lanterna', (0, 0, 0, 1), nebbia=False, emissione=hexc('#ffa860'), forza=30.0))
        s += passo; i += 1
    for ss, ll in ((6, 5.8), (-14, -5.8), (30, 5.8), (52, -5.8)):
        q = self.punto(ss, ll); AN.lampada((q.x, q.y, q.z + 1.5), energia=260, colore='#ffb060')
Mondo.stupe = stupe

def luci_citta(self, s=520.0, n=90, seme=7):
    random.seed(seme); m = mat_semplice('luce_citta', (0, 0, 0, 1), nebbia=False, emissione=hexc('#ffb868'), forza=70.0)
    for i in range(n):
        p = self.tr.pos(s + random.uniform(-60, 80), random.uniform(-190, 190)); AN.sfera((p.x, p.y, self.quota(p.x, p.y) + random.uniform(0.6, 5)), random.uniform(0.7, 1.3), m)
Mondo.luci_citta = luci_citta

def pozza(self, s=6.0, lat=6.8, r=2.3):
    c = self.punto(s, lat); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, radius=r, segments=48)
    me = bpy.data.meshes.new('pozza'); bm.to_mesh(me); bm.free(); o = AN.collega(bpy.data.objects.new('pozza', me), mat_semplice('acqua_pozza', (0.015, 0.025, 0.04, 1), rough=0.02, nebbia=False)); o.location = (c.x, c.y, c.z + 0.05)
    cm = mat_semplice('cerchio', (0.6, 0.7, 1, 1), nebbia=False, emissione=hexc('#9aa8ff'), forza=2.5)
    for q in (0.5, 1.0, 1.5, 2.0):
        bpy.ops.mesh.primitive_torus_add(major_radius=q, minor_radius=0.016, location=(c.x, c.y, c.z + 0.07), major_segments=48, minor_segments=6); bpy.context.object.data.materials.append(cm)
Mondo.pozza = pozza

def gregge(self, s=30.0, lat=-30.0, n=7, seme=3):
    random.seed(seme)
    for i in range(n):
        p = self.punto(s + random.uniform(-9, 9), lat + random.uniform(-9, 9)); animale('pecora', (p.x, p.y, p.z), frame=random.randrange(150), yaw=random.uniform(0, 360), scala=1.0, nome='pecora%d' % i)
    p = self.punto(s + 12, lat - 6); animale('mucca', (p.x, p.y, p.z), frame=40, yaw=random.uniform(0, 360), nome='mucca')
Mondo.gregge = gregge

def gola_acqua(self):
    """Fiume rosso di Ulaan Tsutgalan: scorre a monte sul terreno, precipita dal bordo della gola e prosegue in fondo."""
    g0, g1, gl, gw, gp = self.gola; tr = self.tr; mat = materiale_acqua(rosso=True); W = 4.4
    def nastro(s_a, s_b, f):
        bm = bmesh.new(); prev = None; n = max(2, int(abs(s_b - s_a) / 3.0))
        for i in range(n + 1):
            s = s_a + (s_b - s_a) * i / n; a = tr.pos(s, gl - W); b = tr.pos(s, gl + W); r = (bm.verts.new((a.x, a.y, f(s, a))), bm.verts.new((b.x, b.y, f(s, b))))
            if prev: bm.faces.new((prev[0], prev[1], r[1], r[0]))
            prev = r
        me = bpy.data.meshes.new('fiume_rosso'); bm.to_mesh(me); bm.free(); return AN.collega(bpy.data.objects.new('fiume_rosso', me), mat)
    nastro(g0 - 170, g0 + 3, lambda s, p: self.quota(p.x, p.y) + 0.22)                      # a monte, sul terreno
    nastro(g0 + 6, g1, lambda s, p: tr.pos(s, 0).z - gp + 0.9)                              # a valle, in fondo alla gola
    a = tr.pos(g0 + 3.5, gl - W); b = tr.pos(g0 + 3.5, gl + W); zt = self.quota(a.x, a.y) + 0.2; zb = tr.pos(g0 + 3.5, 0).z - gp + 0.9
    bm = bmesh.new(); v = [bm.verts.new(q) for q in ((a.x, a.y, zt), (b.x, b.y, zt), (b.x, b.y, zb), (a.x, a.y, zb))]; bm.faces.new(v)
    me = bpy.data.meshes.new('cascata'); bm.to_mesh(me); bm.free(); AN.collega(bpy.data.objects.new('cascata', me), mat)
    c = tr.pos(g0 + 7, gl); AN.polvere((c.x, c.y, zb + 1.6), n=70, raggio=7, size=(0.8, 2.2), colore=(0.9, 0.85, 0.82, 1), alfa=0.07, schiaccia=0.9)
Mondo.gola_acqua = gola_acqua

def veste(m, completo=True, densita=1.0, erba=(0.0, 0.0, 16.0), nuvole=True, pezzi=True):
    """Il vestito di ogni tappa: alberi, erba, nuvole, montagne e i pezzi che la riconoscono."""
    k = m.k; el = LUCE_T[k][0]
    m.vegetazione(densita=densita)
    if erba: m.erba_vicino(s=erba[0], lat=erba[1], raggio=erba[2])
    sole = hexc(LUCE_T[k][4])[:3]
    if nuvole and not NUV.get(k): m.nuvole(n=14 if k < 10 else 4, colore=tuple(0.55 + 0.45 * c for c in sole) if k < 11 else (0.08, 0.09, 0.14), forza=3.4 if k < 10 else 0.6)
    m.montagne(altezza={2: 650, 7: 450, 8: 800, 5: 110, 3: 160}.get(k, 260), colore='#8795ab' if k < 9 else ('#6a6a85' if k == 9 else '#22263a'), massimo=0.8)
    if m.fiume: m.acqua()
    if not pezzi: return m
    if k in (0, 1, 3, 4):
        for i, (s, l) in enumerate(((30, -34), (60, 52), (-10, 70))): 
            p = m.punto(s, l); ger((p.x, p.y, p.z), yaw=random.uniform(0, 360), scala=1.0)
        m.gregge(s=34, lat=-30)
    if k in (2, 7, 8):
        for i in range(14):
            p = m.punto(random.uniform(-60, 200), random.choice((-1, 1)) * random.uniform(16, 60)); masso(p, (random.uniform(1.5, 5), random.uniform(1.5, 5), random.uniform(1.2, 4.5)), seme=i, yaw=random.uniform(0, 360), rosso=(k == 7))
    if k == 5:
        for i, (s, l, r_, h_) in enumerate(((50, -45, 40, 8), (110, 60, 55, 11), (-20, -90, 60, 13))):
            p = m.punto(s, l); AN.duna((p.x, p.y, p.z - 0.5), r_, h_, yaw=random.uniform(-20, 20), colore=(0.30, 0.20, 0.10, 1))
        for i in range(10): animale('lama', m.punto(40 + i * 3, -35 - i * 2), frame=i * 11, yaw=random.uniform(0, 360)) if i == 0 else None
    if k == 9: m.rovine(s=30, lato=1); m.rovine(s=70, lato=-1, seme=9)
    if k == 10: m.stupe()
    if k == 11: m.luci_citta(); m.pozza()
    return m

BELLE = {   # tappa → (az luce, luna az, eroe frame, camera: s, lat, h, mira s, mira lat, mira h, focale)
    0: dict(az=262, cam=(-8.5, 3.2, 0.85, 7.0, -1.0, 1.45, 40), frame=12),
    9: dict(az=266, cam=(-7.5, -4.5, 1.1, 4.0, 0.5, 1.4, 45), frame=6),
    11: dict(az=88, luna_az=88, luna_el=21, cam=(10.0, 5.0, 0.9, 0.0, 0.0, 1.5, 38), frame=6),
}

def scena_tappa(k, az=None, eroe_frame=6, camp=24, curva=0.7, colline=1.0, cam='lato', seme=3.0, risoluzione=None, luna_az=None, luna_el=24.0):
    nuovo(campioni=camp)
    m = Mondo(k, curva=curva, colline=colline, seme=seme + k)
    az_def = {0: 262, 1: 235, 2: 250, 3: 250, 4: 232, 5: 250, 6: 232, 7: 250, 8: 260, 9: 266, 10: 262, 11: 280}
    luce(m, az if az is not None else az_def[k], luna_az=luna_az, luna_el=luna_el)
    random.seed(k * 7 + 1); veste(m)
    eroe_su(m, 0, 0, frame=eroe_frame)
    if cam == 'lato': cam_su(m, 8.0, -5.0, 1.3, -3.0, 0.0, 1.35, 35)
    elif isinstance(cam, tuple): cam_su(m, *cam)
    if risoluzione: bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = risoluzione
    return m

# =====================================================================================================================
#  PROVE
# =====================================================================================================================
def scena(k, az=250.0, curva=0.6, colline=1.0, eroe_s=0.0, cam=None, eroe_frame=6, esposizione=0.0, kw_veg=True, **kw):
    nuovo(esposizione=0.0, campioni=kw.pop('campioni', 24))
    m = Mondo(k, curva=curva, colline=colline, **kw)
    luce(m, az, esposizione)
    if kw_veg: m.vegetazione(); m.erba_vicino(s=eroe_s, lat=0, raggio=16); m.nuvole(n=40); m.montagne()
    eroe_su(m, eroe_s, 0.0, frame=eroe_frame)
    if cam is None: cam_su(m, eroe_s + 9.0, -5.2, 1.5, eroe_s - 4.0, 0.0, 1.5, 35)
    else: cam(m)
    return m

if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    out = os.path.abspath(a[0]); os.makedirs(out, exist_ok=True); modo = a[1] if len(a) > 1 else 'griglia'
    if modo.isdigit():
        k = int(modo); t0 = time.time(); scena(k); print('COSTRUITA in %.1f s' % (time.time() - t0)); t0 = time.time(); scatta(os.path.join(out, 'kit_%02d.jpg' % k)); print('RENDER %.1f s' % (time.time() - t0))
    elif modo == 'beauty':
        for k, B in BELLE.items():
            t0 = time.time(); scena_tappa(k, az=B['az'], eroe_frame=B['frame'], camp=64, cam=B['cam'], risoluzione=(2560, 1072), luna_az=B.get('luna_az'), luna_el=B.get('luna_el', 24.0))
            t1 = time.time(); scatta(os.path.join(out, 'beauty_%02d.jpg' % k)); print('BEAUTY', k, 'build %.1f s' % (t1 - t0), 'render EEVEE 2560x1072 64 campioni: %.1f s' % (time.time() - t1))
    elif modo == 'griglia':
        for k in range(12):
            t0 = time.time(); scena_tappa(k); t1 = time.time(); scatta(os.path.join(out, 'tappa_%02d.jpg' % k)); print('TAPPA', k, 'build %.1f s' % (t1 - t0), 'render %.1f s' % (time.time() - t1))
    elif modo == 'tempi':
        B = BELLE[0]; scena_tappa(0, az=B['az'], eroe_frame=B['frame'], camp=64, cam=B['cam'], risoluzione=(2560, 1072))
        sc = bpy.context.scene
        # il .blend della scena, da aprire in Blender (immagini con percorso relativo)
        blend = os.path.join(out, 'kit-alba.blend'); bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
        try: bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
        except Exception as e: print('percorsi assoluti:', e)
        t0 = time.time(); scatta(os.path.join(out, 'tempi_eevee.jpg')); print('TEMPO EEVEE 2560x1072 64 campioni: %.1f s' % (time.time() - t0))
        # Cycles (Metal): il sole lo dà il cielo, la lampada si spegne
        for o in bpy.data.objects:
            if o.type == 'LIGHT' and o.data.type == 'SUN': o.data.energy = 0.0
        sc.render.engine = 'CYCLES'
        try:
            pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'METAL'; pr.get_devices()
            for d in pr.devices: d.use = True
            sc.cycles.device = 'GPU'
        except Exception as e: print('niente GPU', e)
        sc.cycles.samples = 64; sc.cycles.use_denoising = True; sc.cycles.use_adaptive_sampling = True
        t0 = time.time(); scatta(os.path.join(out, 'tempi_cycles.jpg')); print('TEMPO CYCLES 2560x1072 64 campioni + denoise: %.1f s' % (time.time() - t0))
