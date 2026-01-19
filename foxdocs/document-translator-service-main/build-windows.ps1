# ===================================================================
# PowerShell Build Script for Document Translator Service (EXE)
# For Windows 10/11 + Python 3.11
# CPU-ONLY VERSION (No GPU/CUDA dependencies)
# ===================================================================

# Параметры
param(
    [switch]$DepsOnly  # Только установка зависимостей, без сборки
)

# Stop on errors
$ErrorActionPreference = "Stop"

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$OutputEncoding = [System.Text.Encoding]::UTF8

# Color output functions
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Error-Custom { Write-Host "[ERROR] $args" -ForegroundColor Red }

# ===================================================================
# CONFIGURATION
# ===================================================================
$PYTHON_VERSION = "3.11"
$VENV_DIR = "venv"
$BUILD_DIR = "build"
$DIST_DIR = "dist"
$CACHE_DIR = ".cache"
$APP_NAME = "DocumentTranslator"

Write-Info "=== Document Translator Service - Windows Build Script ==="
Write-Info "Build started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# ===================================================================
# IMPORTANT: Visual C++ Redistributable Check
# ===================================================================
Write-Warning "========================================="
Write-Warning "IMPORTANT: Visual C++ Redistributable Required!"
Write-Warning "If not installed, download from:"
Write-Warning "https://aka.ms/vs/17/release/vc_redist.x64.exe"
Write-Warning "The EXE will not work without it!"
Write-Warning "========================================="
Write-Info ""
Start-Sleep -Seconds 3

# ===================================================================
# STEP 1: Check Python
# ===================================================================
Write-Info "Checking Python $PYTHON_VERSION..."

try {
    $pythonVersion = & python --version 2>&1
    if ($pythonVersion -match "Python 3\.11") {
        Write-Success "Found: $pythonVersion"
    } else {
        Write-Error-Custom "Python 3.11 required, found: $pythonVersion"
        exit 1
    }
} catch {
    Write-Error-Custom "Python not found! Install Python 3.11 from python.org"
    exit 1
}

# ===================================================================
# STEP 2: Create virtual environment
# ===================================================================
Write-Info "Creating virtual environment..."

if (Test-Path $VENV_DIR) {
    Write-Warning "Virtual environment exists. Removing old one..."
    Remove-Item -Recurse -Force $VENV_DIR
}

python -m venv $VENV_DIR
Write-Success "Virtual environment created"

# Activate virtual environment
$VENV_PYTHON = ".\$VENV_DIR\Scripts\python.exe"
$VENV_PIP = ".\$VENV_DIR\Scripts\pip.exe"

# ===================================================================
# STEP 3: Upgrade pip
# ===================================================================
Write-Info "Upgrading pip, setuptools, wheel..."
& $VENV_PIP install --upgrade pip setuptools wheel
Write-Success "pip upgraded"

# ===================================================================
# STEP 4: Install dependencies (following Dockerfile order)
# ===================================================================

# Set environment variables for CPU-ONLY
$env:CUDA_VISIBLE_DEVICES = ""
$env:USE_CUDA = "0"
$env:USE_GPU = "0"
$env:PIP_NO_CACHE_DIR = "1"

Write-Info "=== Installing dependencies ==="

# Create constraints file programmatically (avoid encoding issues)
Write-Info "Creating constraints file to block GPU dependencies..."
$constraintsContent = @"
# PIP CONSTRAINTS - CPU-ONLY
nvidia-cublas-cu12==99.99.99+invalid
nvidia-cublas-cu11==99.99.99+invalid
nvidia-cuda-cupti-cu12==99.99.99+invalid
nvidia-cuda-cupti-cu11==99.99.99+invalid
nvidia-cuda-nvrtc-cu12==99.99.99+invalid
nvidia-cuda-nvrtc-cu11==99.99.99+invalid
nvidia-cuda-runtime-cu12==99.99.99+invalid
nvidia-cuda-runtime-cu11==99.99.99+invalid
nvidia-cudnn-cu12==99.99.99+invalid
nvidia-cudnn-cu11==99.99.99+invalid
nvidia-cufft-cu12==99.99.99+invalid
nvidia-cufft-cu11==99.99.99+invalid
nvidia-curand-cu12==99.99.99+invalid
nvidia-curand-cu11==99.99.99+invalid
nvidia-cusolver-cu12==99.99.99+invalid
nvidia-cusolver-cu11==99.99.99+invalid
nvidia-cusparse-cu12==99.99.99+invalid
nvidia-cusparse-cu11==99.99.99+invalid
nvidia-nccl-cu12==99.99.99+invalid
nvidia-nccl-cu11==99.99.99+invalid
nvidia-nvtx-cu12==99.99.99+invalid
nvidia-nvtx-cu11==99.99.99+invalid
nvidia-nvjitlink-cu12==99.99.99+invalid
nvidia-nvjitlink-cu11==99.99.99+invalid
opencv-python==99.99.99+invalid
opencv-contrib-python==99.99.99+invalid
tensorflow-gpu==99.99.99+invalid
"@

