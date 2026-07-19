# Downloads the Stockfish engine binary into engine/bin/stockfish.exe.
# The binary is gitignored; run this once per clone (or set CHESSLAB_STOCKFISH_PATH).
param(
    [string]$Tag = "sf_18",
    [string]$Flavor = "x86-64-avx2"  # use x86-64 for CPUs without AVX2
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$binDir = Join-Path $repoRoot "engine\bin"
$target = Join-Path $binDir "stockfish.exe"

if (Test-Path $target) {
    Write-Host "Stockfish already present at $target"
    exit 0
}

$asset = "stockfish-windows-$Flavor.zip"
$url = "https://github.com/official-stockfish/Stockfish/releases/download/$Tag/$asset"
$tmpZip = Join-Path $env:TEMP $asset
$tmpDir = Join-Path $env:TEMP "stockfish-extract"

Write-Host "Downloading $url"
Invoke-WebRequest -Uri $url -OutFile $tmpZip

New-Item -ItemType Directory -Force $binDir | Out-Null
if (Test-Path $tmpDir) { Remove-Item -Recurse -Force $tmpDir }
Expand-Archive -Path $tmpZip -DestinationPath $tmpDir

$exe = Get-ChildItem -Path $tmpDir -Recurse -Filter "stockfish*.exe" | Select-Object -First 1
if ($null -eq $exe) { throw "No stockfish exe found in archive" }
Copy-Item $exe.FullName $target

Remove-Item $tmpZip
Remove-Item -Recurse -Force $tmpDir
Write-Host "Stockfish installed at $target"
& $target "quit" | Select-Object -First 1
