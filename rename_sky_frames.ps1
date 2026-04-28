$dir = 'C:\Users\domde\Documents\CAVALLIMONGOLI_THEGAME\ASSETS_PER_GRAFICO\07_LIVELLI\01-bulloncino\background\layer_cielo'
$files = Get-ChildItem -Path $dir -Filter '*.jpg' | Sort-Object Name
Write-Host ('Trovati ' + $files.Count + ' file .jpg')
Get-ChildItem -Path $dir -Filter 'sky_*.png' | Remove-Item -Force
if (Test-Path "$dir\sky.png") { Remove-Item "$dir\sky.png" -Force }
$n = 1
foreach ($f in $files) {
    Rename-Item -Path $f.FullName -NewName "sky_$n.png" -Force
    $n++
}
Write-Host ('Rinominati ' + ($n - 1) + ' file: sky_1.png ... sky_' + ($n - 1) + '.png')
Copy-Item "$dir\sky_1.png" "$dir\sky.png" -Force
Write-Host 'sky_1.png copiato come sky.png (fallback statico)'
Write-Host 'RINOMINA COMPLETATA'
