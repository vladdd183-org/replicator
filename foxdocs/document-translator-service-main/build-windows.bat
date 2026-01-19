@echo off
REM ===================================================================
REM Wrapper для запуска PowerShell скрипта сборки
REM ===================================================================

echo ========================================
echo Document Translator Service - Build
echo ========================================
echo.

REM Проверка PowerShell
where powershell >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PowerShell не найден!
    echo Установите PowerShell или запустите скрипт вручную.
    pause
    exit /b 1
)

echo Запуск сборки через PowerShell...
echo Это может занять 20-40 минут в зависимости от скорости интернета и CPU.
echo.

REM Запуск PowerShell скрипта с правами выполнения
powershell -ExecutionPolicy Bypass -File "%~dp0build-windows.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Сборка завершена успешно!
    echo ========================================
    echo Дистрибутив находится в: dist\DocumentTranslator\
) else (
    echo.
    echo ========================================
    echo [ERROR] Сборка завершилась с ошибкой!
    echo ========================================
)

pause