# Save with ASCII encoding (compatible with cp1252)
$constraintsContent | Out-File -FilePath "constraints-temp.txt" -Encoding ASCII -Force
$CONSTRAINTS_FILE = "constraints-temp.txt"
Write-Success "Constraints file created: $CONSTRAINTS_FILE"

# STEP 4.1: Base dependencies for building
Write-Info "Installing base dependencies..."
& $VENV_PIP install --no-cache-dir -c $CONSTRAINTS_FILE `
    "numpy>=1.24.0,<2.0.0" `
    "setuptools<60" `
    "pyyaml==6.0.2" `
    "Cython"
Write-Success "Base dependencies installed"

# STEP 4.2: OpenCV CPU-only versions
Write-Info "Installing OpenCV (CPU-only)..."
& $VENV_PIP install --no-cache-dir -c $CONSTRAINTS_FILE `
    "pillow==11.*" `
    "opencv-python-headless==4.10.*" `
    "opencv-contrib-python-headless==4.10.*"
Write-Success "OpenCV installed"

# STEP 4.3: Web framework
Write-Info "Installing web framework..."
& $VENV_PIP install --no-cache-dir -c $CONSTRAINTS_FILE `
    "litestar==2.17.0" `
    "pydantic==2.9.*" `
    "pydantic-settings==2.*" `
    "dishka==1.4.*" `
    "logfire==2.7.*" `
    "uvicorn[standard]==0.32.*" `
    "multipart"
Write-Success "Web framework installed"

# STEP 4.4: PaddlePaddle CPU-only
Write-Info "Installing PaddlePaddle (CPU-only)..."
& $VENV_PIP install --no-cache-dir -c $CONSTRAINTS_FILE `
    "paddlepaddle==3.2.0" `
    --index-url https://www.paddlepaddle.org.cn/packages/stable/cpu/
Write-Success "PaddlePaddle installed"

# STEP 4.5: scikit-image
Write-Info "Installing scikit-image..."
& $VENV_PIP install --no-cache-dir -c $CONSTRAINTS_FILE `
    "scikit-image>=0.19.0"
Write-Success "scikit-image installed"

# STEP 4.6: Common dependencies
Write-Info "Installing common dependencies..."
& $VENV_PIP install --no-cache-dir -c $CONSTRAINTS_FILE `
    "typing-extensions>=4.0.0" `
    "packaging>=20.0" `
    "requests>=2.25.0" `
    "filelock>=3.0.0" `
    "cryptography>=41.0.0" `
    "py-machineid>=0.6.0" `
    "huggingface-hub" `
    "pandas" `
    "prettytable" `
    "colorlog" `
    "chardet" `
    "aistudio-sdk" `
    "modelscope" `
    "py-cpuinfo" `
    "ruamel.yaml" `
    "ujson" `
    "protobuf" `
    "networkx" `
    "opt-einsum" `
    "pyclipper>=1.3.0"
Write-Success "Common dependencies installed"

# STEP 4.7: PaddleX and PaddleOCR
Write-Info "Installing PaddleX..."
# Install without constraints for paddlex (needs prebuilt wheels)
& $VENV_PIP install --no-cache-dir "paddlex[ocr-core]==3.2.1"
Write-Success "PaddleX installed"

Write-Info "Installing PaddleOCR..."
& $VENV_PIP install --no-cache-dir --no-deps "paddleocr==3.2.0"
Write-Success "PaddleOCR installed"

# STEP 4.8: PDF libraries
Write-Info "Installing PDF libraries (PyMuPDF, pypdfium2)..."
& $VENV_PIP install --no-cache-dir -c $CONSTRAINTS_FILE `
    "pymupdf>=1.23.0" `
    "pypdfium2>=4.0.0"
Write-Success "PDF libraries installed"

# STEP 4.9: PyTorch CPU-only
Write-Info "Installing PyTorch (CPU-only)..."
& $VENV_PIP install --no-cache-dir `
    "torch==2.5.0+cpu" `
    --index-url https://download.pytorch.org/whl/cpu
Write-Success "PyTorch installed"

# STEP 4.10: Stanza and dependencies
Write-Info "Installing stanza dependencies..."
& $VENV_PIP install --no-cache-dir -c $CONSTRAINTS_FILE `
    "tqdm>=1.56.0"
