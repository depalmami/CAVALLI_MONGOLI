# ANIMATIC v2: gli stessi shot dello storyboard (stesse inquadrature dell'animatic v1, animatic.py), girati nei SET del kit
# (kit.py): pista di terra, suolo e luce della tappa, alberi del gioco, erba, nuvole, montagne, pezzi di set.
# Alba e tramonto (S01–S05, S18) in Cycles, come deciso dopo la prova del kit (EEVEE con sole basso è piatto); il resto EEVEE.
# Dal 23 nov le pose vengono da pose.py (rig del trailer: braccio, armi in pugno, salto, sguardo; Boss che marcia; birra che pattina):
# è l'«animatic v3» (trailer/blender/animatic-v3/).
#
# uso:  blender -b --python tools/trailer3d/animatic2.py -- <cartella uscita> [S03 S09a … | tutti]
#
# Coordinate: quelle di mondo dell'animatic v1 (strada lungo -Y vicino all'origine, destra del cavallo = -X), con la quota presa
# dal terreno del kit; i lati del sole e della luna sono RELATIVI alla strada (0 = davanti, +90 = a destra, 180 = alle spalle).
import bpy, sys, os, math, random
QUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, QUI)
import animatic as AN
import kit
import pose
from animatic import hexc, importa, metti, oggetto, animale, predone, lampada, polvere, zolle, scintille, camera, scatta

CYCLES = {'S01', 'S02', 'S03', 'S04', 'S05', 'S18'}

def az_rel(m, s, rel):
    t = m.tr.tang(s); return math.degrees(math.atan2(t.y, t.x)) - rel

def mondo(k, sole_rel=0.0, curva=0.35, colline=0.3, esposizione=0.0, luna_rel=None, luna_el=24.0, seme=3.0, gola=None, **veste):
    AN.nuovo(campioni=24)
    m = kit.Mondo(k, curva=curva, colline=colline, seme=seme + k, gola=gola)
    kit.luce(m, az_rel(m, 0, sole_rel if luna_rel is None else luna_rel), esposizione, energia=0 if MOTORE == 'CYCLES' else None, luna_el=luna_el)
    random.seed(k * 7 + 1); kit.veste(m, **veste)
    return m

def P(m, x, y, dz=0.0): return (x, y, m.quota(x, y) + dz)
def yaw_su(m, x, y): return m.tr.yaw(m.tr.vicino(x, y)[0])

def E(m, x, y, azione='Gallop', frame=6, yaw=None, dz=0.0, braccio=None, sguardo=None, arma=None, rot=(0, 0, 0), **kw):
    """Il protagonista dal rig del trailer (pose.py): clip di corpo + braccio + sguardo, arma nella presa. Ritorna (radice, info)."""
    return pose.eroe(P(m, x, y, dz), yaw_su(m, x, y) if yaw is None else yaw, (azione, frame), braccio, sguardo, arma, rot=rot, **kw)

def R(m, x, y, tinta, azione='Gallop', frame=0, yaw=None, scala=0.46, nome='predone'):
    return predone(P(m, x, y), tinta, azione, frame, yaw_su(m, x, y) if yaw is None else yaw, scala, nome)

def C(m, a, b, lens, fstop=None, fuoco=None):
    pa = P(m, a[0], a[1], a[2]); pb = P(m, b[0], b[1], b[2]); pf = None if fuoco is None else P(m, *fuoco)
    return camera(pa, pb, lens, fuoco=pf, fstop=fstop)

def B(m, x, y, mascella=0.0, scala=1.35, yaw=0.0, **kw):
    """Il Boss da pose.py: fase del passo, passo, unisono, testa, alza (vedi pose.boss)."""
    return pose.boss(P(m, x, y), yaw, scala, mascella=mascella, **kw)

