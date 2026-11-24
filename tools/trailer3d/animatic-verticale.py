# ANIMATIC VERTICALE (storyboard v2, 23 nov): 30 s in 9:16, tono comico. Un fotogramma per shot (S09 e S13 ne hanno più d'uno),
# nei set del kit e con le pose del rig del trailer, inquadrati per il verticale: le cose alte riempiono il quadro.
# Le gag dello storyboard sono già nei fotogrammi: la sagoma di polvere lasciata alla partenza (S06), il predone che cade rigido
# (S11), la doppia presa davanti alla birra (S14), la gamba del Boss fuori passo (S22), il Boss che tossisce la polvere (S26),
# lo sguardo in macchina (S05, S14, S27), la birra che attraversa il nero (S28).
#
# uso:  blender -b --python tools/trailer3d/animatic-verticale.py -- <cartella uscita> [S05 S22 … | tutti]
# Anteprima a 720×1280 (il formato vero è 1080×1920: stessa inquadratura, solo più pixel).
import bpy, sys, os, math, random
QUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, QUI)
import animatic as AN
import animatic2 as A2
import kit, pose
from mathutils import Vector
from animatic import hexc, oggetto, animale, polvere, zolle, scintille, lampada, camera
from animatic2 import P, E, C, B, mondo, notte_boss

AN.W, AN.H = 720, 1280
CYCLES = {'S03', 'S04', 'S05', 'S06', 'S18'}
STORIA = ['S03', 'S04', 'S05', 'S06', 'S08', 'S09a', 'S09b', 'S09c', 'S09d', 'S10', 'S11', 'S13a', 'S13b', 'S14',
          'S15', 'S16', 'S18', 'S19', 'S20', 'S21', 'S22', 'S23', 'S24', 'S25', 'S26', 'S27', 'S28']
TINTE = dict(arancio='#ffc9a3', azzurro='#a9c8ff', verde='#d6ffb3', rosa='#ffb3d1')

S = {}
def shot(*nomi):
    def d(f):
        for n in nomi: S[n] = f
        return f
    return d

def rivale(m, x, y, colore, azione='Gallop', frame=0, yaw=None, rot=(0, 0, 0), nome='predone'):
    """Un predone con le tinte del gioco SMORZATE (decisione del 23 nov)."""
    return AN.predone(P(m, x, y), pose.tinta_smorzata(TINTE[colore], 0.35), azione, frame, A2.yaw_su(m, x, y) if yaw is None else yaw, 0.46, nome, rot)

def guarda_in_macchina(info, dist, alto=0.1, lens=60, fstop=None):
    """Camera davanti al muso, nella direzione in cui guarda la testa (orizzontale): il cavallo guarda in macchina."""
    mu, nu = info['muso'], info['nuca']
    d = (mu - nu); d.z = 0; d.normalize()
    mira = mu * 0.6 + nu * 0.4
    pos = mira + d * dist + Vector((0, 0, alto))
    return camera(pos, mira, lens, fuoco=mira if fstop else None, fstop=fstop)

def nuvola_sagoma(radice, n=160, colore=(0.80, 0.62, 0.44, 1), alfa=0.45, seme=4):
    """La gag di S06: la mesh cotta del cavallo diventa polvere (un fantasma color terra) + sbuffi sparsi sulla superficie."""
    random.seed(seme)
    mat = AN.materiale_polvere(colore, alfa)
    corpo = next(o for o in radice.children if o.type == 'MESH')
    corpo.data.materials.clear(); corpo.data.materials.append(mat)
    bpy.context.view_layer.update()
    vs = corpo.data.vertices; Mw = corpo.matrix_world
    mat2 = AN.materiale_polvere(colore, alfa * 0.45)
    for i in range(n):
        p = Mw @ vs[random.randrange(len(vs))].co
        p += Vector((random.gauss(0, 0.05), random.gauss(0, 0.05), random.gauss(0, 0.05)))
        AN.sfera(p, random.uniform(0.04, 0.13), mat2, 'sbuffo')

# ------------------------------------------------------------------------------------------------------- ATTO 1 · L'EROE (alba)
@shot('S03')
def s03():
    m = mondo(0, sole_rel=180)                                     # sole alle spalle del cavallo: controluce verso di noi
    E(m, 0, 0, 'Idle', 20)
    C(m, (0.35, -9.0, 0.35), (0, 0, -0.4), 50)                      # mira bassa: il cavallo sta in alto, la strada sotto

