#!/bin/bash
# ============================================
# Сборка license-helper с PyArmor
# ============================================

set -e  # Выход при ошибке

echo "============================================"
echo "Building License Helper with PyArmor Protection"
echo "============================================"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

# Установка зависимостей
echo ""
echo "[1/5] Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyarmor pyinstaller

# Очистка предыдущих сборок
echo ""
echo "[2/5] Cleaning previous builds..."
rm -rf obfuscated dist build *.spec

# Создание директории для обфусцированного кода
echo ""
echo "[3/5] Obfuscating code with PyArmor..."
mkdir -p obfuscated
pyarmor gen -O obfuscated -r license_helper.py

# Копирование дополнительных файлов
[ -f "LICENSE" ] && cp LICENSE obfuscated/ || true

# Переход в директорию с обфусцированным кодом
cd obfuscated

# Сборка бинарника
echo ""
echo "[4/5] Building executable with PyInstaller..."

BUILD_ARGS="--onefile --name license-helper --clean"

# Скрытые импорты (необходимы после обфускации PyArmor)
BUILD_ARGS="$BUILD_ARGS --hidden-import fastapi"
BUILD_ARGS="$BUILD_ARGS --hidden-import uvicorn"
BUILD_ARGS="$BUILD_ARGS --hidden-import uvicorn.logging"
BUILD_ARGS="$BUILD_ARGS --hidden-import uvicorn.loops"
BUILD_ARGS="$BUILD_ARGS --hidden-import uvicorn.loops.auto"
BUILD_ARGS="$BUILD_ARGS --hidden-import uvicorn.protocols"
BUILD_ARGS="$BUILD_ARGS --hidden-import uvicorn.protocols.http"
BUILD_ARGS="$BUILD_ARGS --hidden-import uvicorn.protocols.http.auto"
BUILD_ARGS="$BUILD_ARGS --hidden-import uvicorn.protocols.websockets"
BUILD_ARGS="$BUILD_ARGS --hidden-import uvicorn.protocols.websockets.auto"
BUILD_ARGS="$BUILD_ARGS --hidden-import uvicorn.lifespan"
BUILD_ARGS="$BUILD_ARGS --hidden-import uvicorn.lifespan.on"
BUILD_ARGS="$BUILD_ARGS --hidden-import pydantic"
BUILD_ARGS="$BUILD_ARGS --hidden-import httpx"
BUILD_ARGS="$BUILD_ARGS --hidden-import cryptography"
BUILD_ARGS="$BUILD_ARGS --hidden-import cryptography.hazmat.primitives.asymmetric.padding"
BUILD_ARGS="$BUILD_ARGS --hidden-import cryptography.hazmat.primitives.hashes"
BUILD_ARGS="$BUILD_ARGS --hidden-import cryptography.hazmat.primitives.serialization"
BUILD_ARGS="$BUILD_ARGS --hidden-import cryptography.hazmat.backends"
BUILD_ARGS="$BUILD_ARGS --collect-all uvicorn"
BUILD_ARGS="$BUILD_ARGS --collect-all fastapi"

# Добавляем LICENSE если есть
if [ -f "LICENSE" ]; then
    BUILD_ARGS="$BUILD_ARGS --add-data LICENSE:."
fi

pyinstaller $BUILD_ARGS license_helper.py

echo ""
echo "[5/5] Copying executable to parent directory..."
cd ..
cp obfuscated/dist/license-helper ./license-helper
chmod +x license-helper

echo ""
echo "============================================"
echo "Build complete!"
echo "============================================"
echo ""
echo "Executable: license-helper"
echo ""
echo "To test:"
echo "  1. Run: ./license-helper"
echo "  2. Open: http://localhost:9999/health"
echo ""

