# ===================================================================
# Quick Rebuild Script - Rebuild EXE without reinstalling dependencies
# ===================================================================

$ErrorActionPreference = "Stop"

# Color output functions
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Error-Custom { Write-Host "[ERROR] $args" -ForegroundColor Red }

$APP_NAME = "DocumentTranslator"
$VENV_DIR = "venv"
$PYINSTALLER = ".\$VENV_DIR\Scripts\pyinstaller.exe"

Write-Info "=== Quick EXE Rebuild ==="
Write-Info "Rebuild started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# Check if venv exists
if (-Not (Test-Path $VENV_DIR)) {
    Write-Error-Custom "Virtual environment not found! Run build-windows.ps1 first"
    exit 1
}

# Check if spec file exists
if (-Not (Test-Path "DocumentTranslator.spec.template")) {
    Write-Error-Custom "Spec template not found!"
    exit 1
}

# Copy updated spec template
Write-Info "Updating spec file..."
Copy-Item "DocumentTranslator.spec.template" "$APP_NAME.spec" -Force
Write-Success "Spec file updated"

# Check for custom hooks and runtime hooks
if (Test-Path "hook-multipart.py") {
    Write-Info "Custom multipart hook found"
} else {
    Write-Warning "Custom hook-multipart.py not found, multipart may not work!"
}

if (Test-Path "pyi_rth_logfire.py") {
    Write-Info "Runtime hook for logfire found"
} else {
    Write-Warning "Runtime hook pyi_rth_logfire.py not found, logfire may not work!"
}

# Clean previous build
Write-Info "Cleaning previous build..."
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
}
Write-Success "Cleaned"

# Rebuild EXE
Write-Info "=== Rebuilding EXE ==="
Write-Warning "This may take 10-30 minutes..."

try {
    & $PYINSTALLER `
        --clean `
        --noconfirm `
        "$APP_NAME.spec"
    
    Write-Success "Rebuild completed successfully!"
} catch {
    Write-Error-Custom "Rebuild error: $_"
    exit 1
}

# Check result
$exePath = ".\dist\$APP_NAME\$APP_NAME.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Success "EXE file created: $exePath"
    Write-Info "Size: $([math]::Round($exeSize, 2)) MB"
    
    Write-Success "========================================="
    Write-Success "   REBUILD COMPLETED SUCCESSFULLY!"
    Write-Success "========================================="
    Write-Info "Distribution located at: .\dist\$APP_NAME\"
    Write-Info ""
    Write-Info "To run:"
    Write-Info "  cd .\dist\$APP_NAME\"
    Write-Info "  .\$APP_NAME.exe"
} else {
    Write-Error-Custom "EXE file not found!"
    exit 1
}

Write-Info "Finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

