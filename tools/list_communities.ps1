$d = Get-Content 'H:\Yakuwarmi\mapas interactivos\communities_geo.json' -Raw | ConvertFrom-Json
foreach($c in $d){
    Write-Host "$($c.id) | $($c.name) | $($c.ha)"
}
