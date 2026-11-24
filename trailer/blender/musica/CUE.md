# Cue sheet della musica a 165 BPM

1 s = 2,75 battiti, 4 s = 11 battiti esatti; battito = 0.3636 s = 8.73 fotogrammi, semicroma = 2.18 fotogrammi.
Le frasi ripartono su un taglio: **downbeat 1 = 5,5 s (S08), downbeat 2 = 14,5 s (S15), downbeat 3 = 23,5 s (S25)**. «Scarto» = quanto il taglio
cade lontano dalla semicroma più vicina della sua frase, in fotogrammi (0 = esattamente sulla griglia, ±1 = un fotogramma, che a video non si nota).

| Shot | Taglio (s) | Fotogramma | Battiti dal downbeat | Scarto (fotogrammi) | La musica |
|---|---|---|---|---|---|
| S03 | 0.00 | 0 | 0.000 | +0.0 | cori in Re minore, boato lontano; cresce |
| S04 | 2.00 | 48 | 5.500 | +0.0 | STOP (nastro che si ferma, disco che gratta); zoom a scatto; dita dei piedi |
| S05 | 3.50 | 84 | 9.625 | +1.1 | SILENZIO |
| S06 | 4.50 | 108 | 12.375 | -1.1 | gambe a vuoto (ronzio che sale); 5,0 la musica riparte più forte, whoosh |
| S08 | 5.50 | 132 | 0.000 | +0.0 | DOWNBEAT 1 (frase 1, mezzo tempo): cassa che scoppia 5,75; presa della sciabola 6,375 |
| S09a | 7.00 | 168 | 4.125 | +1.1 | sciabola: shing + stab; scintilla 7,33 |
| S09b | 7.50 | 180 | 5.500 | +0.0 | mazza: giro, TAC a 7,83 |
| S09c | 8.00 | 192 | 6.875 | -1.1 | frusta: SCHIOCCO a 8,21 |
| S09d | 8.50 | 204 | 8.250 | +0.0 | arco: twang a 8,625, freccia |
| S10 | 9.00 | 216 | 9.625 | +1.1 | zoccoli (tom) + riser |
| S11 | 9.50 | 228 | 11.000 | +0.0 | scontro a 10,1; rallentatore (musica giù); cade rigido a 10,58 |
| S13a | 11.00 | 264 | 15.125 | +1.1 | rotolo; lampo 11,25 |
| S13b | 11.50 | 276 | 16.500 | +0.0 | mazza a 11,75; bolle che scoppiano a catena fino a ~12,4 (musica bassa) |
| S14 | 12.50 | 300 | 19.250 | +0.0 | STOP; birra sui pattini (squittii), doppia presa 13,4–13,5, sbandata 13,5–14; riser dalle 14,1 |
| S15 | 14.50 | 348 | 0.000 | +0.0 | DOWNBEAT 2 (frase 2, cassa su ogni battito): stab La |
| S16 | 15.00 | 360 | 1.375 | -1.1 | stab Sol |
| S18 | 15.50 | 372 | 2.750 | +0.0 | stab Fa |
| S19 | 16.00 | 384 | 4.125 | +1.1 | stab Mi |
| S20 | 16.50 | 396 | 5.500 | +0.0 | stab Re grave, poi la musica si spegne (nastro che rallenta); tonfi della terra a 16,67 · 17,0 · 17,33 · 17,63 |
| S21 | 18.00 | 432 | 9.625 | +1.1 | orrore finto: bordone, un tonfo ogni mezzo secondo (18,0 … 20,5) |
| S22 | 19.00 | 456 | 12.375 | -1.1 | tonfi; gamba fuori passo 20,0–20,3 |
| S23 | 21.00 | 504 | 17.875 | -1.1 | riser; ruggito 21,3–22,4; vapore |
| S24 | 22.50 | 540 | 22.000 | +0.0 | colpo d'orchestra, riser; scintilla della lama 22,9 |
| S25 | 23.50 | 564 | 0.000 | +0.0 | DOWNBEAT 3 (frase 3, la carica): ottoni |
| S26 | 24.50 | 588 | 2.750 | +0.0 | SNAP 24,625 (tutto si ferma), tosse 24,92 |
| S27 | 25.50 | 612 | 5.500 | +0.0 | salto al rallentatore: cori, reverse, boato di sub |
| fermo | 26.50 | 636 | 8.250 | +0.0 | fermo immagine: STOP (nastro che si ferma), la coda di riverbero si spegne entro 27,45 |
| nero | 27.50 | 660 | 11.000 | +0.0 | silenzio assoluto fino a 29,0 (i titoli) |
| S28 | 29.00 | 696 | 15.125 | +1.1 | la birra sui pattini attraversa il nero; tintinnio a 29,62 |

## In Ableton
- Imposta il tempo a **165** e importa `guida-165bpm.mid` all'inizio del brano: la traccia «Tempo e cue» ha i marcatori (nome shot e istante), «Click 165» un colpo a ogni battito (più forte sul primo di ogni battuta) e «Tagli» una nota a ogni taglio.
- Il video parte dal secondo 0 = battuta 1: nessun offset. Le frasi 2 e 3 non cadono su una battuta intera (14,5 s = battito 39,875; 23,5 s = battito 64,625): se vuoi le battute allineate, sposta il downbeat della frase sul taglio e lascia che la griglia scorra (è ciò che fa la bozza).
- `trailer-30s-musica-bozza.wav` è la bozza sintetizzata (tutto da numpy, `tools/trailer3d/musica165.py`): serve per sentire i tempi, i suoni veri si rifanno. `stem/` ha batteria, basso, musica, effetti e riverbero separati, sommati danno il master.
- Loudness della bozza: -12 LUFS al massimo, guadagno statico (la dinamica resta); non è mixata come un master.
