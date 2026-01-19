#!/bin/bash
# Скрипт для сборки CPU-ONLY Docker образа БЕЗ NVIDIA зависимостей

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

IMAGE_NAME=${1:-"document-translator"}
IMAGE_TAG=${2:-"cpu-only"}
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo "======================================================================"
echo "  🚀 Building CPU-ONLY Docker Image (NO NVIDIA/CUDA)"
echo "======================================================================"
echo ""
echo "📦 Image: $FULL_IMAGE_NAME"
echo "🎯 Target: CPU-only (no GPU/CUDA dependencies)"
echo ""

# Проверка файлов
if [ ! -f "Dockerfile.cpu-only" ]; then
    echo -e "${RED}❌ Error: Dockerfile.cpu-only not found${NC}"
    exit 1
fi

if [ ! -f ".pip-constraints.txt" ]; then
    echo -e "${YELLOW}⚠️  Warning: .pip-constraints.txt not found${NC}"
fi

# Начинаем сборку
echo -e "${BLUE}⏳ Starting build...${NC}"
echo ""

# Засекаем время
START_TIME=$(date +%s)

# Сборка с выводом прогресса
docker build \
    -f Dockerfile.cpu-only \
    -t "$FULL_IMAGE_NAME" \
    --progress=plain \
    . 2>&1 | tee build-cpu-only.log

# Проверяем результат
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    END_TIME=$(date +%s)
    BUILD_TIME=$((END_TIME - START_TIME))
    
    echo ""
    echo "======================================================================"
    echo -e "${GREEN}✅ Build SUCCESS!${NC}"
    echo "======================================================================"
    echo ""
    echo "📦 Image: $FULL_IMAGE_NAME"
    echo "⏱️  Build time: ${BUILD_TIME}s"
    echo ""
    
    # Показываем размер образа
    echo "📊 Image size:"
    docker images "$FULL_IMAGE_NAME" --format "  {{.Size}}"
    echo ""
    
    # Проверяем наличие NVIDIA пакетов в образе
    echo -e "${BLUE}🔍 Verifying NO NVIDIA packages...${NC}"
    if docker run --rm "$FULL_IMAGE_NAME" pip list 2>/dev/null | grep -i nvidia; then
        echo -e "${RED}❌ ERROR: NVIDIA packages found in image!${NC}"
        echo "Image built but contains unwanted NVIDIA dependencies."
        exit 1
    else
        echo -e "${GREEN}✅ VERIFIED: No NVIDIA packages found!${NC}"
    fi
    
    echo ""
    echo "======================================================================"
    echo "🎉 CPU-ONLY Image Ready!"
    echo "======================================================================"
    echo ""
    echo "Run with:"
    echo "  docker run -p 8000:8000 $FULL_IMAGE_NAME"
    echo ""
    
else
    echo ""
    echo "======================================================================"
    echo -e "${RED}❌ Build FAILED${NC}"
    echo "======================================================================"
    echo ""
    echo "Check build-cpu-only.log for details"
    exit 1
fi



