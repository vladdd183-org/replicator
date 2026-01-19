#!/bin/bash
# ===================================================================
# Build Windows EXE using Docker
# Works on Linux/Mac - builds Windows executable via Wine
# ===================================================================

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Docker
if ! command -v docker &> /dev/null; then
    error "Docker не найден! Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    error "Docker Compose не найден!"
    exit 1
fi

# Build mode selection
BUILD_MODE="${1:-onedir}"

case "$BUILD_MODE" in
    onedir)
        info "Режим: ONE-DIR (папка с EXE и зависимостями)"
        SERVICE="build-onedir"
        ;;
    onefile)
        info "Режим: ONE-FILE (один большой EXE файл)"
        warn "Первый запуск будет медленнее из-за распаковки"
        SERVICE="build-onefile"
        ;;
    *)
        error "Неизвестный режим: $BUILD_MODE"
        echo "Использование: $0 [onedir|onefile]"
        echo "  onedir  - папка с EXE и зависимостями (быстрее, рекомендуется)"
        echo "  onefile - один файл EXE (проще распространять)"
        exit 1
        ;;
esac

echo ""
info "========================================"
info "Windows EXE Build via Docker"
info "========================================"
info "Режим: $BUILD_MODE"
info "Использует готовый PyInstaller образ"
info "Начало: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Clean previous build
if [ -d "dist" ]; then
    warn "Очистка предыдущей сборки..."
    rm -rf dist/*
fi

if [ -d "build" ]; then
    rm -rf build/*
fi

# Build Docker image
info "Сборка Docker образа (может занять 10-20 минут при первом запуске)..."
docker-compose -f docker-compose.build.yml build "$SERVICE"

if [ $? -ne 0 ]; then
    error "Не удалось собрать Docker образ"
    exit 1
fi

success "Docker образ собран"

# Run build
info "Запуск сборки Windows EXE..."
info "Это может занять 30-60 минут..."
echo ""

docker-compose -f docker-compose.build.yml run --rm "$SERVICE"

if [ $? -ne 0 ]; then
    error "Ошибка сборки"
    exit 1
fi

# Check result
echo ""
warn "================================================"
warn "⚠️  Docker собирает LINUX binary, НЕ Windows!"
warn "================================================"
warn "Для Windows EXE → build-windows.ps1 на Windows"
warn "================================================"
echo ""

# Check for Linux binary (what Docker actually produces)
LINUX_PATH="dist/DocumentTranslator"
WIN_PATH_ONEFILE="dist/DocumentTranslator.exe"
WIN_PATH_ONEDIR="dist/DocumentTranslator/DocumentTranslator.exe"

if [ -f "$LINUX_PATH" ]; then
    SIZE=$(du -h "$LINUX_PATH" | cut -f1)
    success "========================================"
    success "✅ LINUX BINARY СОЗДАН УСПЕШНО!"
    success "========================================"
    info "Файл: $LINUX_PATH"
    info "Размер: $SIZE"
    info "Платформа: Linux ELF 64-bit"
    echo ""
    info "Для запуска на Linux:"
    info "  chmod +x dist/DocumentTranslator"
    info "  ./dist/DocumentTranslator"
    echo ""
    warn "⚠️  Это НЕ Windows .exe файл!"
    warn "⚠️  Для Windows используйте build-windows.ps1"
elif [ -f "$WIN_PATH_ONEFILE" ]; then
    SIZE=$(du -h "$WIN_PATH_ONEFILE" | cut -f1)
    success "✅ Windows EXE создан: $WIN_PATH_ONEFILE"
    info "Размер: $SIZE"
elif [ -f "$WIN_PATH_ONEDIR" ]; then
    SIZE=$(du -h "$WIN_PATH_ONEDIR" | cut -f1)
    success "✅ Windows EXE создан: $WIN_PATH_ONEDIR"
    info "Размер: $SIZE"
else
    error "❌ Бинарный файл не найден"
    if [ -d "dist" ]; then
        info "Содержимое dist/:"
        ls -lh dist/
    fi
    exit 1
fi

info "Завершено: $(date '+%Y-%m-%d %H:%M:%S')"


