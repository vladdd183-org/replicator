#!/bin/bash
# ============================================
# Скрипт для просмотра релизов на сервере
# ============================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка аргументов
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <ssh_connection> [limit]"
    echo ""
    echo "Examples:"
    echo "  $0 user@server.com          # List latest 20 releases"
    echo "  $0 user@server.com 50       # List latest 50 releases"
    echo "  $0 user@server.com all      # List all releases"
    exit 1
fi

SSH_CONNECTION="$1"
LIMIT="${2:-20}"
RELEASE_BASE_DIR="/root/licenser-server/releases"

print_info "Connecting to server: $SSH_CONNECTION"

# ============================================
# Проверка директории релизов
# ============================================
if ! ssh "$SSH_CONNECTION" "[ -d '$RELEASE_BASE_DIR' ]"; then
    print_error "Releases directory not found on server: $RELEASE_BASE_DIR"
    exit 1
fi

# ============================================
# Получение общей информации
# ============================================
print_info "Fetching releases information..."

TOTAL_COUNT=$(ssh "$SSH_CONNECTION" "find $RELEASE_BASE_DIR -maxdepth 1 -type d | tail -n +2 | wc -l")
TOTAL_SIZE=$(ssh "$SSH_CONNECTION" "du -sh $RELEASE_BASE_DIR | cut -f1")

echo ""
echo "=========================================="
echo "Releases Overview"
echo "=========================================="
echo "Total Releases: $TOTAL_COUNT"
echo "Total Size:     $TOTAL_SIZE"
echo "Location:       $RELEASE_BASE_DIR"
echo "=========================================="
echo ""

# ============================================
# Список релизов
# ============================================
print_info "Fetching release list..."

if [ "$LIMIT" == "all" ]; then
    RELEASES=$(ssh "$SSH_CONNECTION" "ls -lt $RELEASE_BASE_DIR/ | grep '^d' | awk '{print \$9, \$6, \$7, \$8}'")
else
    RELEASES=$(ssh "$SSH_CONNECTION" "ls -lt $RELEASE_BASE_DIR/ | grep '^d' | head -$LIMIT | awk '{print \$9, \$6, \$7, \$8}'")
fi

echo "=========================================="
echo "Available Releases"
echo "=========================================="

if [ -z "$RELEASES" ]; then
    print_warning "No releases found"
else
    printf "%-30s | %-12s | %-s\n" "Release Date" "Size" "Modified"
    echo "----------------------------------------"
    
    # Получаем размер для каждого релиза
    echo "$RELEASES" | while read -r release_name month day time; do
        if [ -n "$release_name" ]; then
            size=$(ssh "$SSH_CONNECTION" "du -sh $RELEASE_BASE_DIR/$release_name 2>/dev/null | cut -f1")
            printf "%-30s | %-12s | %s %s %s\n" "$release_name" "$size" "$month" "$day" "$time"
        fi
    done
fi

echo "=========================================="
echo ""

# ============================================
# Последний релиз (детальная информация)
# ============================================
LATEST=$(ssh "$SSH_CONNECTION" "ls -t $RELEASE_BASE_DIR/ | head -1")

if [ -n "$LATEST" ]; then
    print_success "Latest Release: $LATEST"
    echo ""
    print_info "Files in latest release:"
    
    ssh "$SSH_CONNECTION" "ls -lh $RELEASE_BASE_DIR/$LATEST/" | tail -n +2 | while read line; do
        echo "  $line"
    done
    
    echo ""
    
    # Показать манифест если есть
    if ssh "$SSH_CONNECTION" "[ -f '$RELEASE_BASE_DIR/$LATEST/release-manifest.json' ]"; then
        print_info "Release manifest:"
        ssh "$SSH_CONNECTION" "cat $RELEASE_BASE_DIR/$LATEST/release-manifest.json" | while read line; do
            echo "  $line"
        done
    fi
fi

echo ""
print_info "To download a release, use:"
echo "  ./scripts/download-release.sh $SSH_CONNECTION [release_name]"
echo ""

