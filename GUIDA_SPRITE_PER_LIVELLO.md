# Guida Produzione Sprite per Livello

## Come Funziona

Il gioco e' una corsa pseudo-3D. Ai lati della strada appaiono oggetti (alberi, cartelloni, rocce, colonne) che scorrono mentre il cavallo avanza. Ogni livello del live ha un tema visivo diverso, quindi gli oggetti ai lati della strada cambiano: nel livello CANTIERE ci saranno gru e betoniere al posto degli alberi, nel livello DIGGIEI ci saranno casse audio e palle disco, ecc.

Ogni sprite che crei sostituira' uno sprite originale. Il gioco usa le dimensioni dell'originale per calcolare quanto grande appare sullo schermo, quindi **le proporzioni (aspect ratio) del tuo sprite devono corrispondere a quelle dell'originale che stai sostituendo**.

---

## Regole Generali

### Formato File
- **PNG** con sfondo trasparente (RGBA)
- Nessun altro formato accettato

### Dimensioni
- **Rispetta le proporzioni** dell'originale (vedi tabella sotto)
- Puoi lavorare a qualsiasi risoluzione, ma l'aspect ratio deve essere quello indicato
- Risoluzione consigliata: **2x le dimensioni originali** per qualita' nitida (es. se l'originale e' 200x315, lavora a 400x630)
- Non andare sotto le dimensioni originali

### Stile
- Lo stile originale e' **pixel art retro** a bassa risoluzione
- Non sei obbligato a replicare lo stile pixel art - puoi usare illustrazioni, disegni, foto stilizzate, qualsiasi cosa funzioni per il live
- L'importante e' che l'oggetto sia **riconoscibile** anche quando appare piccolo sullo schermo e sfreccia via velocemente
- Usa **forme chiare e contrastate** - dettagli troppo fini non si vedranno

### Composizione
- L'oggetto deve essere **ancorato in basso al centro** dell'immagine
- Il punto di contatto col "terreno" deve essere al bordo inferiore del PNG
- Lo sfondo deve essere **completamente trasparente**
- Non lasciare troppo spazio vuoto intorno all'oggetto

### Ancoraggio Visivo
```
     ___
    |   |      <-- L'oggetto puo' estendersi in qualsiasi direzione
    |   |
    | X |      <-- Ma la BASE deve essere centrata in basso
    |___|
  ===========  <-- Bordo inferiore del PNG = livello del terreno
```

---

## I 22 Sprite da Produrre per Ogni Livello

### GRUPPO A - Elementi Alti (appaiono come "alberi" ai lati della strada)

Questi sono gli oggetti piu' visibili e frequenti. Appaiono su entrambi i lati della strada, a distanze variabili, e creano la "scenografia" principale.

| Nome File | Dimensioni Originali | Proporzione | Ruolo | Frequenza |
|-----------|---------------------|-------------|-------|-----------|
| `PALM_TREE.png` | 215 x 540 | **1:2.5** (molto alto e stretto) | Elemento alto principale, appare spesso vicino alla strada | Altissima |
| `TREE1.png` | 360 x 360 | **1:1** (quadrato) | Elemento medio, chioma larga | Alta |
| `TREE2.png` | 282 x 295 | **1:1** (quasi quadrato) | Elemento medio variante | Alta |
| `DEAD_TREE1.png` | 135 x 332 | **1:2.5** (alto e stretto) | Elemento alto secondario, scheletrico | Media |
| `DEAD_TREE2.png` | 150 x 260 | **1:1.7** (alto) | Elemento alto variante | Media |

**Cosa diventano per livello:**

- **BULLONCINO**: Ciminiere, torri metalliche, serbatoi verticali, gru a traliccio
- **HANNO FALLITO**: Piloni rotti, antenne storte, edifici crollati, alberi glitchati
- **ODORE DEL BUONGIORNO**: Funghi giganti, alberi marci con mosche, piante palustri alte
- **CANTIERE**: Gru, ponteggi/impalcature, piloni in costruzione, torri di cemento
- **SEGRETO DEL RAP**: Lampioni urbani, torri di casse audio, antenne con graffiti, pali della luce
- **COME TU DICI**: Colonne di bolle, alghe giganti, coralli alti, geyser d'acqua
- **DIGGIEI**: Torri di speaker, pali con luci stroboscopiche, colonne di fumo colorato

---

