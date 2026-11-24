"""MAPPA DEL TRAILER (storia IG 1080x1920, 30 fps, 30 s) — la condividono musica.py e monta.py.

120 BPM: un battito = 0,5 s = 15 fotogrammi, una battuta = 2 s. Ogni taglio cade su un battito o su una croma,
e ogni colpo che si vede (frusta, mazza, calcio, sciabola, morso) cade su un colpo della musica.

Struttura alla hollywoodiana:
  ATTO 1  0,0-7,0    tensione: drone, orologio, zoccoli lontani, gola (canto difonico), due BRAAM, due cartelli
  ATTO 2  7,0-18,75  azione: taiko, ostinato d'archi, armi una dopo l'altra, poi tagli a croma e a semicroma
  BUCO    18,75-19,5 nero e silenzio: «QUALCOSA SI È SVEGLIATO» e un ringhio
  ATTO 3  19,5-25,5  il Boss a pezzi: fauci, gambe, l'ombra alle spalle, il morso; tre colpi secchi
  TITOLO  25,5-30,0  BOOM, titolo, la chiusura delle fauci, PROSSIMAMENTE
"""
BPM = 120
BEAT = 60 / BPM
FPS = 30
DUR = 30.0

# --- i tagli: (inizio, fine, ripresa, sorgente) ---------------------------------------------------------------------
# sorgente = lista di (t_uscita, t_ripresa): punti di una curva di velocità. Fra due punti il tempo della ripresa
# avanza in linea retta (pendenza 1 = tempo reale, 0,25 = rallentatore 4×). Il tempo della ripresa è in secondi di
# gioco dall'inizio della ripresa (vedi riprese.js: gli eventi «eventi» stanno su quell'asse).
# fx: effetti del taglio (vedi monta.py): zoom = (da, a) ingrandimento, punch = istante del colpo (scossone+lampo),
#     scuro = quanto scurire, scuoti = scossa continua
TAGLI = [
    # ATTO 1
    dict(t=(0.00, 2.00), r='a1_testa_notte', s=[(0.00, 0.10), (2.00, 1.10)], zoom=(1.12, 1.0), entra_dal_nero=0.9, luce=1.35),
    dict(t=(2.00, 3.50), r='a2_alba_galoppo', s=[(2.00, 0.40), (3.50, 1.15)], zoom=(1.0, 1.08), punch=2.00),
    dict(t=(4.50, 5.75), r='a3_rivali_tramonto', s=[(4.50, 0.40), (5.75, 1.65)], zoom=(1.0, 1.06), punch=4.50),
    dict(t=(6.50, 7.50), r='a4_sciabola_alzata', s=[(6.50, 0.40), (7.00, 0.90), (7.20, 0.95), (7.50, 1.25)], zoom=(1.0, 1.12), punch=7.00),
    # ATTO 2
    dict(t=(7.50, 8.50), r='b1_frusta', s=[(7.50, 0.30), (8.50, 1.30)], punch=7.75),
    dict(t=(8.50, 9.50), r='b2_mazza', s=[(8.50, 0.20), (9.00, 0.70), (9.30, 0.775), (9.50, 0.975)], punch=9.00, zoom=(1.0, 1.1)),
    dict(t=(9.50, 10.75), r='b3_calcio', s=[(9.50, 0.10), (10.00, 0.60), (10.25, 0.66), (10.75, 1.16)], punch=10.00),
    dict(t=(11.50, 12.50), r='b4_arco', s=[(11.50, 0.15), (12.50, 1.15)], punch=11.50, zoom=(1.0, 1.08)),
    dict(t=(12.50, 14.00), r='b6_mischia', s=[(12.50, 0.25), (14.00, 1.75)], punch=12.50),
    dict(t=(14.00, 15.00), r='b7_notte_branco', s=[(14.00, 0.80), (15.00, 1.80)], punch=14.00, luce=1.6),
    dict(t=(15.00, 16.00), r='b5_sciabola_colpo', s=[(15.00, 0.45), (15.25, 0.70), (15.50, 0.7625), (16.00, 1.2625)], punch=15.25),
    # raffica a semiminime
    dict(t=(16.00, 16.25), r='b8_frusta_retro', s=[(16.00, 0.35), (16.25, 0.60)], punch=16.00, luce=1.3),
    dict(t=(16.25, 16.50), r='b1_frusta', s=[(16.25, 1.20), (16.50, 1.45)], punch=16.25),
    dict(t=(16.50, 16.75), r='b2_mazza', s=[(16.50, 0.66), (16.75, 0.76)], punch=16.50, zoom=(1.15, 1.2)),
    dict(t=(16.75, 17.00), r='b6_mischia', s=[(16.75, 2.25), (17.00, 2.50)], punch=16.75),
    # raffica a crome
    dict(t=(17.00, 17.125), r='b5_sciabola_colpo', s=[(17.00, 0.69), (17.125, 0.73)], punch=17.00, zoom=(1.25, 1.3)),
    dict(t=(17.125, 17.25), r='a3_rivali_tramonto', s=[(17.125, 2.20), (17.25, 2.33)], punch=17.125),
    dict(t=(17.25, 17.375), r='b3_calcio', s=[(17.25, 0.62), (17.375, 0.70)], punch=17.25, zoom=(1.2, 1.25)),
    dict(t=(17.375, 17.50), r='b7_notte_branco', s=[(17.375, 2.20), (17.50, 2.33)], punch=17.375, luce=1.6),
    dict(t=(17.50, 17.625), r='b2_mazza', s=[(17.50, 0.70), (17.625, 0.74)], punch=17.50, zoom=(1.3, 1.35)),
    dict(t=(17.625, 17.75), r='a2_alba_galoppo', s=[(17.625, 1.80), (17.75, 1.93)], punch=17.625),
    dict(t=(17.75, 17.875), r='b8_frusta_retro', s=[(17.75, 1.10), (17.875, 1.23)], punch=17.75, luce=1.3),
    dict(t=(17.875, 18.00), r='b4_arco', s=[(17.875, 1.05), (18.00, 1.18)], punch=17.875),
    # salita finale: il galoppo che si stringe
    dict(t=(18.00, 18.75), r='a4_sciabola_alzata', s=[(18.00, 1.30), (18.75, 2.05)], zoom=(1.0, 1.45), scuoti=(0.0, 14.0)),
    # ATTO 3 — il Boss
    dict(t=(19.50, 21.00), r='c1_fauci', s=[(19.50, 0.35), (21.00, 1.85)], zoom=(1.0, 1.1), punch=19.50, freddo=True, luce=1.3),
    dict(t=(21.00, 21.75), r='c2_gambe', s=[(21.00, 0.30), (21.75, 1.05)], punch=21.00, freddo=True, luce=1.4),
    dict(t=(21.75, 23.25), r='c3_incombe', s=[(21.75, 0.80), (23.25, 2.30)], punch=21.75, freddo=True, scuro=0.08),
    dict(t=(23.25, 24.50), r='c4_morso', s=[(23.25, 0.60), (24.50, 1.85)], zoom=(1.0, 1.15), scuoti=(2.0, 10.0), freddo=True, luce=1.3),
    # tre colpi secchi
    dict(t=(24.50, 24.833), r='b5_sciabola_colpo', s=[(24.50, 0.69), (24.833, 0.78)], punch=24.50, zoom=(1.2, 1.3)),
    dict(t=(24.833, 25.167), r='c1_fauci', s=[(24.833, 1.60), (25.167, 1.95)], punch=24.833, zoom=(1.25, 1.35), freddo=True, luce=1.3),
    dict(t=(25.167, 25.40), r='b2_mazza', s=[(25.167, 0.69), (25.40, 0.75)], punch=25.167, zoom=(1.3, 1.4)),
    # TITOLO: sotto il titolo, al buio, il galoppo all'alba rallentato e sfocato
    dict(t=(25.50, 28.25), r='a2_alba_galoppo', s=[(25.50, 1.20), (28.25, 1.89)], sotto_titolo=True, zoom=(1.1, 1.2)),
    # la chiusura delle fauci: lo scatto finisce sul 28,75
    dict(t=(28.25, 28.80), r='c5_scatto_fauci', s=[(28.25, 0.07), (28.80, 0.62)], freddo=True, punch=28.75, luce=1.3),
]

