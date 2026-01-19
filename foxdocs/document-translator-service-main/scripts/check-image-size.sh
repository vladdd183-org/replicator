#!/bin/bash
# Скрипт для проверки размера Docker образа и анализа его содержимого

set -e

IMAGE_NAME=${1:-"document-translator:optimized"}

echo "======================================"
echo "  Docker Image Size Analysis"
echo "======================================"
echo ""

# Проверяем, существует ли образ
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo "❌ Error: Image '$IMAGE_NAME' not found"
    echo ""
    echo "Please build the image first:"
    echo "  docker build -f Dockerfile.optimized -t $IMAGE_NAME ."
    exit 1
fi

echo "📦 Image: $IMAGE_NAME"
echo ""

# Общий размер образа
echo "=== Total Image Size ==="
docker images "$IMAGE_NAME" --format "Size: {{.Size}}"
echo ""

# Размеры слоев
echo "=== Layer Sizes (Top 10) ==="
docker history "$IMAGE_NAME" --no-trunc --format "{{.Size}}\t{{.CreatedBy}}" | \
    grep -v "0B" | \
    head -10 | \
    awk '{
        size=$1;
        gsub(/\t/, " ", $0);
        cmd=substr($0, index($0, $2));
        if (length(cmd) > 60) cmd = substr(cmd, 1, 57) "...";
        printf "%-10s %s\n", size, cmd
    }'
echo ""

# Самые большие Python пакеты
echo "=== Largest Python Packages (Top 15) ==="
docker run --rm "$IMAGE_NAME" pip list --format=freeze 2>/dev/null | \
    xargs docker run --rm "$IMAGE_NAME" pip show 2>/dev/null | \
    awk '/^Name:/ {name=$2} /^Size:/ {if ($2 != "") print $2, name}' | \
    sort -n -r | \
    head -15 | \
    awk '{
        size=$1;
        name=$2;
        if (size >= 1048576) printf "%7.1f MB  %s\n", size/1048576, name;
        else if (size >= 1024) printf "%7.1f KB  %s\n", size/1024, name;
        else printf "%7d B   %s\n", size, name;
    }'
echo ""

# Проверка наличия CUDA зависимостей
echo "=== Checking for CUDA Dependencies ==="
CUDA_PACKAGES=$(docker run --rm "$IMAGE_NAME" pip list 2>/dev/null | grep -iE "(cuda|cudnn|cublas|cufft|nvidia)" || echo "")

if [ -z "$CUDA_PACKAGES" ]; then
    echo "✅ No CUDA packages found - image is CPU-only"
else
    echo "⚠️  WARNING: Found potential CUDA packages:"
    echo "$CUDA_PACKAGES"
fi
echo ""

# Проверка версий ключевых пакетов
echo "=== Key Package Versions ==="
docker run --rm "$IMAGE_NAME" python -c "
import sys
packages = [
    'paddlepaddle',
    'paddleocr', 
    'opencv-python-headless',
    'numpy',
    'pillow',
    'ctranslate2',
    'argostranslate',
    'pymupdf',
    'litestar'
]

for pkg in packages:
    try:
        mod = __import__(pkg.replace('-', '_'))
        version = getattr(mod, '__version__', 'unknown')
        print(f'{pkg:25} {version}')
    except ImportError:
        print(f'{pkg:25} NOT INSTALLED')
" 2>/dev/null
echo ""

# Размер образа в сравнении с целевым
echo "=== Size Comparison ==="
SIZE_MB=$(docker images "$IMAGE_NAME" --format "{{.Size}}" | sed 's/[^0-9.]//g')
TARGET_SIZE=800

if command -v bc &> /dev/null; then
    if (( $(echo "$SIZE_MB < $TARGET_SIZE" | bc -l) )); then
        echo "✅ Image size (${SIZE_MB}MB) is within target (${TARGET_SIZE}MB)"
    else
        DIFF=$(echo "$SIZE_MB - $TARGET_SIZE" | bc)
        echo "⚠️  Image size (${SIZE_MB}MB) exceeds target (${TARGET_SIZE}MB) by ${DIFF}MB"
    fi
else
    echo "Target size: ${TARGET_SIZE}MB"
    echo "Actual size: ${SIZE_MB}MB"
fi
echo ""

# Рекомендации
echo "=== Optimization Tips ==="
echo "1. Use 'docker build --squash' to merge layers (experimental)"
echo "2. Run 'dive $IMAGE_NAME' for detailed layer analysis"
echo "3. Check for duplicate dependencies in different layers"
echo "4. Consider using distroless base image for even smaller size"
echo ""

echo "======================================"
echo "  Analysis Complete"
echo "======================================"