def usa_cycles(campioni=48, cpu=False):
    """Cycles sulla GPU (Metal). cpu=True aggiunge anche la CPU: sui chip Apple dà poca velocità in più e MOLTO calore (il 23 nov il
    render dell'atto 1 teneva la CPU al 941%), quindi di norma resta spenta."""
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'
    try:
        pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'METAL'; pr.get_devices()
        for d in pr.devices: d.use = cpu or d.type != 'CPU'
        sc.cycles.device = 'GPU'
    except Exception as e: print('niente GPU', e)
    sc.cycles.samples = campioni; sc.cycles.use_denoising = True; sc.cycles.use_adaptive_sampling = True

S = {}
def shot(*nomi):
    def d(f):
        for n in nomi: S[n] = f
        return f
    return d

TINTE = [(0.9, 0.62, 0.42), (0.38, 0.30, 0.26), (0.95, 0.9, 0.8), (0.55, 0.40, 0.30), (0.28, 0.22, 0.2), (0.8, 0.6, 0.4)]

# ---------------------------------------------------------------------------------------------------------------- ATTO 1
@shot('S01')
def s01():
    m = mondo(0, sole_rel=0)
    m.gregge(s=60, lat=36, n=6, seme=8)
    C(m, (-62, 62, 46), (-20, -80, 0), 24)

@shot('S02')
def s02():
    m = mondo(0, sole_rel=180, erba=(40, 0, 14), pezzi=False)
    random.seed(11)
    for i in range(11):
        R(m, random.uniform(-9, 8) + (i % 3) * 0.8, -40 + random.uniform(-5, 4), TINTE[i % 6], frame=(i * 5) % 14, yaw=-90, scala=0.47, nome='cavallo%d' % i)
    polvere(P(m, 1, -37, 0.9), n=70, raggio=9, size=(0.5, 1.2), colore=(0.9, 0.65, 0.4, 1), alfa=0.06)
    C(m, (0, -104, 1.4), (0, -40, 1.9), 135, fstop=4.0, fuoco=(0, -40, 1.7))

@shot('S03')
def s03():
    m = mondo(0, sole_rel=8)
    E(m, 0, 0, 'Idle', 20)
    random.seed(4)
    for i in range(6): R(m, -50 - i * 6, -150 - random.uniform(0, 14), (0.45, 0.33, 0.26), frame=i * 2, yaw=-90, scala=0.47, nome='lontano%d' % i)
    C(m, (-3.2, 8.5, 0.85), (1.0, -7.0, 1.45), 40)

@shot('S04')
def s04():
    m = mondo(0, sole_rel=-20, erba=None)
    m.erba_vicino(s=0, lat=7, raggio=7, densita=420)
    E(m, -7, 0, 'Idle', 30)
    C(m, (-7.9, -1.7, 0.14), (-7.0, -0.4, 0.5), 24, fstop=3.2, fuoco=(-7.0, -0.45, 0.2))

@shot('S05')
def s05():
    m = mondo(0, sole_rel=-20)
    E(m, 0, 0, 'Idle', 12)
    C(m, (-1.9, -2.7, 1.5), (-0.1, -0.65, 1.42), 100, fstop=3.2, fuoco=(-0.15, -0.65, 1.42))

# ---------------------------------------------------------------------------------------------------------------- ATTO 2
@shot('S06')
def s06():
    m = mondo(1, sole_rel=-15)
    E(m, 0, 1.0, 'Gallop', 6)
    zolle(P(m, 0, 0.2, 0.2), n=220, raggio=1.3, size=(0.004, 0.014)); polvere(P(m, 0, 1.0, 0.5), n=40, raggio=1.8, size=(0.2, 0.6), alfa=0.10)
    C(m, (0.35, -2.4, 0.22), (0, 0.6, 0.5), 24, fstop=4, fuoco=(0, 0.6, 0.4))

@shot('S07')
def s07():
    m = mondo(1, sole_rel=120)
    E(m, 0, 0, 'Gallop', 10)
    polvere(P(m, 0, 2.4, 0.3), n=60, raggio=1.4, size=(0.1, 0.35), alfa=0.25)
    C(m, (6.8, 0.2, 1.05), (0, -0.1, 0.95), 35, fstop=2.8, fuoco=(0, 0, 0.9))

