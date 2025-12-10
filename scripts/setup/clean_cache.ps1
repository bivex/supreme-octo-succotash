# Clean Python cache files and directories
# This script recursively removes all __pycache__ directories and .pyc files

Write-Host "Cleaning Python cache files..." -ForegroundColor Green

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Change to project root directory
Set-Location $projectRoot

# Remove all __pycache__ directories recursively
Get-ChildItem -Path . -Directory -Name "__pycache__" -Recurse | ForEach-Object {
    $fullPath = Join-Path $projectRoot $_
    if (Test-Path $fullPath) {
        Remove-Item $fullPath -Recurse -Force
        Write-Host "Removed: $fullPath" -ForegroundColor Yellow
    }
}

# Remove all .pyc files recursively
Get-ChildItem -Path . -File -Name "*.pyc" -Recurse | ForEach-Object {
    $fullPath = Join-Path $projectRoot $_
    if (Test-Path $fullPath) {
        Remove-Item $fullPath -Force
        Write-Host "Removed: $fullPath" -ForegroundColor Yellow
    }
}

# Remove all .pyo files recursively
Get-ChildItem -Path . -File -Name "*.pyo" -Recurse | ForEach-Object {
    $fullPath = Join-Path $projectRoot $_
    if (Test-Path $fullPath) {
        Remove-Item $fullPath -Force
        Write-Host "Removed: $fullPath" -ForegroundColor Yellow
    }
}

# Remove all .pyd files recursively (compiled extensions)
Get-ChildItem -Path . -File -Name "*.pyd" -Recurse | ForEach-Object {
    $fullPath = Join-Path $projectRoot $_
    if (Test-Path $fullPath) {
        Remove-Item $fullPath -Force
        Write-Host "Removed: $fullPath" -ForegroundColor Yellow
    }
}

Write-Host "Cache cleanup completed!" -ForegroundColor Green
