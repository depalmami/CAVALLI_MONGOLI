# Alberi realistici (impostori)

Fotografie da 8 lati, fatte in Blender 5.1 dai modelli Poly Haven a piena risoluzione
(milioni di poligoni) e usate nel gioco come sagome che si girano verso la camera.

- `abete_a/b/c.webp` — da **Fir Tree 01** (`fir_tree_01`), https://polyhaven.com/a/fir_tree_01
- `pino_a/b/c.webp` — da **Pine Tree 01** (`pine_tree_01`), https://polyhaven.com/a/pine_tree_01

Autori: Rob Tuytel (fotografia), Rico Cilliers (modellazione). Licenza **CC0** (pubblico dominio):
nessun obbligo di attribuzione, il credito è per cortesia.

Rifarle: `blender -b --python tools/fotografa-alberi.py -- <modello>_1k.gltf <uscita> <prefisso>` (script nel
diario del PIANO-audioreattivo.md, 5 ottobre 2026): 8 vedute ortografiche 384×1024 a 45°, sfondo
trasparente, luce neutra dall'alto; poi conversione in WebP q82.
