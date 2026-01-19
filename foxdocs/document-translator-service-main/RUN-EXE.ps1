# ===================================================================
# Script to run DocumentTranslator.exe in PRODUCTION mode
# ===================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Document Translator Service" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables for PRODUCTION mode
$env:APP_ENV = "production"
$env:APP_DEBUG = "False"
$env:APP_HOST = "0.0.0.0"
$env:APP_PORT = "8000"

# Optional: Set LOGFIRE_TOKEN if you have one
# $env:LOGFIRE_TOKEN = "your-token-here"

Write-Host "[INFO] Starting in PRODUCTION mode..." -ForegroundColor Green
Write-Host "[INFO] Server will start on http://$($env:APP_HOST):$($env:APP_PORT)" -ForegroundColor Green
Write-Host "[INFO] Press CTRL+C to stop" -ForegroundColor Yellow
Write-Host ""

# Run the application
.\DocumentTranslator.exe