@shot('S08')
def s08():
    m = mondo(1, sole_rel=170)
    r, info = E(m, 0, 0, 'Gallop', 14, braccio=('Afferra', 8))
    h = info['presa'].translation
    # la cassa è appena esplosa davanti al muso: pannelli di cartone in volo, la sciabola che gira sopra la mano
    random.seed(8); cart = AN.materiale('cartone', colore=hexc('#b98a55'), rough=0.85)
    for i in range(9):
        AN.scatola(P(m, random.uniform(-0.9, 0.7), random.uniform(-2.6, -1.2), random.uniform(0.5, 1.9)),
                   (random.uniform(0.25, 0.45), 0.012, random.uniform(0.2, 0.4)), cart, rot=(random.uniform(0, 90), random.uniform(0, 90), random.uniform(0, 180)))
    oggetto('models/armi/saber.glb', (h.x - 0.05, h.y - 0.18, h.z + 0.12), rot=(70, 0, 160), scala=1.0, nome='sciabola')
    lampada(P(m, -0.2, -1.8, 1.2), colore='#ffb060', energia=260, raggio=0.4)
    scintille(P(m, -0.2, -1.8, 1.2), n=40, raggio=1.0, colore='#c8955a', forza=3)
    C(m, (-1.35, 1.7, 2.0), (-0.45, -1.2, 1.45), 28)

@shot('S09a', 'S09b', 'S09c', 'S09d')
def s09(nome):
    m = mondo(1, sole_rel=-30)
    f, rot, lung = dict(S09a=('saber', (14, 0, 12), 0.85), S09b=('mace', (12, 0, -18), 0.60), S09c=('whip', (6, 0, 12), 1.0), S09d=('bow', (0, 0, 14), 0.95))[nome]
    k = 1.5
    oggetto('models/armi/%s.glb' % f, P(m, 0, 0, 1.0), rot=rot, scala=k, nome='arma')
    if nome == 'S09d': oggetto('models/armi/freccia.glb', P(m, 0.12, 0.05, 1.0), rot=(0, 0, 14), scala=1.3, nome='freccia')
    cz = 1.0 if nome == 'S09d' else 1.0 + 0.5 * lung * k
    C(m, (-1.5, -2.3, cz + 0.1), (0, 0, cz), 70, fstop=2.0, fuoco=(0, 0, cz))

@shot('S10')
def s10():
    m = mondo(1, sole_rel=120)
    E(m, 0, -1.5, 'Gallop', 8, sguardo=('Sguardo_D', 3))
    R(m, -3.4, 1.4, hexc('#ffc9a3')[:3], frame=2, nome='p1'); R(m, 3.4, 2.4, hexc('#a9c8ff')[:3], frame=9, nome='p2'); R(m, -0.4, 6.0, hexc('#d6ffb3')[:3], frame=5, nome='p3')
    polvere(P(m, 0, 8.5, 0.6), n=120, raggio=5, size=(0.4, 1.0), alfa=0.08)
    C(m, (7.5, -8.5, 2.3), (-0.3, 1.6, 1.2), 32)

@shot('S11')
def s11():
    m = mondo(2, sole_rel=210)
    r, info = E(m, 0, 0, 'Gallop', 14, braccio=('Sciabola_Fendente', 11), arma='saber')
    t = info['punta']
    R(m, t.x - 0.95, t.y + 0.15, hexc('#a9c8ff')[:3], azione='Attack_Headbutt', frame=12, yaw=90, nome='rivale')
    scintille(t, n=60, raggio=0.6, forza=80); lampada(t, colore='#ffe0b0', energia=300, raggio=0.15)
    polvere(P(m, -1.2, 0.3, 0.5), n=90, raggio=2.2, size=(0.05, 0.2), alfa=0.35)
    C(m, (3.2, -6.2, 1.5), (t.x - 0.2, t.y + 0.3, t.z), 40)        # davanti a sinistra: il predone resta DIETRO lo scontro

