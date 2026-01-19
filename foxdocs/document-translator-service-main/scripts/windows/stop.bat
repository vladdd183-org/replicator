@echo off
REM ============================================
REM Скрипт остановки Document Translator Service
REM ============================================

echo.
echo ============================================
echo   Остановка Document Translator Service
echo ============================================
echo.

REM Проверка Docker
docker version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Docker не запущен!
    echo Если контейнеры запущены, сначала запустите Docker Desktop.
    echo.
    pause
    exit /b 1
)

REM Проверка наличия docker-compose.yml
if not exist "docker-compose.yml" (
    echo [ОШИБКА] Файл docker-compose.yml не найден!
    echo Убедитесь, что вы находитесь в папке с релизом.
    echo.
    pause
    exit /b 1
)

echo Остановка контейнеров...
docker-compose down

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Не удалось остановить контейнеры!
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Сервис успешно остановлен!
echo ============================================
echo.

REM Проверка, что контейнеры остановлены
echo Проверка статуса:
docker ps -a | findstr "doctrans" >nul
if not errorlevel 1 (
    echo [INFO] Остановленные контейнеры все еще существуют.
    echo Они будут удалены при следующем запуске start.bat
) else (
    echo [OK] Контейнеры полностью удалены.
)

echo.
echo Для запуска снова используйте: start.bat
echo.
pause