### GRUPPO B - Elementi Bassi (appaiono come "cespugli" e vegetazione bassa)

Riempiono gli spazi tra gli elementi alti. Sono piu' piccoli e appaiono in grande quantita'.

| Nome File | Dimensioni Originali | Proporzione | Ruolo | Frequenza |
|-----------|---------------------|-------------|-------|-----------|
| `BUSH1.png` | 240 x 155 | **1.5:1** (largo e basso) | Cespuglio / elemento basso principale | Altissima |
| `BUSH2.png` | 232 x 152 | **1.5:1** (largo e basso) | Cespuglio variante | Altissima |
| `CACTUS.png` | 235 x 118 | **2:1** (molto largo e basso) | Elemento basso e largo | Alta |
| `STUMP.png` | 195 x 140 | **1.4:1** (leggermente largo) | Elemento piccolo a terra | Media |

**Cosa diventano per livello:**

- **BULLONCINO**: Bidoni industriali, scatole metalliche, ingranaggi a terra, tubi spezzati
- **HANNO FALLITO**: Macerie basse, schegge, resti di muri, cavi aggrovigliati
- **ODORE DEL BUONGIORNO**: Funghi bassi, pozzanghere, cumuli di rifiuti, mosche
- **CANTIERE**: Sacchi di cemento, mucchi di sabbia, cassette attrezzi, coni stradali piccoli
- **SEGRETO DEL RAP**: Boombox a terra, lattine di spray, scarpe appese, vinili
- **COME TU DICI**: Conchiglie, stelle marine, piccoli coralli, ciottoli bagnati
- **DIGGIEI**: Casse piccole, grovigli di cavi, bottiglie, ghiaccio secco con fumo

---

### GRUPPO C - Ostacoli (appaiono come rocce e strutture solide)

Elementi di media grandezza che danno varieta' al paesaggio. Appaiono sia vicini che lontani dalla strada.

