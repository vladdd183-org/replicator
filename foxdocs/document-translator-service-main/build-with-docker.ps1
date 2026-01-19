# ============================================
# PowerShell скрипт для сборки Windows EXE через Docker (Native Windows Container)
# Использует: Dockerfile.windows-native
# Требует: Windows Server 2019+ с Docker Desktop в режиме Windows containers
# ============================================

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Green
Write-Host "Building Windows EXE with Docker (Native Windows Container)" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Проверка что Docker работает в режиме Windows containers
$dockerInfo = docker info 2>&1 | Out-String
if ($dockerInfo -notmatch "OSType: windows") {
    Write-Host "ERROR: Docker must be in Windows containers mode!" -ForegroundColor Red
    Write-Host "Switch to Windows containers in Docker Desktop settings." -ForegroundColor Yellow
    exit 1
}

# Генерация версии
$date = Get-Date -Format "yyyy.MM.dd"
$sha = (git rev-parse --short HEAD 2>$null) ?? "unknown"
$version = "v$date-$sha"

Write-Host "Version: $version" -ForegroundColor Yellow
Write-Host ""

# Создание директории для выходных файлов
$outputDir = ".\release-output"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

# Сборка Docker образа
Write-Host "Step 1/3: Building Docker image..." -ForegroundColor Green
docker build `
    --build-arg VERSION=$date `
    --build-arg SHA_SHORT=$sha `
    -f Dockerfile.windows-native `
    -t document-translator-builder:latest `
    .

Write-Host ""
Write-Host "Step 2/3: Running container to extract files..." -ForegroundColor Green

# Запуск контейнера с volume для выгрузки
docker run --rm `
    -v "${PWD}\${outputDir}:C:\output" `
    document-translator-builder:latest

Write-Host ""
Write-Host "Step 3/3: Cleanup..." -ForegroundColor Green

# Опционально: удаляем образ для экономии места
# docker rmi document-translator-builder:latest

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "✅ Build Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Files created in: $outputDir" -ForegroundColor Yellow
Write-Host ""
Get-ChildItem $outputDir
Write-Host ""

