@echo off
REM ============================================
REM Скрипт запуска Document Translator Service
REM ============================================

echo.
echo ============================================
echo   Запуск Document Translator Service
echo ============================================
echo.

REM Проверка Docker
echo Проверка Docker...
docker version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Docker не запущен!
    echo.
    echo Пожалуйста:
    echo 1. Запустите Docker Desktop
    echo 2. Дождитесь сообщения "Engine started"
    echo 3. Запустите этот скрипт снова
    echo.
    pause
    exit /b 1
)

echo Docker работает. Продолжаем...
echo.

REM Проверка наличия docker-compose.yml
if not exist "docker-compose.yml" (
    echo [ОШИБКА] Файл docker-compose.yml не найден!
    echo Убедитесь, что вы находитесь в папке с релизом.
    echo.
    pause
    exit /b 1
)

REM Проверка, загружен ли образ
echo Проверка наличия образа...
docker images | findstr "document-translator-service" >nul
if errorlevel 1 (
    echo.
    echo [ПРЕДУПРЕЖДЕНИЕ] Образ не найден в Docker!
    echo.
    echo Сначала загрузите образ командой:
    echo   load-image.bat
    echo.
    pause
    exit /b 1
)

echo Образ найден. Запускаем сервис...
echo.

REM Остановка предыдущего контейнера (если запущен)
docker-compose down >nul 2>&1

REM Запуск сервиса
echo Запуск контейнеров...
docker-compose up -d

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Не удалось запустить сервис!
    echo.
    echo Просмотрите логи командой:
    echo   docker-compose logs
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Сервис успешно запущен!
echo ============================================
echo.

REM Ожидание запуска
echo Ожидание инициализации сервиса...
timeout /t 5 /nobreak >nul

REM Проверка статуса
echo.
echo Статус контейнеров:
docker-compose ps
echo.

REM Проверка здоровья
echo Проверка доступности API...
timeout /t 3 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [ПРЕДУПРЕЖДЕНИЕ] API пока не отвечает. Сервис может еще загружаться...
    echo Подождите 30-60 секунд и проверьте вручную:
    echo   http://localhost:8000/health
) else (
    echo [OK] API доступен!
)

echo.
echo ============================================
echo Полезные ссылки:
echo ============================================
echo API документация: http://localhost:8000/docs
echo Проверка здоровья: http://localhost:8000/health
echo.
echo Для просмотра логов: docker-compose logs -f
echo Для остановки: stop.bat
echo.
pause