| Nome File | Dimensioni Originali | Proporzione | Ruolo | Frequenza |
|-----------|---------------------|-------------|-------|-----------|
| `BOULDER1.png` | 168 x 248 | **1:1.5** (piu' alto che largo) | Ostacolo verticale | Media |
| `BOULDER2.png` | 298 x 140 | **2:1** (largo e basso) | Ostacolo orizzontale | Media |
| `BOULDER3.png` | 320 x 220 | **1.5:1** (largo) | Ostacolo grande | Media |
| `COLUMN.png` | 200 x 315 | **1:1.6** (alto, tipo colonna) | Struttura ripetuta ai bordi strada | Altissima |

**Nota su COLUMN**: Questo sprite e' speciale - appare ripetuto regolarmente lungo tutto il tracciato come una fila continua di colonne ai bordi strada. E' l'elemento piu' "architettonico".

**Cosa diventano per livello:**

- **BULLONCINO**: Blocchi di acciaio, container, travi d'acciaio, silos piccoli
- **HANNO FALLITO**: Televisori rotti, barriere divelte, statue crollate, blocchi di cemento
- **ODORE DEL BUONGIORNO**: Tronchi marci, cumuli di fango, bidoni rovesciati, sacchi di spazzatura
- **CANTIERE**: Jersey barrier (new jersey), coni stradali grandi, betoniere, cassonetti
- **SEGRETO DEL RAP**: Amplificatori, giradischi giganti, blocchi di cemento con graffiti, idranti
- **COME TU DICI**: Ancore, forzieri sommersi, massi coperti di alghe, conchiglie giganti
- **DIGGIEI**: Amplificatori Marshall, casse sub-bass, generatori, frigoriferi per bevande

---

### GRUPPO D - Cartelloni/Billboard (appaiono come insegne e poster)

Cartelloni pubblicitari ai lati della strada. Perfetti per scritte, loghi, simboli tematici. Appaiono meno frequentemente ma sono molto visibili.

| Nome File | Dimensioni Originali | Proporzione | Ruolo |
|-----------|---------------------|-------------|-------|
| `BILLBOARD01.png` | 300 x 170 | **1.8:1** (panoramico) | Cartellone largo |
| `BILLBOARD02.png` | 215 x 220 | **1:1** (quadrato) | Cartellone quadrato |
| `BILLBOARD03.png` | 230 x 220 | **1:1** (quadrato) | Cartellone quadrato |
| `BILLBOARD04.png` | 268 x 170 | **1.6:1** (largo) | Cartellone largo |
| `BILLBOARD05.png` | 298 x 190 | **1.6:1** (largo) | Cartellone largo |
| `BILLBOARD06.png` | 298 x 190 | **1.6:1** (largo) | Cartellone largo |
| `BILLBOARD07.png` | 298 x 190 | **1.6:1** (largo) | Cartellone largo |
| `BILLBOARD08.png` | 385 x 265 | **1.5:1** (largo grande) | Cartellone grande |
| `BILLBOARD09.png` | 328 x 282 | **1.2:1** (quasi quadrato) | Cartellone grande |

**Cosa diventano per livello:**

- **BULLONCINO**: Segnali "PERICOLO", cartelli industriali, targhe di fabbrica, indicazioni macchinari
- **HANNO FALLITO**: Poster di propaganda strappati, schermate di errore, manifesti vandalizzati, segni "SYSTEM FAILURE"
- **ODORE DEL BUONGIORNO**: Cartelli "VIETATO DISCARICA" marciti, poster coperti di mosche, insegne arrugginite
- **CANTIERE**: Cartelli "LAVORI IN CORSO", planimetrie, segnali sicurezza, avvisi di cantiere
- **SEGRETO DEL RAP**: Poster rap/hip-hop, insegne neon, graffiti murali, locandine concerti
- **COME TU DICI**: Cartelli "ATTENZIONE CORRENTE", bolle decorative, segnali marini, mappe nautiche
- **DIGGIEI**: Locandine DJ set, insegne club neon, poster festa, loghi "DIGGIEI"

---

## Riepilogo Quantita' per Livello

Per completare un livello servono **22 PNG**:

| Gruppo | Quanti | Nomi File |
|--------|--------|-----------|
| A - Alti | 5 | PALM_TREE, TREE1, TREE2, DEAD_TREE1, DEAD_TREE2 |
| B - Bassi | 4 | BUSH1, BUSH2, CACTUS, STUMP |
| C - Ostacoli | 4 | BOULDER1, BOULDER2, BOULDER3, COLUMN |
| D - Cartelloni | 9 | BILLBOARD01 - BILLBOARD09 |
| **Totale** | **22** | |

**Per tutti e 7 i livelli: 154 PNG in totale.**

Non sei obbligato a fare tutti e 22 per ogni livello. Quelli mancanti useranno lo sprite originale (albero, roccia, ecc). Ma piu' ne fai, piu' il livello sara' immersivo.

**Priorita' di produzione** (cosa fare prima per massimo impatto):
1. `PALM_TREE` + `TREE1` + `COLUMN` (sono ovunque, cambiarli trasforma la scena)
2. `BUSH1` + `BUSH2` (riempiono gli spazi)
3. `BILLBOARD08` + `BILLBOARD01` (i cartelloni piu' grandi e visibili)
4. Tutto il resto

---

## Dove Mettere i File

Ogni livello ha la sua cartella:

```
images/levels/
  1-bulloncino/          <-- PNG del livello 1
  2-hanno-fallito/       <-- PNG del livello 2
  3-odore-del-buongiorno/
  4-cantiere/
  5-segreto-del-rap/
  6-come-tu-dici/
  7-diggiei/
```

I nomi dei file DEVONO essere esattamente quelli nella tabella, **in maiuscolo con estensione .png**:
```
PALM_TREE.png
TREE1.png
TREE2.png
DEAD_TREE1.png
DEAD_TREE2.png
BUSH1.png
BUSH2.png
CACTUS.png
STUMP.png
BOULDER1.png
BOULDER2.png
BOULDER3.png
COLUMN.png
BILLBOARD01.png
BILLBOARD02.png
BILLBOARD03.png
BILLBOARD04.png
BILLBOARD05.png
BILLBOARD06.png
BILLBOARD07.png
BILLBOARD08.png
BILLBOARD09.png
```

---

## Checklist Rapida per Ogni Sprite

- [ ] Formato PNG con sfondo trasparente
- [ ] Proporzioni corrette (vedi tabella del gruppo)
- [ ] Oggetto ancorato in basso al centro
- [ ] Forme chiare e contrastate (deve leggersi anche da piccolo)
- [ ] Nome file esatto in MAIUSCOLO (es. `TREE1.png`, non `tree1.png`)
- [ ] Salvato nella cartella corretta del livello
