#!/bin/bash
# Скрипт для сборки оптимизированного Docker образа

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

IMAGE_NAME=${1:-"document-translator"}
IMAGE_TAG=${2:-"optimized"}
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo "======================================"
echo "  Building Optimized Docker Image"
echo "======================================"
echo ""
echo "📦 Image: $FULL_IMAGE_NAME"
echo ""

# Проверяем, существует ли Dockerfile.optimized
if [ ! -f "Dockerfile.optimized" ]; then
    echo -e "${RED}❌ Error: Dockerfile.optimized not found${NC}"
    exit 1
fi

# Проверяем, существует ли pyproject.toml
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: pyproject.toml not found${NC}"
    exit 1
fi

# Сохраняем размер старого образа (если существует)
OLD_SIZE=""
if docker image inspect "$FULL_IMAGE_NAME" &> /dev/null; then
    OLD_SIZE=$(docker images "$FULL_IMAGE_NAME" --format "{{.Size}}")
    echo -e "${YELLOW}ℹ️  Previous image size: $OLD_SIZE${NC}"
    echo ""
fi

# Собираем образ
echo "🔨 Building Docker image..."
echo ""

BUILD_START=$(date +%s)

# Используем BuildKit для улучшенной сборки
export DOCKER_BUILDKIT=1

docker build \
    -f Dockerfile.optimized \
    -t "$FULL_IMAGE_NAME" \
    --progress=plain \
    --no-cache \
    . 2>&1 | tee build.log

BUILD_END=$(date +%s)
BUILD_TIME=$((BUILD_END - BUILD_START))

echo ""
echo "✅ Build completed in ${BUILD_TIME}s"
echo ""

# Получаем размер нового образа
NEW_SIZE=$(docker images "$FULL_IMAGE_NAME" --format "{{.Size}}")
echo -e "${GREEN}📦 New image size: $NEW_SIZE${NC}"

# Сравниваем размеры
if [ -n "$OLD_SIZE" ]; then
    echo "📊 Size comparison:"
    echo "   Old: $OLD_SIZE"
    echo "   New: $NEW_SIZE"
    echo ""
fi

# Запускаем проверку размера
if [ -f "scripts/check-image-size.sh" ]; then
    echo "🔍 Running size analysis..."
    echo ""
    bash scripts/check-image-size.sh "$FULL_IMAGE_NAME"
else
    echo -e "${YELLOW}⚠️  Size analysis script not found${NC}"
fi

# Опционально: тегируем как latest
read -p "Tag as 'latest'? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker tag "$FULL_IMAGE_NAME" "${IMAGE_NAME}:latest"
    echo -e "${GREEN}✅ Tagged as ${IMAGE_NAME}:latest${NC}"
fi

echo ""
echo "======================================"
echo "  Build Complete"
echo "======================================"
echo ""
echo "To run the container:"
echo "  docker run -p 8000:8000 $FULL_IMAGE_NAME"
echo ""
echo "To test the container:"
echo "  docker run --rm $FULL_IMAGE_NAME python -c 'import paddleocr; import argostranslate'"
echo ""



