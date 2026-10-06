# Alberi realistici (impostori)

Fotografie da 8 lati, fatte in Blender 5.1 dai modelli Poly Haven a piena risoluzione
(milioni di poligoni) e usate nel gioco come sagome che si girano verso la camera.

- `abete_a/b/c.webp` — da **Fir Tree 01** (`fir_tree_01`), https://polyhaven.com/a/fir_tree_01
- `pino_a/b/c.webp` — da **Pine Tree 01** (`pine_tree_01`), https://polyhaven.com/a/pine_tree_01
- `larice_*.webp`, `larice_oro_*.webp` — le foto degli abeti ricolorate (`tools/larici-da-abete.py`)
- `latifoglia_a/b/c.webp` — da **Island Tree 01/02/03** (`island_tree_01..03`), https://polyhaven.com/a/island_tree_01
- `cespuglio_a/b/c.webp` — da **Fern 02** (`fern_02`), https://polyhaven.com/a/fern_02
- `prato.webp` — 16 ciuffi da **Grass Medium 01/02**, **Nettle Plant**, **Dandelion 01**, **Celandine 01**
  (`grass_medium_01`, `grass_medium_02`, `nettle_plant`, `dandelion_01`, `celandine_01`) su polyhaven.com
- `nuvole.webp` — nuvole volumetriche generate in Blender/Cycles (`tools/nuvole-blender.py`), nessun modello esterno

Autori (abete e pino): Rob Tuytel (fotografia), Rico Cilliers (modellazione). Licenza **CC0** (pubblico dominio):
nessun obbligo di attribuzione, il credito è per cortesia.

Rifarle: `blender -b --python tools/fotografa-alberi.py -- <modello>_1k.gltf <uscita> <prefisso>` (script nel
diario del PIANO-audioreattivo.md, 5 ottobre 2026): 8 vedute ortografiche 384×1024 a 45°, sfondo
trasparente, luce neutra dall'alto; poi conversione in WebP q82.

Latifoglie, cespugli e prato: `blender -b --python tools/fotografa-piante.py -- impostore|ciuffi ...`
(istruzioni in testa allo script). Le latifoglie sono 8 vedute 512×512, i cespugli 512×256, il prato
una griglia 4×4 di celle 256 viste di fianco. (`grass_bermuda_01` è stato scaricato ma i suoi fili
sono troppo piccoli per contare: non usato.)