@shot('S04')
def s04():
    m = mondo(0, sole_rel=160, erba=None)
    m.erba_vicino(s=0, lat=7, raggio=7, densita=480)
    E(m, -7, 0, 'Idle', 30)
    C(m, (-7.55, -1.25, 0.18), (-7.0, -0.05, 0.42), 30, fstop=3.2, fuoco=(-7.0, -0.25, 0.2))

@shot('S05')
def s05():
    m = mondo(0, sole_rel=200)
    r, info = E(m, 0, 0, 'Idle', 12, sguardo=('Sguardo_D', 9))
    guarda_in_macchina(info, 1.55, alto=0.05, lens=55, fstop=2.8)

@shot('S06')
def s06():
    m = mondo(0, sole_rel=150)
    sag, _ = E(m, 0, 0, 'Gallop', 6)                               # dov'era: la sagoma di polvere
    nuvola_sagoma(sag)
    E(m, 0.3, -13, 'Gallop', 10)                                   # lui è già lontano
    zolle(P(m, 0, -0.3, 0.15), n=160, raggio=1.2, size=(0.004, 0.014))
    C(m, (-2.2, 5.5, 1.0), (0, -4.0, 1.0), 35)

# ------------------------------------------------------------------------------------------------------- ATTO 2 · ARMI E LOTTA
@shot('S08')
def s08():
    m = mondo(1, sole_rel=170)
    r, info = E(m, 0, 0, 'Gallop', 14, braccio=('Afferra', 8))
    h = info['presa'].translation
    random.seed(8); cart = AN.materiale('cartone', colore=hexc('#b98a55'), rough=0.85)
    for i in range(10):
        AN.scatola(P(m, random.uniform(-1.0, 0.6), random.uniform(-2.6, -1.0), random.uniform(0.6, 2.6)),
                   (random.uniform(0.25, 0.45), 0.012, random.uniform(0.2, 0.4)), cart, rot=(random.uniform(0, 90), random.uniform(0, 90), random.uniform(0, 180)))
    oggetto('models/armi/saber.glb', (h.x - 0.05, h.y - 0.15, h.z + 0.14), rot=(70, 0, 160), scala=1.0, nome='sciabola')
    lampada(P(m, -0.2, -1.8, 1.4), colore='#ffb060', energia=260, raggio=0.4)
    scintille(P(m, -0.2, -1.8, 1.5), n=40, raggio=1.0, colore='#c8955a', forza=3)
    C(m, (-0.95, 1.35, 2.05), (-0.42, -1.0, 1.75), 24)

@shot('S09a', 'S09b', 'S09c', 'S09d')
def s09(nome):
    m = mondo(1, sole_rel=-30, pezzi=False)
    f, rot, lung = dict(S09a=('saber', (8, 0, 12), 0.85), S09b=('mace', (6, 0, -18), 0.60), S09c=('whip', (4, 0, 12), 1.0), S09d=('bow', (0, 0, 14), 0.95))[nome]
    k = 1.5
    oggetto('models/armi/%s.glb' % f, P(m, 0, 0, 1.0), rot=rot, scala=k, nome='arma')
    if nome == 'S09d': oggetto('models/armi/freccia.glb', P(m, 0.12, 0.05, 1.0), rot=(0, 0, 14), scala=1.3, nome='freccia')
    cz = 1.0 + 0.5 * lung * k
    C(m, (-1.5, -2.3, cz + 0.1), (0, 0, cz), 55, fstop=2.0, fuoco=(0, 0, cz))

@shot('S10')
def s10():
    m = mondo(1, sole_rel=150)
    E(m, 0, 0, 'Gallop', 8, sguardo=('Sguardo_D', 3))
    rivale(m, -1.3, 3.5, 'arancio', frame=2, nome='p1'); rivale(m, 1.1, 7.0, 'azzurro', frame=9, nome='p2'); rivale(m, -0.6, 11.0, 'verde', frame=5, nome='p3')
    polvere(P(m, 0, 9, 0.6), n=80, raggio=5, size=(0.3, 0.9), alfa=0.04)
    C(m, (0.4, -14, 1.3), (-0.1, 4, 1.5), 85)

