# sync_levels_to_game.ps1
# Copia gli asset da ASSETS_PER_GRAFICO/07_LIVELLI → javascript-racer/images/levels
# rinominando i file nel formato MAIUSCOLO atteso dal gioco.

$assetBase = 'C:\Users\domde\Documents\CAVALLIMONGOLI_THEGAME\ASSETS_PER_GRAFICO\07_LIVELLI'
$gameBase  = 'C:\Users\domde\Documents\CAVALLIMONGOLI_THEGAME\javascript-racer\images\levels'

# Mappa: nome-file-grafico → NOME-FILE-GIOCO
$spriteMap = @{
    'billboard01.png' = 'BILLBOARD01.png'
    'billboard02.png' = 'BILLBOARD02.png'
    'billboard03.png' = 'BILLBOARD03.png'
    'billboard04.png' = 'BILLBOARD04.png'
    'billboard05.png' = 'BILLBOARD05.png'
    'billboard06.png' = 'BILLBOARD06.png'
    'billboard07.png' = 'BILLBOARD07.png'
    'billboard08.png' = 'BILLBOARD08.png'
    'billboard09.png' = 'BILLBOARD09.png'
    'tree1.png'       = 'TREE1.png'
    'tree2.png'       = 'TREE2.png'
    'dead_tree1.png'  = 'DEAD_TREE1.png'
    'dead_tree2.png'  = 'DEAD_TREE2.png'
    'palm_tree.png'   = 'PALM_TREE.png'
    'bush1.png'       = 'BUSH1.png'
    'bush2.png'       = 'BUSH2.png'
    'cactus.png'      = 'CACTUS.png'
    'stump.png'       = 'STUMP.png'
    'boulder1.png'    = 'BOULDER1.png'
    'boulder2.png'    = 'BOULDER2.png'
    'boulder3.png'    = 'BOULDER3.png'
    'column.png'      = 'COLUMN.png'
}

# Mappa cartelle livello
$levels = @(
    @{ folder = '01-bulloncino';          gameFolder = '1-bulloncino' },
    @{ folder = '02-hanno-fallito';       gameFolder = '2-hanno-fallito' },
    @{ folder = '03-odore-del-buongiorno';gameFolder = '3-odore-del-buongiorno' },
    @{ folder = '04-cantiere';            gameFolder = '4-cantiere' },
    @{ folder = '05-segreto-del-rap';     gameFolder = '5-segreto-del-rap' },
    @{ folder = '06-come-tu-dici';        gameFolder = '6-come-tu-dici' },
    @{ folder = '07-diggiei';             gameFolder = '7-diggiei' }
)

foreach ($lvl in $levels) {
    $src = "$assetBase\$($lvl.folder)"
    $dst = "$gameBase\$($lvl.gameFolder)"

    [System.IO.Directory]::CreateDirectory($dst) | Out-Null

    $copied = 0

    # Sprites (vegetazione + ostacoli + billboard)
    foreach ($entry in $spriteMap.GetEnumerator()) {
        $srcFile = $null

        # Cerca nella cartella elementi_pista (sia vegetazione che ostacoli che billboard)
        $candidates = @(
            "$src\elementi_pista\billboard_cartelloni\$($entry.Key)",
            "$src\elementi_pista\vegetazione\$($entry.Key)",
            "$src\elementi_pista\ostacoli\$($entry.Key)"
        )
        foreach ($c in $candidates) {
            if (Test-Path $c) { $srcFile = $c; break }
        }

        if ($srcFile) {
            Copy-Item $srcFile "$dst\$($entry.Value)" -Force
            $copied++
        }
    }

    # Background: sky.png, hills.png, trees.png
    # Il gioco li carica tramite loadLevelSprites() → levelBackgrounds → applyLevelBackgrounds()
    $skySrc   = "$src\background\layer_cielo\sky.png"
    $hillsSrc = "$src\background\layer_colline\hills.png"
    $treesSrc = "$src\background\layer_alberi\trees.png"
    if (Test-Path $skySrc)   { Copy-Item $skySrc   "$dst\sky.png"   -Force; $copied++ }
    if (Test-Path $hillsSrc) { Copy-Item $hillsSrc "$dst\hills.png" -Force; $copied++ }
    if (Test-Path $treesSrc) { Copy-Item $treesSrc "$dst\trees.png" -Force; $copied++ }

    # Frame animati cielo: sky_1.png, sky_2.png, ... (il gioco li carica tramite skyAnim)
    $frameNum = 1
    while ($true) {
        $frameSrc = "$src\background\layer_cielo\sky_$frameNum.png"
        if (-not (Test-Path $frameSrc)) { break }
        Copy-Item $frameSrc "$dst\sky_$frameNum.png" -Force
        $copied++
        $frameNum++
    }
    if ($frameNum -gt 1) {
        Write-Host "  → $($frameNum - 1) frame animati cielo (sky_1..sky_$($frameNum-1).png)"
    }

    Write-Host "[$($lvl.gameFolder)] → $copied file sincronizzati in $dst"
}

Write-Host ""
Write-Host "=== SYNC COMPLETATO ==="
Write-Host "Il gioco ora usa gli asset aggiornati."
