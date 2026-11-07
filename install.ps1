# Install the collage skill's Python dependencies and verify the package.
# Run once, from inside the installed collage/ folder:
#   powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = if ($env:PYTHON) { $env:PYTHON } else { "python" }
Write-Host "collage: installing Python dependencies with $py ..."
& $py -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host ""
Write-Host "collage: verifying the installed skill ..."
& $py scripts/check_setup.py
exit $LASTEXITCODE