@shot('S12')
def s12():
    m = mondo(2, sole_rel=70)
    r, info = E(m, 0, 0, 'Gallop', 20, yaw=-8, braccio=('Frusta', 10), arma='whip')
    t = info['punta']
    R(m, -3.3, 0.6, hexc('#ffc9a3')[:3], azione='Attack_Kick', frame=10, yaw=90, nome='rivale')
    scintille(t, n=30, raggio=0.25, colore='#fff4e0', forza=40)
    polvere(P(m, -1.5, 0.8, 0.4), n=70, raggio=2.0, size=(0.05, 0.25), alfa=0.35)
    C(m, (0.6, -7.5, 1.3), (-1.4, 0.2, 1.2), 35)

@shot('S13a')
def s13a():
    m = mondo(2, sole_rel=-170)
    oggetto('models/pluriball/rotolo.glb', P(m, 0, -5.5), yaw=30, scala=1.6, nome='rotolo')
    E(m, 0, -1.0, 'Gallop', 4)
    C(m, (2.2, -9.5, 0.9), (0, -4.0, 0.7), 28)

@shot('S13b')
def s13b():
    m = mondo(2, sole_rel=-130)
    p, _ = importa('models/pluriball/pony-skin.glb', nome='pony'); metti(p, P(m, 0, 0))
    oggetto('models/armi/mace.glb', P(m, -0.95, -0.7, 1.0), rot=(0, 0, -62), scala=1.2, nome='mazza')
    scintille(P(m, -0.4, -0.45, 1.1), n=40, raggio=0.4, colore='#ffffff', forza=20)
    C(m, (-1.9, -2.5, 1.2), (-0.45, -0.45, 1.1), 85, fstop=3.0, fuoco=(-0.4, -0.45, 1.1))

@shot('S14')
def s14():
    m = mondo(2, sole_rel=150)
    pose.birra(P(m, -0.6, -2.4), yaw=65, scala=2.0, fase=0.27, forza=1.7, piega=7)
    E(m, 0.8, 2.6, 'Gallop', 16, sguardo=('Sguardo_D', 9))
    C(m, (-5.6, -3.2, 0.45), (0, -0.5, 0.6), 35)

# ---------------------------------------------------------------------------------------------------------------- ATTO 3
@shot('S15')
def s15():
    m = mondo(3, sole_rel=120)
    E(m, 0, 0, 'Gallop', 2)
    C(m, (7.2, 0.3, 1.1), (0, -0.2, 1.0), 35, fstop=4, fuoco=(0, 0, 1.0))

@shot('S16')
def s16():
    m = mondo(5, sole_rel=70)
    zc = m.quota(45, -50) - 0.5 + 8.0
    animale('lama', (45, -50, zc - 0.25), frame=40, yaw=10, scala=1.4, nome='lama_cresta')
    E(m, 8, -12, 'Gallop', 9)
    camera(P(m, -2, 0, 1.6), (45, -50, zc + 1.4), 50)

@shot('S17')
def s17():
    m = mondo(7, sole_rel=150, gola=(20, 170, -32, 20, 22), densita=0.6)
    m.gola_acqua()
    E(m, 9, -28, 'Gallop', 12)
    z0 = m.tr.pos(110, 0).z; z1 = m.tr.pos(24, 0).z
    camera((21, -118, z0 + 16), (31, -24, z1 - 9), 30)

@shot('S18')
def s18():
    m = mondo(9, sole_rel=-5)
    E(m, 0.5, -16, 'Gallop', 6)
    animale('aquila', P(m, -2.0, -7.0, 2.2), azione='Flying', frame=12, yaw=-35, scala=1.2, nome='aquila')
    C(m, (-1.0, 3.0, 2.6), (2.0, -40, 3.0), 45)

@shot('S19')
def s19():
    m = mondo(10, sole_rel=0, esposizione=0.3)
    E(m, 0, -5.5, 'Gallop', 4)
    C(m, (4.4, 3.5, 1.2), (-1.0, -10.0, 1.6), 35)

