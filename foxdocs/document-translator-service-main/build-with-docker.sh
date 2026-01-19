#!/bin/bash
# ============================================
# Скрипт для сборки Windows EXE через Docker (Wine)
# Использует: Dockerfile.windows-builder-wine
# ============================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Building Windows EXE with Docker (Wine)${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Генерация версии
VERSION=$(date +%Y.%m.%d)
SHA_SHORT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
FULL_VERSION="v${VERSION}-${SHA_SHORT}"

echo -e "${YELLOW}Version: ${FULL_VERSION}${NC}"
echo ""

# Создание директории для выходных файлов
OUTPUT_DIR="./release-output"
mkdir -p "$OUTPUT_DIR"

# Сборка Docker образа
echo -e "${GREEN}Step 1/3: Building Docker image...${NC}"
echo -e "${YELLOW}Using: Dockerfile.windows-builder-simple${NC}"
docker build \
  --build-arg VERSION="$VERSION" \
  --build-arg SHA_SHORT="$SHA_SHORT" \
  -f Dockerfile.windows-builder-simple \
  -t document-translator-builder:latest \
  .

echo ""
echo -e "${GREEN}Step 2/3: Running container to extract files...${NC}"

# Запуск контейнера и копирование файлов
CONTAINER_ID=$(docker create document-translator-builder:latest)

# Копируем файлы из контейнера
docker cp "${CONTAINER_ID}:/release/." "$OUTPUT_DIR/"

# Удаляем контейнер
docker rm "$CONTAINER_ID"

echo ""
echo -e "${GREEN}Step 3/3: Cleanup...${NC}"

# Опционально: удаляем образ для экономии места
# docker rmi document-translator-builder:latest

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ Build Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Files created in: ${YELLOW}${OUTPUT_DIR}${NC}"
echo ""
ls -lh "$OUTPUT_DIR"
echo ""
echo -e "Archive: ${YELLOW}$(ls -1 ${OUTPUT_DIR}/*.tar.gz 2>/dev/null || echo 'Not created')${NC}"
echo ""

