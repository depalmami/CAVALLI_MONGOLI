# 🏇 Guida Sprite per Horse Racing Game

## 📋 Lista Completa Sprite Necessari (24 totali)

### Sistema di Naming
Tutti gli sprite seguono questo schema:
```
PLAYER_[UPHILL_]DIREZIONE_FRAME.png
```

Dove:
- **UPHILL_** = opzionale, presente solo per sprite in salita
- **DIREZIONE** = STRAIGHT | LEFT | RIGHT
- **FRAME** = 1 | 2 | 3 | 4 (ciclo di galoppo)

---

## 🎯 Sprite Necessari

### **GALOPPO IN PIANO (12 sprite)**

#### Dritto (Straight)
1. `PLAYER_STRAIGHT_1.png` - Frame 1: Zampe raccolte sotto il corpo
2. `PLAYER_STRAIGHT_2.png` - Frame 2: Estensione anteriore
3. `PLAYER_STRAIGHT_3.png` - Frame 3: Fase di volo (tutte le zampe sollevate)
4. `PLAYER_STRAIGHT_4.png` - Frame 4: Estensione posteriore

#### Svolta a Sinistra (Left)
5. `PLAYER_LEFT_1.png` - Frame 1: Zampe raccolte, inclinato a sinistra
6. `PLAYER_LEFT_2.png` - Frame 2: Estensione anteriore, inclinato a sinistra
7. `PLAYER_LEFT_3.png` - Frame 3: Fase di volo, inclinato a sinistra
8. `PLAYER_LEFT_4.png` - Frame 4: Estensione posteriore, inclinato a sinistra

#### Svolta a Destra (Right)
9. `PLAYER_RIGHT_1.png` - Frame 1: Zampe raccolte, inclinato a destra
10. `PLAYER_RIGHT_2.png` - Frame 2: Estensione anteriore, inclinato a destra
11. `PLAYER_RIGHT_3.png` - Frame 3: Fase di volo, inclinato a destra
12. `PLAYER_RIGHT_4.png` - Frame 4: Estensione posteriore, inclinato a destra

---

### **GALOPPO IN SALITA (12 sprite)**

#### Dritto in Salita
13. `PLAYER_UPHILL_STRAIGHT_1.png` - Frame 1: Zampe raccolte, prospettiva salita
14. `PLAYER_UPHILL_STRAIGHT_2.png` - Frame 2: Estensione anteriore, prospettiva salita
15. `PLAYER_UPHILL_STRAIGHT_3.png` - Frame 3: Fase di volo, prospettiva salita
16. `PLAYER_UPHILL_STRAIGHT_4.png` - Frame 4: Estensione posteriore, prospettiva salita

#### Svolta a Sinistra in Salita
17. `PLAYER_UPHILL_LEFT_1.png` - Frame 1: Zampe raccolte, sinistra + salita
18. `PLAYER_UPHILL_LEFT_2.png` - Frame 2: Estensione anteriore, sinistra + salita
19. `PLAYER_UPHILL_LEFT_3.png` - Frame 3: Fase di volo, sinistra + salita
20. `PLAYER_UPHILL_LEFT_4.png` - Frame 4: Estensione posteriore, sinistra + salita

#### Svolta a Destra in Salita
21. `PLAYER_UPHILL_RIGHT_1.png` - Frame 1: Zampe raccolte, destra + salita
22. `PLAYER_UPHILL_RIGHT_2.png` - Frame 2: Estensione anteriore, destra + salita
23. `PLAYER_UPHILL_RIGHT_3.png` - Frame 3: Fase di volo, destra + salita
24. `PLAYER_UPHILL_RIGHT_4.png` - Frame 4: Estensione posteriore, destra + salita

---

## 📐 Specifiche Tecniche

### Dimensioni Sprite
- **Larghezza consigliata**: 400-700px
- **Altezza consigliata**: 600-1200px
- **Aspect ratio**: ~1.5-2.0 (altezza/larghezza)
- Il gioco scalerà automaticamente mantenendo le proporzioni

### Formato
- **Tipo file**: PNG
- **Trasparenza**: Sì (sfondo trasparente)
- **Colore**: RGB o RGBA

### Posizionamento nella Cartella
Tutti gli sprite devono essere salvati in:
```
images/horses/
```

---

## 🎨 Linee Guida Artistiche

### Ciclo di Galoppo (4 Frame)

**Frame 1 - Raccolta**
```
  /|     |\
 / |     | \
/  |_____|  \
  ||  |  ||    <- Zampe anteriori e posteriori sotto il corpo
  ||  |  ||
```

