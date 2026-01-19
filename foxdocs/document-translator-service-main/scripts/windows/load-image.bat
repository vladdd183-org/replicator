@echo off
REM ============================================
REM Скрипт загрузки Docker образа
REM Document Translator Service
REM ============================================

echo.
echo ============================================
echo   Загрузка Docker образа
echo ============================================
echo.

REM Проверка запуска Docker Desktop
echo Проверка Docker...
docker version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Docker не запущен!
    echo.
    echo Пожалуйста:
    echo 1. Запустите Docker Desktop
    echo 2. Дождитесь сообщения "Engine started" или зеленого индикатора в трее
    echo 3. Запустите этот скрипт снова
    echo.
    pause
    exit /b 1
)

echo Docker работает. Продолжаем...
echo.

REM Поиск файла образа
echo Поиск файла образа...
for %%f in (docker-image-*.tar) do (
    set IMAGE_FILE=%%f
    goto :found
)

echo [ОШИБКА] Файл образа не найден!
echo Убедитесь, что файл docker-image-*.tar находится в этой папке.
echo.
pause
exit /b 1

:found
echo Найден образ: %IMAGE_FILE%
echo.

REM Проверка размера файла (предупреждение)
echo [ВНИМАНИЕ] Загрузка образа может занять несколько минут...
echo.

REM Загрузка образа
echo Загрузка образа в Docker...
docker load -i "%IMAGE_FILE%"

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Не удалось загрузить образ!
    echo Проверьте, что файл не поврежден.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Образ успешно загружен!
echo ============================================
echo.
echo Проверка загруженных образов:
docker images | findstr "document-translator"
echo.
echo Теперь вы можете:
echo 1. Запустить сервис: start.bat
echo 2. Запустить License Helper: license-helper-*.exe
echo.
pause

