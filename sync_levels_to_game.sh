#!/usr/bin/env bash
# sync_levels_to_game.sh
# Equivalente Mac/Linux di sync_levels_to_game.ps1.
# Copia gli asset da ASSETS_PER_GRAFICO/07_LIVELLI/{lvl}/elementi_pista/{vegetazione,ostacoli,billboard_cartelloni}/*.png
# verso images/levels/{game_lvl}/*.PNG rinominando in MAIUSCOLO come si aspetta il gioco.
# Copia anche i background (sky/hills/trees) e i frame animati sky_N.png.
#
# Uso: bash sync_levels_to_game.sh
#      (oppure ./sync_levels_to_game.sh dopo chmod +x)

set -e
cd "$(dirname "$0")"

ASSETS="ASSETS_PER_GRAFICO/07_LIVELLI"
GAME="images/levels"

if [ ! -d "$ASSETS" ]; then
  echo "ERRORE: cartella '$ASSETS' non trovata. Lancia lo script dalla root del progetto."
  exit 1
fi

# Mappa cartella-grafico → cartella-gioco (array paralleli per compat bash 3.2 macOS)
SRC_LEVELS=(01-bulloncino 02-hanno-fallito 03-odore-del-buongiorno 04-cantiere 05-segreto-del-rap 06-come-tu-dici 07-diggiei)
DST_LEVELS=(1-bulloncino  2-hanno-fallito  3-odore-del-buongiorno  4-cantiere  5-segreto-del-rap  6-come-tu-dici  7-diggiei)

# Lista sprite da rinominare (lowercase → MAIUSCOLO)
SPRITES=(
  billboard01 billboard02 billboard03 billboard04 billboard05
  billboard06 billboard07 billboard08 billboard09
  tree1 tree2 dead_tree1 dead_tree2 palm_tree
  bush1 bush2 cactus stump
  boulder1 boulder2 boulder3 column
  semi truck car01 car02 car03 car04
)

# Cartella "comune" da cui prendere veicoli (e altri default) se NON ci sono per-livello.
# Permette di avere un set unico di TIR/macchine senza doverli copiare 7 volte a mano.
COMMON="ASSETS_PER_GRAFICO/04_ELEMENTI_PISTA"

TOTAL_COPIED=0

for i in "${!SRC_LEVELS[@]}"; do
  src_lvl="${SRC_LEVELS[$i]}"
  dst_lvl="${DST_LEVELS[$i]}"
  src="$ASSETS/$src_lvl"
  dst="$GAME/$dst_lvl"

  mkdir -p "$dst"
  copied=0

  # Sprite scenario + veicoli
  # Ordine di ricerca: per-livello (07_LIVELLI/<lvl>/) → comune (04_ELEMENTI_PISTA/)
  # Così SE manca la versione custom per il livello, prende il default condiviso.
  for s in "${SPRITES[@]}"; do
    upper=$(echo "$s" | tr '[:lower:]' '[:upper:]')
    target="$dst/${upper}.png"
    found=""
    for sub in billboard_cartelloni vegetazione ostacoli veicoli; do
      per_level="$src/elementi_pista/$sub/${s}.png"
      common="$COMMON/$sub/${s}.png"
      if [ -f "$per_level" ]; then
        cp -f "$per_level" "$target"
        copied=$((copied+1))
        found="per-level/$sub"
        break
      elif [ -f "$common" ]; then
        cp -f "$common" "$target"
        copied=$((copied+1))
        found="common/$sub"
        break
      fi
    done
    # se non trovato → si lascia stare (il gioco userà l'atlas come fallback)
  done

  # Background statici
  [ -f "$src/background/layer_cielo/sky.png" ]   && cp -f "$src/background/layer_cielo/sky.png"   "$dst/sky.png"   && copied=$((copied+1))
  [ -f "$src/background/layer_colline/hills.png" ] && cp -f "$src/background/layer_colline/hills.png" "$dst/hills.png" && copied=$((copied+1))
  [ -f "$src/background/layer_alberi/trees.png" ]  && cp -f "$src/background/layer_alberi/trees.png"  "$dst/trees.png" && copied=$((copied+1))

  # Frame animati cielo (sky_1.png, sky_2.png, ... finché esistono)
  frame=1
  frames_copied=0
  while [ -f "$src/background/layer_cielo/sky_${frame}.png" ]; do
    cp -f "$src/background/layer_cielo/sky_${frame}.png" "$dst/sky_${frame}.png"
    frames_copied=$((frames_copied+1))
    frame=$((frame+1))
  done
  copied=$((copied+frames_copied))

  if [ "$frames_copied" -gt 0 ]; then
    echo "[$dst_lvl] $copied file (di cui $frames_copied frame cielo animato)"
  else
    echo "[$dst_lvl] $copied file"
  fi
  TOTAL_COPIED=$((TOTAL_COPIED+copied))
done

echo ""
echo "=== SYNC COMPLETATO: $TOTAL_COPIED file copiati ==="
echo "Ricarica il browser con ⌘⇧R per vedere gli asset aggiornati."