**Frame 2 - Estensione Anteriore**
```
      /|\
     / | \___
    /  |     \
   |   |_____|  <- Zampe anteriori estese, posteriori raccolte
  ||        ||
  ||        ||
```

**Frame 3 - Fase di Volo**
```
     ___/|\___
    /    |    \
   /     |_____\
  |           |  <- Tutte le zampe sollevate/estese
   \         /
    \\_____//
```

**Frame 4 - Estensione Posteriore**
```
  /|\
 / | \
/  |  \___
   |_____|    <- Zampe posteriori estese, anteriori raccolte
 ||        ||
 ||        ||
```

---

## 🔄 Come Funziona l'Animazione

1. **Velocità di animazione**: Proporzionale alla velocità del cavallo
   - Cavallo fermo/lento: ~10 FPS
   - Cavallo al galoppo pieno: ~30 FPS

2. **Loop continuo**: 1 → 2 → 3 → 4 → 1 → 2 → 3 → 4 ...

3. **Selezione automatica**: Il gioco sceglie automaticamente:
   - La direzione (straight/left/right) in base allo sterzo
   - Il terreno (piano/salita) in base al percorso
   - Il frame (1-4) in base al tempo e alla velocità

---

## ⚙️ Sistema Fallback

Il codice include un sistema di fallback intelligente:

1. **Se manca un frame specifico** (es. `PLAYER_STRAIGHT_3.png`):
   → Usa il frame 1 (`PLAYER_STRAIGHT_1.png`)

2. **Se manca un'intera direzione**:
   → Usa gli sprite originali delle auto come placeholder

Questo significa che puoi iniziare con meno sprite e aggiungerli gradualmente!

---

## 🚀 Ordine Consigliato di Creazione

### Fase 1: MINIMO FUNZIONALE (6 sprite)
Crea solo i frame 1 per tutte le direzioni:
- `PLAYER_STRAIGHT_1.png`
- `PLAYER_LEFT_1.png`
- `PLAYER_RIGHT_1.png`
- `PLAYER_UPHILL_STRAIGHT_1.png`
- `PLAYER_UPHILL_LEFT_1.png`
- `PLAYER_UPHILL_RIGHT_1.png`

### Fase 2: ANIMAZIONE BASE (12 sprite)
Aggiungi i 4 frame per il piano:
- Tutti i `PLAYER_STRAIGHT_[1-4].png`
- Tutti i `PLAYER_LEFT_[1-4].png`
- Tutti i `PLAYER_RIGHT_[1-4].png`

### Fase 3: COMPLETO (24 sprite)
Completa con le versioni uphill:
- Tutti i `PLAYER_UPHILL_*_[1-4].png`

---

## 🛠️ Strumenti Consigliati

### Per Creare Sprite
- **Aseprite** - Ideale per pixel art e animazioni
- **Photoshop/GIMP** - Per grafica ad alta risoluzione
- **Blender** - Se vuoi renderizzare da modelli 3D

### Per Organizzare
- **TexturePacker** - Per creare sprite sheets (opzionale)
- **Bulk Rename Utility** - Per rinominare file in batch

---

## 📞 Riferimento Rapido

**Percorso sprite**:
```
images/horses/PLAYER_[UPHILL_]DIRECTION_FRAME.png
```

**Dimensioni totali**:
- 24 sprite × ~500KB/sprite = ~12MB totali

**Tempo stimato creazione**:
- Fase 1: 2-3 ore
- Fase 2: 4-6 ore
- Fase 3: 6-8 ore
- **Totale**: 12-17 ore (dipende dall'esperienza artistica)

---

## ✅ Checklist

- [ ] Frame 1 di tutte le direzioni (6 sprite) - PRIORITÀ ALTA
- [ ] Frame 2-4 per STRAIGHT (3 sprite)
- [ ] Frame 2-4 per LEFT (3 sprite)
- [ ] Frame 2-4 per RIGHT (3 sprite)
- [ ] Frame 1-4 per UPHILL_STRAIGHT (4 sprite)
- [ ] Frame 2-4 per UPHILL_LEFT (3 sprite)
- [ ] Frame 2-4 per UPHILL_RIGHT (3 sprite)

**TOTALE**: 24 sprite

---

## 💡 Suggerimenti Finali

1. **Inizia semplice**: Crea prima i frame 1, testa il gioco, poi aggiungi gli altri
2. **Usa riferimenti**: Cerca video di cavalli al galoppo per capire il movimento
3. **Mantieni coerenza**: Usa lo stesso stile artistico per tutti gli sprite
4. **Testa frequentemente**: Carica gli sprite nel gioco per vedere come appaiono in movimento

Buona creazione! 🎨🏇
