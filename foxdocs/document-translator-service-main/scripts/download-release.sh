#!/bin/bash
# ============================================
# Скрипт для скачивания релиза с сервера
# ============================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка аргументов
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <ssh_connection> [release_date] [output_dir]"
    echo ""
    echo "Examples:"
    echo "  $0 user@server.com                              # Download latest release"
    echo "  $0 user@server.com 2025-01-15_14-30-00          # Download specific release"
    echo "  $0 user@server.com 2025-01-15_14-30-00 ./releases # Download to specific directory"
    echo ""
    echo "Available releases:"
    echo "  $0 user@server.com --list"
    exit 1
fi

SSH_CONNECTION="$1"
RELEASE_DATE="${2:-latest}"
OUTPUT_DIR="${3:-.}"
RELEASE_BASE_DIR="/root/licenser-server/releases"

print_info "Connecting to server: $SSH_CONNECTION"

# ============================================
# Список доступных релизов
# ============================================
if [ "$RELEASE_DATE" == "--list" ]; then
    print_info "Fetching list of available releases..."
    ssh "$SSH_CONNECTION" "ls -lt $RELEASE_BASE_DIR/ | grep '^d' | awk '{print \$9}' | head -20"
    exit 0
fi

# ============================================
# Получение последнего релиза
# ============================================
if [ "$RELEASE_DATE" == "latest" ]; then
    print_info "Fetching latest release..."
    RELEASE_DATE=$(ssh "$SSH_CONNECTION" "ls -t $RELEASE_BASE_DIR/ | head -1")
    
    if [ -z "$RELEASE_DATE" ]; then
        print_error "No releases found on server"
        exit 1
    fi
    
    print_success "Latest release: $RELEASE_DATE"
fi

RELEASE_PATH="$RELEASE_BASE_DIR/$RELEASE_DATE"

# ============================================
# Проверка существования релиза
# ============================================
print_info "Checking if release exists..."
if ! ssh "$SSH_CONNECTION" "[ -d '$RELEASE_PATH' ]"; then
    print_error "Release not found: $RELEASE_PATH"
    print_info "Available releases:"
    ssh "$SSH_CONNECTION" "ls -lt $RELEASE_BASE_DIR/ | grep '^d' | awk '{print \$9}' | head -10"
    exit 1
fi

# ============================================
# Получение информации о релизе
# ============================================
print_info "Fetching release information..."
RELEASE_SIZE=$(ssh "$SSH_CONNECTION" "du -sh $RELEASE_PATH | cut -f1")
FILE_COUNT=$(ssh "$SSH_CONNECTION" "find $RELEASE_PATH -type f | wc -l")

echo ""
echo "=========================================="
echo "Release Information"
echo "=========================================="
echo "Date:       $RELEASE_DATE"
echo "Size:       $RELEASE_SIZE"
echo "Files:      $FILE_COUNT"
echo "Source:     $RELEASE_PATH"
echo "Destination: $OUTPUT_DIR/$RELEASE_DATE"
echo "=========================================="
echo ""

# ============================================
# Подтверждение скачивания
# ============================================
read -p "Download this release? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Download cancelled"
    exit 0
fi

# ============================================
# Создание директории для скачивания
# ============================================
mkdir -p "$OUTPUT_DIR"

# ============================================
# Скачивание релиза
# ============================================
print_info "Downloading release..."
print_info "This may take a while depending on file size and network speed..."

# Используем rsync для более надёжного скачивания с прогресс-баром
if command -v rsync &> /dev/null; then
    rsync -avz --progress "$SSH_CONNECTION:$RELEASE_PATH" "$OUTPUT_DIR/"
else
    # Fallback на scp если rsync не установлен
    scp -r "$SSH_CONNECTION:$RELEASE_PATH" "$OUTPUT_DIR/"
fi

# ============================================
# Проверка скачанных файлов
# ============================================
DOWNLOAD_PATH="$OUTPUT_DIR/$RELEASE_DATE"

if [ ! -d "$DOWNLOAD_PATH" ]; then
    print_error "Download failed: directory not found"
    exit 1
fi

print_success "Download complete!"
echo ""
echo "=========================================="
echo "Downloaded Files"
echo "=========================================="
ls -lh "$DOWNLOAD_PATH"
echo "=========================================="
echo ""

# ============================================
# Проверка манифеста
# ============================================
if [ -f "$DOWNLOAD_PATH/release-manifest.json" ]; then
    print_info "Release manifest found:"
    cat "$DOWNLOAD_PATH/release-manifest.json"
    echo ""
fi

# ============================================
# Проверка README
# ============================================
if [ -f "$DOWNLOAD_PATH/README.md" ]; then
    print_info "README found. Opening..."
    if command -v bat &> /dev/null; then
        bat "$DOWNLOAD_PATH/README.md"
    elif command -v less &> /dev/null; then
        less "$DOWNLOAD_PATH/README.md"
    else
        cat "$DOWNLOAD_PATH/README.md"
    fi
fi

echo ""
print_success "Release downloaded successfully to: $DOWNLOAD_PATH"
echo ""
print_info "Next steps:"
echo "  1. cd $DOWNLOAD_PATH"
echo "  2. Read README.md for installation instructions"
echo "  3. Run ./install.sh to install (requires Docker)"
echo ""

