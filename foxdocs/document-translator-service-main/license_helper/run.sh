#!/bin/bash
# ============================================
# Запуск License Helper напрямую (без сборки)
# ============================================

echo "============================================"
echo "Starting License Helper Service"
echo "============================================"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

# Установка зависимостей (если не установлены)
if ! python3 -c "import fastapi" &> /dev/null; then
    echo ""
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Запуск
echo ""
echo "Starting license-helper service..."
echo "Press Ctrl+C to stop"
echo ""

python3 license_helper.py