& $VENV_PIP install --no-cache-dir --no-deps "stanza==1.1.1"
Write-Success "Stanza installed"

# STEP 4.11: argostranslate and dependencies
Write-Info "Installing argostranslate..."
& $VENV_PIP install --no-cache-dir -c $CONSTRAINTS_FILE `
    "ctranslate2>=3.16.0" `
    "sentencepiece==0.2.0" `
    "sacremoses==0.0.53"
& $VENV_PIP install --no-cache-dir --no-deps -c $CONSTRAINTS_FILE `
    "argostranslate==1.9.*"
Write-Success "argostranslate installed"

# STEP 4.12: Upgrade setuptools and additional dependencies
Write-Info "Installing final dependencies..."
& $VENV_PIP install --no-cache-dir -c $CONSTRAINTS_FILE `
    "setuptools>=65.0" `
    "more-itertools"
Write-Success "All dependencies installed"

# ===================================================================
# STEP 5: Install PyInstaller
# ===================================================================
Write-Info "Installing PyInstaller..."
& $VENV_PIP install --no-cache-dir "pyinstaller>=6.0.0"
Write-Success "PyInstaller installed"

# ===================================================================
# STEP 6: Check for NVIDIA packages
# ===================================================================
Write-Info "Checking for NVIDIA packages..."
$nvidiaPackages = & $VENV_PIP list | Select-String -Pattern "nvidia" -CaseSensitive:$false
if ($nvidiaPackages) {
    Write-Error-Custom "Found NVIDIA packages: $nvidiaPackages"
    exit 1
} else {
    Write-Success "No NVIDIA packages - CPU-only build confirmed"
}

# ===================================================================
# Если нужны только зависимости - выходим
# ===================================================================
if ($DepsOnly) {
    Write-Success "========================================="
    Write-Success "   DEPENDENCIES INSTALLED!"
    Write-Success "========================================="
    Write-Info "Virtual environment ready at: .\$VENV_DIR"
    Write-Info "PyInstaller installed and ready"
    Write-Info "Finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Info ""
    Write-Info "To build EXE now, run:"
    Write-Info "  .\build-onefile.ps1    (for single EXE file)"
    Write-Info "Or re-run without -DepsOnly for ONEDIR build"
    exit 0
}

# ===================================================================
# STEP 7: Preload models (optional - may fail if VC++ not installed)
# ===================================================================
if (Test-Path "scripts\prewarm_models.py") {
    Write-Info "Preloading models (OPTIONAL - failures are OK)..."
    Write-Warning "If this fails due to DLL errors, install VC++ Redistributable"
    Write-Warning "Models will download at first run instead"
    
    # Create cache directories
    New-Item -ItemType Directory -Force -Path "$CACHE_DIR" | Out-Null
    New-Item -ItemType Directory -Force -Path ".argos" | Out-Null
    New-Item -ItemType Directory -Force -Path ".paddlex" | Out-Null
    New-Item -ItemType Directory -Force -Path ".stanza" | Out-Null
    
    # Set environment variables
    $env:XDG_CACHE_HOME = "$PWD\$CACHE_DIR"
    $env:ARGOS_DATA_DIR = "$PWD\.argos"
    $env:STANZA_RESOURCES_DIR = "$PWD\.stanza"
    $env:PYTHONWARNINGS = "ignore::FutureWarning"
    
    try {
        $result = & $VENV_PYTHON "scripts\prewarm_models.py" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Models preloaded successfully"
        } else {
            Write-Warning "Model preload had errors (this is OK)"
            Write-Warning "Models will download when EXE first runs"
        }
    } catch {
        Write-Warning "Failed to preload models (this is OK)"
        Write-Warning "Models will download when EXE first runs"
    }
} else {
    Write-Warning "Script prewarm_models.py not found, skipping preload"
}

