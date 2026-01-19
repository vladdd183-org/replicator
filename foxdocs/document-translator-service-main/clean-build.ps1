# ===================================================================
# Скрипт очистки временных файлов сборки
# ===================================================================

$ErrorActionPreference = "Stop"

function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Warning { Write-Host "[WARN] $args" -ForegroundColor Yellow }

Write-Info "=== Очистка файлов сборки ==="
Write-Warning "Это удалит: venv, build, __pycache__, *.spec"
Write-Info "Дистрибутив в dist/ будет сохранён"
Write-Info ""

$confirmation = Read-Host "Продолжить? (y/n)"
if ($confirmation -ne 'y') {
    Write-Info "Отменено"
    exit 0
}

# Удаляем директории
$dirsToRemove = @("venv", "build", "__pycache__")
foreach ($dir in $dirsToRemove) {
    if (Test-Path $dir) {
        Write-Info "Удаление $dir..."
        Remove-Item -Recurse -Force $dir
        Write-Success "Удалено: $dir"
    } else {
        Write-Info "Пропущено: $dir (не существует)"
    }
}

# Удаляем spec файлы
Write-Info "Удаление *.spec файлов..."
Get-ChildItem -Filter "*.spec" | Remove-Item -Force
Write-Success "*.spec файлы удалены"

# Удаляем кеши Python
Write-Info "Удаление Python кешей..."
Get-ChildItem -Include "__pycache__" -Recurse -Force | Remove-Item -Recurse -Force
Get-ChildItem -Include "*.pyc" -Recurse -Force | Remove-Item -Force
Write-Success "Python кеши удалены"

Write-Success "=== Очистка завершена ==="
Write-Info "Для полной очистки (включая dist) используйте: clean-build.ps1 -Full"

