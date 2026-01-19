# ============================================
# Скрипт остановки Document Translator Service (PowerShell)
# ============================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Остановка Document Translator Service" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
try {
    $null = docker version 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Host ""
    Write-Host "[ОШИБКА] Docker не запущен!" -ForegroundColor Red
    Write-Host "Если контейнеры запущены, сначала запустите Docker Desktop."
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверка наличия docker-compose.yml
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "[ОШИБКА] Файл docker-compose.yml не найден!" -ForegroundColor Red
    Write-Host "Убедитесь, что вы находитесь в папке с релизом."
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "Остановка контейнеров..." -ForegroundColor Yellow
docker-compose down

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ОШИБКА] Не удалось остановить контейнеры!" -ForegroundColor Red
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Сервис успешно остановлен!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Проверка, что контейнеры остановлены
$containers = docker ps -a | Select-String "doctrans"
if ($null -ne $containers -and $containers.Count -gt 0) {
    Write-Host "[INFO] Остановленные контейнеры все еще существуют." -ForegroundColor Cyan
    Write-Host "Они будут удалены при следующем запуске start.bat"
} else {
    Write-Host "[OK] Контейнеры полностью удалены." -ForegroundColor Green
}

Write-Host ""
Write-Host "Для запуска снова используйте: start.bat (или start.ps1)"
Write-Host ""

Read-Host "Нажмите Enter для выхода"

