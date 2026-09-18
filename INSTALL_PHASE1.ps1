$ErrorActionPreference = "Stop"

$Repo = (Get-Location).Path
$Zip = Join-Path $Repo "phoenix_core_v2_phase1_build.zip"
$Temp = Join-Path $Repo ".phase1_build_extract"

if (-not (Test-Path $Zip)) {
    throw "Place phoenix_core_v2_phase1_build.zip in the Phoenix Core V2 repository root first."
}

if (Test-Path $Temp) { Remove-Item $Temp -Recurse -Force }
Expand-Archive -Path $Zip -DestinationPath $Temp -Force

Get-ChildItem $Temp -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($Temp.Length).TrimStart('\')
    $destination = Join-Path $Repo $relative
    $parent = Split-Path $destination -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force $parent | Out-Null }
    Copy-Item $_.FullName $destination -Force
}

Remove-Item $Temp -Recurse -Force
Remove-Item $Zip -Force

Write-Host ""
Write-Host "Phoenix Core V2 Phase 1 foundation installed."
Write-Host "Next: run .\.venv\Scripts\python.exe -m pytest -q"
