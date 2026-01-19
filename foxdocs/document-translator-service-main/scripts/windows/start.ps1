# ============================================
# Скрипт запуска Document Translator Service (PowerShell)
# ============================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Запуск Document Translator Service" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
Write-Host "Проверка Docker..." -ForegroundColor Yellow
try {
    $null = docker version 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Host ""
    Write-Host "[ОШИБКА] Docker не запущен!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Пожалуйста:" -ForegroundColor Yellow
    Write-Host "1. Запустите Docker Desktop"
    Write-Host "2. Дождитесь сообщения 'Engine started'"
    Write-Host "3. Запустите этот скрипт снова"
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "Docker работает. Продолжаем..." -ForegroundColor Green
Write-Host ""

# Проверка наличия docker-compose.yml
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "[ОШИБКА] Файл docker-compose.yml не найден!" -ForegroundColor Red
    Write-Host "Убедитесь, что вы находитесь в папке с релизом."
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверка, загружен ли образ
Write-Host "Проверка наличия образа..." -ForegroundColor Yellow
$images = docker images | Select-String "document-translator-service"
if ($null -eq $images -or $images.Count -eq 0) {
    Write-Host ""
    Write-Host "[ПРЕДУПРЕЖДЕНИЕ] Образ не найден в Docker!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Сначала загрузите образ командой:"
    Write-Host "  load-image.bat (или load-image.ps1)"
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "Образ найден. Запускаем сервис..." -ForegroundColor Green
Write-Host ""

# Остановка предыдущего контейнера (если запущен)
$null = docker-compose down 2>&1

# Запуск сервиса
Write-Host "Запуск контейнеров..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ОШИБКА] Не удалось запустить сервис!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Просмотрите логи командой:"
    Write-Host "  docker-compose logs"
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Сервис успешно запущен!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Ожидание запуска
Write-Host "Ожидание инициализации сервиса..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Проверка статуса
Write-Host ""
Write-Host "Статус контейнеров:" -ForegroundColor Cyan
docker-compose ps
Write-Host ""

# Проверка здоровья
Write-Host "Проверка доступности API..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[OK] API доступен!" -ForegroundColor Green
} catch {
    Write-Host "[ПРЕДУПРЕЖДЕНИЕ] API пока не отвечает. Сервис может еще загружаться..." -ForegroundColor Yellow
    Write-Host "Подождите 30-60 секунд и проверьте вручную:"
    Write-Host "  http://localhost:8000/health"
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Полезные ссылки:" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "API документация: http://localhost:8000/docs"
Write-Host "Проверка здоровья: http://localhost:8000/health"
Write-Host ""
Write-Host "Для просмотра логов: docker-compose logs -f"
Write-Host "Для остановки: stop.bat (или stop.ps1)"
Write-Host ""

Read-Host "Нажмите Enter для выхода"