@shot('S11')
def s11():
    m = mondo(2, sole_rel=210)
    r, info = E(m, 0, 0, 'Gallop', 14, braccio=('Sciabola_Fendente', 11), arma='saber')
    t = info['punta']
    # il predone cade RIGIDO come un giocattolo: tutto d'un pezzo, di lato, le zampe dritte (clip Idle, non Death)
    rivale(m, t.x - 0.85, t.y + 0.2, 'azzurro', azione='Idle', frame=0, yaw=90, rot=(0, -58, 0), nome='rivale')
    scintille(t, n=60, raggio=0.6, forza=80); lampada(t, colore='#ffe0b0', energia=300, raggio=0.15)
    polvere(P(m, -1.4, 0.0, 0.4), n=80, raggio=2.0, size=(0.05, 0.2), alfa=0.30)
    C(m, (2.6, -5.6, 1.3), (t.x - 0.4, t.y + 0.3, 0.95), 30)

@shot('S13a')
def s13a():
    m = mondo(2, sole_rel=-170)
    oggetto('models/pluriball/rotolo.glb', P(m, 0, -4.6), yaw=30, scala=1.6, nome='rotolo')
    E(m, 0, -1.0, 'Gallop', 4)
    C(m, (1.4, -8.6, 0.45), (0, -3.0, 1.0), 30)

@shot('S13b')
def s13b():
    m = mondo(2, sole_rel=-130, pezzi=False)
    p, _ = AN.importa('models/pluriball/pony-skin.glb', nome='pony'); AN.metti(p, P(m, 0, 0))
    oggetto('models/armi/mace.glb', P(m, -0.95, -0.7, 1.0), rot=(0, 0, -62), scala=1.2, nome='mazza')
    scintille(P(m, -0.4, -0.45, 1.1), n=40, raggio=0.4, colore='#ffffff', forza=20)
    C(m, (-1.9, -2.5, 1.15), (-0.45, -0.45, 1.1), 70, fstop=3.0, fuoco=(-0.4, -0.45, 1.1))

@shot('S14')
def s14():
    m = mondo(2, sole_rel=150)
    pose.birra(P(m, -0.6, -1.4), yaw=70, scala=2.0, fase=0.27, forza=1.7, piega=7)
    # la doppia presa: si è girato a guardare noi, sbandando all'indietro sui piedi nudi
    r, info = E(m, 0.2, 1.0, 'Gallop', 16, sguardo=('Sguardo_D', 9), rot=(-9, 0, 0))
    polvere(P(m, 0.2, 1.3, 0.15), n=50, raggio=0.9, size=(0.06, 0.2), alfa=0.28, schiaccia=0.3)
    C(m, (-2.0, -3.1, 0.35), (0.1, 1.0, 1.15), 24)

# ------------------------------------------------------------------------------------------------------- ATTO 3 · IL VIAGGIO
# Stessa camera, stesso fotogramma di galoppo, mondo diverso: la ripetizione è la gag.
def profilo(m):
    E(m, 0, 0, 'Gallop', 2)
    C(m, (6.5, 0, 1.0), (0, 0, 1.3), 50)

@shot('S15')
def s15():
    m = mondo(3, sole_rel=120); profilo(m)

@shot('S16')
def s16():
    m = mondo(5, sole_rel=70)
    zc = m.quota(-34, 6.5) + 1.5
    animale('lama', (-34, 6.5, zc), frame=40, yaw=-60, scala=1.0, nome='lama_cresta')
    profilo(m)

@shot('S18')
def s18():
    m = mondo(9, sole_rel=90)
    animale('aquila', P(m, -12.0, 2.0, 7.5), azione='Flying', frame=12, yaw=-90, scala=0.45, nome='aquila')
    profilo(m)

@shot('S19')
def s19():
    m = mondo(10, sole_rel=90, esposizione=0.3); profilo(m)

@shot('S20')
def s20():
    m = mondo(11, luna_rel=-60, luna_el=38, pezzi=False)
    m.luci_citta(); m.pozza(s=3, lat=-1.5)
    E(m, 0, 0, 'Walk', 20)
    C(m, (2.6, -6.2, 0.4), (0.6, -0.6, 1.1), 24)

# ------------------------------------------------------------------------------------------------------- ATTO 4 · IL BOSS (notte)
@shot('S21')
def s21():
    m = notte_boss(180, 22); B(m, -3, 0, fase=0.3, passo=0.9)
    C(m, (-0.5, -9, 0.3), (-1.5, 0, 3.8), 40)