# ===================================================================
# STEP 8: Copy spec file for PyInstaller
# ===================================================================
Write-Info "Preparing spec file..."

if (-Not (Test-Path "DocumentTranslator.spec.template")) {
    Write-Error-Custom "File DocumentTranslator.spec.template not found!"
    Write-Info "Make sure the file is in the same directory as the script"
    exit 1
}

# Copy template as working spec file
Copy-Item "DocumentTranslator.spec.template" "$APP_NAME.spec" -Force
Write-Success "Spec file created: $APP_NAME.spec"

# ===================================================================
# STEP 9: Build EXE with PyInstaller
# ===================================================================
Write-Info "=== Starting EXE build ==="
Write-Warning "This may take 10-30 minutes..."

$PYINSTALLER = ".\$VENV_DIR\Scripts\pyinstaller.exe"

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

# ===================================================================
# STEP 10: Check result
# ===================================================================
$exePath = ".\$DIST_DIR\$APP_NAME\$APP_NAME.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Success "EXE file created: $exePath"
    Write-Info "Size: $([math]::Round($exeSize, 2)) MB"
    
    # Check total distribution size
    $distSize = (Get-ChildItem -Path ".\$DIST_DIR\$APP_NAME" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Info "Total distribution size: $([math]::Round($distSize, 2)) MB"
    
    Write-Success "=== Build completed successfully! ==="
    Write-Info "Distribution located at: .\$DIST_DIR\$APP_NAME\"
    Write-Info ""
    Write-Info "To run:"
    Write-Info "  cd .\$DIST_DIR\$APP_NAME\"
    Write-Info "  .\$APP_NAME.exe"
    
} else {
    Write-Error-Custom "EXE file not found!"
    exit 1
}

# ===================================================================
# STEP 11: Create README for distribution
# ===================================================================
$readmeContent = @"
# Document Translator Service - Windows Edition

## IMPORTANT: Prerequisites
**Visual C++ Redistributable 2015-2022 REQUIRED**
If the application fails to start with DLL errors, install:
https://aka.ms/vs/17/release/vc_redist.x64.exe

## System Requirements
- Windows 10/11 (64-bit)
- Visual C++ Redistributable 2015-2022 (link above)
- Minimum 4 GB RAM (8 GB recommended)
- ~2 GB free disk space

## Running
1. Install Visual C++ Redistributable (if not already installed)
2. Open command prompt or PowerShell in this directory
3. Run: $APP_NAME.exe
4. Server will start at http://localhost:8000

## Configuration
Environment variables can be set before running:
- PORT - server port (default 8000)
- HOST - server host (default 0.0.0.0)

## First Run
Additional models may download on first run.
This is normal and will take a few minutes.
Subsequent runs will be faster.

## Troubleshooting
If you get DLL errors:
1. Install VC++ Redistributable from link above
2. Restart the application

## Support
Build: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
CPU-only version (no GPU acceleration)
"@

$readmeContent | Out-File -Encoding UTF8 ".\$DIST_DIR\$APP_NAME\README.txt"
Write-Success "README created"

# Copy VC++ installation instructions
if (Test-Path "INSTALL-VCREDIST.txt") {
    Copy-Item "INSTALL-VCREDIST.txt" ".\$DIST_DIR\$APP_NAME\" -Force
    Write-Success "VC++ installation instructions copied"
}

# Copy run scripts
if (Test-Path "RUN-EXE.bat") {
    Copy-Item "RUN-EXE.bat" ".\$DIST_DIR\$APP_NAME\" -Force
    Write-Success "Run script (BAT) copied"
}
if (Test-Path "RUN-EXE.ps1") {
    Copy-Item "RUN-EXE.ps1" ".\$DIST_DIR\$APP_NAME\" -Force
    Write-Success "Run script (PS1) copied"
}

# Cleanup temporary files
Write-Info "Cleaning up temporary files..."
if (Test-Path $CONSTRAINTS_FILE) {
    Remove-Item $CONSTRAINTS_FILE -Force
    Write-Success "Temporary constraints file removed"
}

Write-Success "========================================="
Write-Success "   BUILD COMPLETED SUCCESSFULLY!"
Write-Success "========================================="
Write-Info "Finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
