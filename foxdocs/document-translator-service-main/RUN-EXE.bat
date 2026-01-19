@echo off
REM ===================================================================
REM Script to run DocumentTranslator.exe in PRODUCTION mode
REM ===================================================================

echo ========================================
echo Document Translator Service
echo ========================================
echo.

REM Set environment variables for PRODUCTION mode
set APP_ENV=production
set APP_DEBUG=False
set APP_HOST=0.0.0.0
set APP_PORT=8000

REM Optional: Set LOGFIRE_TOKEN if you have one
REM set LOGFIRE_TOKEN=your-token-here

echo [INFO] Starting in PRODUCTION mode...
echo [INFO] Server will start on http://%APP_HOST%:%APP_PORT%
echo [INFO] Press CTRL+C to stop
echo.

REM Run the application
DocumentTranslator.exe

pause

