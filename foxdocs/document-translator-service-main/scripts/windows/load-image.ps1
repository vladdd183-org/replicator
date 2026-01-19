# ============================================
# Скрипт загрузки Docker образа (PowerShell)
# Document Translator Service
# ============================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Загрузка Docker образа" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Проверка запуска Docker Desktop
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
    Write-Host "2. Дождитесь сообщения 'Engine started' или зеленого индикатора в трее"
    Write-Host "3. Запустите этот скрипт снова"
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "Docker работает. Продолжаем..." -ForegroundColor Green
Write-Host ""

# Поиск файла образа
Write-Host "Поиск файла образа..." -ForegroundColor Yellow
$imageFiles = Get-ChildItem -Filter "docker-image-*.tar"

if ($imageFiles.Count -eq 0) {
    Write-Host "[ОШИБКА] Файл образа не найден!" -ForegroundColor Red
    Write-Host "Убедитесь, что файл docker-image-*.tar находится в этой папке."
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

$imageFile = $imageFiles[0].Name
Write-Host "Найден образ: $imageFile" -ForegroundColor Green
Write-Host ""

# Проверка размера файла
$fileSize = [math]::Round((Get-Item $imageFile).Length / 1GB, 2)
Write-Host "[ВНИМАНИЕ] Размер образа: $fileSize GB" -ForegroundColor Yellow
Write-Host "Загрузка может занять несколько минут..." -ForegroundColor Yellow
Write-Host ""

# Загрузка образа
Write-Host "Загрузка образа в Docker..." -ForegroundColor Yellow
docker load -i $imageFile

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ОШИБКА] Не удалось загрузить образ!" -ForegroundColor Red
    Write-Host "Проверьте, что файл не поврежден."
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Образ успешно загружен!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Показать загруженные образы
Write-Host "Проверка загруженных образов:" -ForegroundColor Cyan
docker images | Select-String "document-translator"
Write-Host ""

Write-Host "Теперь вы можете:" -ForegroundColor Yellow
Write-Host "1. Запустить сервис: start.bat (или start.ps1)"
Write-Host "2. Запустить License Helper: license-helper-*.exe"
Write-Host ""

Read-Host "Нажмите Enter для выхода"