@shot('S22')
def s22():
    m = notte_boss(180, 28, 0.3)
    B(m, 0, 0, fase=0.22, passo=1.2, ginocchio=1.3, fuori={'Coscia_S2_D': 0.5})     # una gamba fuori passo
    C(m, (3.0, -1.6, 0.3), (-6.0, 0.2, 1.0), 24)

@shot('S23')
def s23():
    m = notte_boss(150, 24); B(m, 0, 0, mascella=40, testa=-26, alza=6, fase=0.5, passo=0.4)
    C(m, (7.4, -5.8, 2.1), (3.0, -0.7, 2.0), 50, fstop=2.8, fuoco=(3.2, -0.7, 2.0))

@shot('S24')
def s24():
    m = notte_boss(90, 30, 0.2)
    B(m, -4.0, 0, mascella=24, alza=-18, fase=0.4, passo=0.4, alto=1.3)
    E(m, 2.0, 0, 'Idle', 10, yaw=-90, braccio=('Sciabola_Alta', 24), arma='saber')
    C(m, (4.6, -0.8, 0.25), (-1.5, 0, 2.6), 18)

@shot('S25')
def s25():
    m = notte_boss(180, 18); B(m, -9, 0, fase=0.65, passo=1.4, mascella=16, alza=4)
    E(m, 1.8, 0, 'Gallop', 8, yaw=-90, braccio=('Sciabola_Alta', 24), arma='saber')
    polvere(P(m, -3.5, 0.3, 0.3), n=40, raggio=2.5, size=(0.15, 0.45), colore=(0.045, 0.05, 0.07, 1), alfa=0.04, schiaccia=0.35)
    C(m, (14.0, 1.8, 1.6), (-3.0, 0, 2.0), 85)

@shot('S26')
def s26():
    m = notte_boss(210, 22)
    r = B(m, 0, 0, mascella=20, alza=6, fase=0.8, passo=0.5)
    b = pose.bocca(r)
    polvere(b + Vector((0.45, 0, 0.05)), n=40, raggio=0.45, size=(0.06, 0.18), colore=(0.30, 0.31, 0.38, 1), alfa=0.20, schiaccia=0.8, seme=11)   # il colpo di tosse
    C(m, (6.6, -5.6, 1.5), (3.6, 0, 1.9), 35)

@shot('S27')
def s27():
    m = notte_boss(145, 70); B(m, 0, 0, fase=0.1, passo=0.8)       # la luna appena sopra il cavallo in volo
    E(m, -1.5, 0, 'Salto', 14, yaw=90, dz=5.0, braccio=('Sciabola_Alta', 24), sguardo=('Sguardo_D', 9), arma='saber')
    C(m, (-0.2, -1.8, 2.6), (-1.45, 0, 5.4), 20)

@shot('S28')
def s28():
    """Il nero, e la birra che lo attraversa: illuminata solo di taglio."""
    AN.nuovo(campioni=32)
    sc = bpy.context.scene
    w = bpy.data.worlds.new('nero'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1); sc.world = w
    pose.birra((0, 0, 0), yaw=0, scala=2.0, fase=0.25, forza=1.7, piega=3)
    lampada((0.6, 0.8, 1.0), colore='#ffd9a0', energia=900, raggio=0.2)
    lampada((-0.8, 0.7, 0.5), colore='#a0b8ff', energia=350, raggio=0.2)
    lampada((0.3, -1.5, 1.2), colore='#ffe6c0', energia=40, raggio=0.5)
    camera((0, -3.2, 0.45), (0, 0, 0.42), 50)

MOTORE = 'EEVEE'
if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    cartella = os.path.abspath(a[0]); os.makedirs(cartella, exist_ok=True)
    lista = STORIA if len(a) < 2 or a[1] == 'tutti' else a[1:]
    import time
    for nome in lista:
        A2.MOTORE = 'CYCLES' if nome in CYCLES else 'EEVEE'
        t0 = time.time(); f = S[nome]; f(nome) if f.__code__.co_argcount else f()
        if A2.MOTORE == 'CYCLES': A2.usa_cycles()
        t1 = time.time(); AN.scatta(os.path.join(cartella, nome + '.jpg'))
        print('SHOT', nome, A2.MOTORE, 'scena %.1f s' % (t1 - t0), 'render %.1f s' % (time.time() - t1))