@shot('S20')
def s20():
    m = mondo(11, luna_rel=-60, luna_el=38, pezzi=False)
    m.luci_citta(); m.pozza(s=5, lat=-3.5)
    E(m, 0, 0, 'Walk', 20)
    C(m, (-4.8, 7.0, 1.0), (1.5, -6.0, 1.7), 28)

# ---------------------------------------------------------------------------------------------------------------- ATTO 4 (notte, il Boss)
def notte_boss(luna_rel, luna_el, esposizione=0.0):
    m = mondo(11, luna_rel=luna_rel, luna_el=luna_el, esposizione=esposizione, pezzi=False, densita=0.5, erba=(0, 0, 14))
    m.luci_citta(); return m

@shot('S21')
def s21():
    m = notte_boss(180, 9); B(m, -3, 0, fase=0.3, passo=0.9)
    C(m, (1.0, -24, 1.0), (-1.0, 0, 3.4), 40)

@shot('S22')
def s22():
    m = notte_boss(180, 28, 0.3); B(m, 0, 0, fase=0.22, passo=1.2, ginocchio=1.3)
    C(m, (-10.5, -2.6, 0.4), (4.0, -0.4, 1.0), 24)

@shot('S23')
def s23():
    m = notte_boss(150, 24); B(m, 0, 0, mascella=38, testa=-22, alza=5, fase=0.5, passo=0.4)
    C(m, (7.8, -8.2, 2.6), (3.0, 0, 1.9), 70, fstop=2.8, fuoco=(3.0, 0, 1.9))

@shot('S24')
def s24():
    m = notte_boss(120, 26); B(m, -8.5, -3.6, fase=0.4, passo=0.6)
    E(m, 14, 0, 'Idle', 10, yaw=-90, braccio=('Sciabola_Alta', 24), arma='saber')
    C(m, (-13.0, -7.2, 1.5), (14, 0, 1.6), 50, fstop=2.8, fuoco=(14, 0, 1.6))

@shot('S25')
def s25():
    m = notte_boss(180, 18); B(m, -9, 0, fase=0.65, passo=1.4, mascella=14, alza=4)
    E(m, 1.8, 0, 'Gallop', 8, yaw=-90, braccio=('Sciabola_Alta', 24), arma='saber')
    polvere(P(m, -1.0, 0.6, 0.35), n=60, raggio=3.0, size=(0.2, 0.6), colore=(0.045, 0.05, 0.07, 1), alfa=0.06, schiaccia=0.35)
    C(m, (-1.2, -46, 1.5), (-2.2, 0, 1.9), 135)

@shot('S26')
def s26():
    m = notte_boss(210, 22); B(m, 0, 0, mascella=6, alza=-8, fase=0.8, passo=0.5)
    polvere(P(m, 5.6, 0, 0.8), n=90, raggio=2.2, size=(0.12, 0.4), colore=(0.05, 0.055, 0.08, 1), alfa=0.08, schiaccia=0.6)
    C(m, (4.0, -9.5, 1.3), (5.0, 0, 1.8), 40)

@shot('S27')
def s27():
    m = notte_boss(152, 27); B(m, 0, 0, fase=0.1, passo=0.8)
    E(m, -1.5, 0, 'Salto', 14, yaw=90, dz=5.0, braccio=('Sciabola_Alta', 24), arma='saber')
    C(m, (0.9, -3.6, 2.6), (-1.4, 0, 5.15), 18)

STORIA = AN.STORIA
MOTORE = 'EEVEE'

if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    cartella = os.path.abspath(a[0]); os.makedirs(cartella, exist_ok=True)
    lista = STORIA if len(a) < 2 or a[1] == 'tutti' else a[1:]
    import time
    for nome in lista:
        MOTORE = 'CYCLES' if nome in CYCLES else 'EEVEE'
        t0 = time.time(); f = S[nome]; f(nome) if f.__code__.co_argcount else f()
        if MOTORE == 'CYCLES': usa_cycles()
        t1 = time.time(); scatta(os.path.join(cartella, nome + '.jpg')); print('SHOT', nome, MOTORE, 'scena %.1f s' % (t1 - t0), 'render %.1f s' % (time.time() - t1))