# --- i cartelli (testo su nero) ----------------------------------------------------------------------------------------
CARTELLI = [
    dict(t=(3.50, 4.50), righe=['NELLA STEPPA']),
    dict(t=(5.75, 6.50), righe=['NON ESISTONO', 'REGOLE']),
    dict(t=(10.75, 11.50), righe=['HAI UNA', 'SOLA VITA']),
    dict(t=(18.95, 19.50), righe=['QUALCOSA', 'SI È SVEGLIATO']),
]
TITOLO = (25.50, 28.25)          # CAVALLI MONGOLI / THE GAME
CHIUSA = (28.95, 30.00)          # PROSSIMAMENTE

# --- i colpi della musica ----------------------------------------------------------------------------------------------
HIT = dict(
    apertura=0.00,
    braam1=2.00, braam2=4.50, cartello1=3.50, cartello2=5.75,
    riser1=(5.00, 7.00), azione=7.00,
    fine_azione=18.75, buco=(18.75, 19.50), ringhio=(18.90, 19.50),
    boss=19.50, boss2=21.00, boss3=21.75, riser2=(23.25, 24.50),
    stutter=(24.50, 24.833, 25.167), pre_titolo=(25.40, 25.50), titolo=25.50,
    scatto=28.75, fine=30.00,
)
# colpi di scena dentro l'atto 2 (impatti sincronizzati ai tagli)
IMPATTI = [7.00, 7.75, 9.00, 10.00, 11.50, 14.00, 15.25]
CARTELLO3 = (10.75, 11.50)       # i tamburi tacciono, resta l'ostinato
RAFFICA4 = (16.00, 17.00)        # semiminime
RAFFICA8 = (17.00, 18.00)        # crome
SALITA = (16.00, 18.75)
