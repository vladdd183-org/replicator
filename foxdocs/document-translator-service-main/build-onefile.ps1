# ===================================================================
# Build ONE-FILE version of DocumentTranslator
# Creates single EXE file (larger, slower first start)
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

Write-Info "=== Building ONE-FILE version ==="
Write-Info "Build started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

Write-Warning "========================================="
Write-Warning "ONE-FILE MODE:"
Write-Warning "- Single EXE file (~2-3 GB)"
Write-Warning "- Slower first startup (extraction to temp)"
Write-Warning "- Easier distribution (one file)"
Write-Warning "========================================="
Write-Info ""
Start-Sleep -Seconds 2

# Check if venv exists
if (-Not (Test-Path $VENV_DIR)) {
    Write-Error-Custom "Virtual environment not found!"
    Write-Info "Please run build-windows.ps1 first to create venv"
    exit 1
}

# Check if spec template exists
if (-Not (Test-Path "DocumentTranslator.onefile.spec.template")) {
    Write-Error-Custom "ONE-FILE spec template not found!"
    exit 1
}

# Copy onefile spec template
Write-Info "Using ONE-FILE spec template..."
Copy-Item "DocumentTranslator.onefile.spec.template" "$APP_NAME.spec" -Force
Write-Success "ONE-FILE spec file created"

# Check for custom hooks
if (Test-Path "hook-multipart.py") {
    Write-Info "Custom multipart hook found"
}
if (Test-Path "pyi_rth_logfire.py") {
    Write-Info "Runtime hook for logfire found"
}
if (Test-Path "pyi_rth_paddlex.py") {
    Write-Info "Runtime hook for paddlex found"
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

# Build ONE-FILE EXE
Write-Info "=== Building ONE-FILE EXE ==="
Write-Warning "This may take 15-40 minutes..."
Write-Warning "Final EXE will be 2-3 GB in size"

try {
    & $PYINSTALLER `
        --clean `
        --noconfirm `
        "$APP_NAME.spec"
    
    Write-Success "Build completed successfully!"
} catch {
    Write-Error-Custom "Build error: $_"
    exit 1
}

# Check result
$exePath = ".\dist\$APP_NAME.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Success "ONE-FILE EXE created: $exePath"
    Write-Info "Size: $([math]::Round($exeSize, 2)) MB"
    
    Write-Success "========================================="
    Write-Success "   ONE-FILE BUILD COMPLETED!"
    Write-Success "========================================="
    Write-Info "EXE located at: .\dist\$APP_NAME.exe"
    Write-Info ""
    Write-Info "To run:"
    Write-Info "  cd .\dist\"
    Write-Info "  set APP_ENV=production"
    Write-Info "  .\$APP_NAME.exe"
    Write-Info ""
    Write-Warning "First startup will be slower (extraction to temp)"
    Write-Warning "Subsequent runs will be faster"
    
} else {
    Write-Error-Custom "EXE file not found!"
    exit 1
}

Write-Info "Finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

