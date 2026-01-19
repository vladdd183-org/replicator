#!/bin/bash
# ============================================
# Сборка license-helper для Linux
# ============================================

echo "============================================"
echo "Building License Helper Service for Linux"
echo "============================================"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

# Установка зависимостей
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# Сборка бинарника
echo ""
echo "Building executable..."
pyinstaller --onefile \
    --name license-helper \
    license_helper.py

echo ""
echo "============================================"
echo "Build complete!"
echo "============================================"
echo ""
echo "Executable: dist/license-helper"
echo ""
echo "You can now:"
echo "  1. Run directly: ./dist/license-helper"
echo "  2. Install as service: sudo ./install_as_service.sh"
echo ""





