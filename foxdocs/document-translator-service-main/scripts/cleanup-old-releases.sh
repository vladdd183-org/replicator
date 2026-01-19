#!/bin/bash
# ============================================
# Скрипт для очистки старых релизов на сервере
# ============================================

set -e

RELEASES_DIR="${RELEASES_DIR:-/root/licenser-server/releases}"
ARCHIVE_DIR="${ARCHIVE_DIR:-/root/licenser-server/archives}"
DAYS_OLD="${DAYS_OLD:-30}"
DRY_RUN="${DRY_RUN:-false}"

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

# ============================================
# Проверка директорий
# ============================================
if [ ! -d "$RELEASES_DIR" ]; then
    print_error "Releases directory not found: $RELEASES_DIR"
    exit 1
fi

print_info "Cleanup Configuration:"
echo "  Releases Directory: $RELEASES_DIR"
echo "  Archive Directory:  $ARCHIVE_DIR"
echo "  Days Old Threshold: $DAYS_OLD"
echo "  Dry Run:            $DRY_RUN"
echo ""

# Создание директории для архивов
mkdir -p "$ARCHIVE_DIR"

# ============================================
# Поиск старых релизов
# ============================================
print_info "Searching for releases older than $DAYS_OLD days..."

OLD_RELEASES=$(find "$RELEASES_DIR" -maxdepth 1 -type d -mtime +$DAYS_OLD ! -path "$RELEASES_DIR")

if [ -z "$OLD_RELEASES" ]; then
    print_success "No old releases found"
    exit 0
fi

# Подсчёт количества и размера
RELEASE_COUNT=$(echo "$OLD_RELEASES" | wc -l)
TOTAL_SIZE=$(du -sh "$RELEASES_DIR" | cut -f1)

echo ""
echo "=========================================="
echo "Old Releases Found"
echo "=========================================="
echo "Count: $RELEASE_COUNT"
echo "Total releases size: $TOTAL_SIZE"
echo ""
echo "Releases to be archived/removed:"
echo "$OLD_RELEASES" | while read dir; do
    if [ -n "$dir" ] && [ "$dir" != "$RELEASES_DIR" ]; then
        basename=$(basename "$dir")
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        mtime=$(stat -c %y "$dir" | cut -d' ' -f1)
        echo "  - $basename (Size: $size, Modified: $mtime)"
    fi
done
echo "=========================================="
echo ""

# ============================================
# Подтверждение
# ============================================
if [ "$DRY_RUN" == "false" ]; then
    read -p "Proceed with archiving and cleanup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Cleanup cancelled"
        exit 0
    fi
fi

# ============================================
# Архивация и удаление
# ============================================
ARCHIVED_COUNT=0
FAILED_COUNT=0

echo "$OLD_RELEASES" | while read dir; do
    if [ -z "$dir" ] || [ "$dir" == "$RELEASES_DIR" ]; then
        continue
    fi
    
    basename=$(basename "$dir")
    archive_file="$ARCHIVE_DIR/${basename}.tar.gz"
    
    print_info "Processing: $basename"
    
    if [ "$DRY_RUN" == "true" ]; then
        print_info "[DRY RUN] Would archive: $basename -> $archive_file"
        print_info "[DRY RUN] Would remove: $dir"
        continue
    fi
    
    # Архивация
    print_info "  Archiving..."
    if tar -czf "$archive_file" -C "$RELEASES_DIR" "$basename" 2>/dev/null; then
        archive_size=$(du -sh "$archive_file" | cut -f1)
        print_success "  Archived: $archive_file ($archive_size)"
        
        # Удаление оригинала
        print_info "  Removing original..."
        if rm -rf "$dir"; then
            print_success "  Removed: $dir"
            ARCHIVED_COUNT=$((ARCHIVED_COUNT + 1))
        else
            print_error "  Failed to remove: $dir"
            FAILED_COUNT=$((FAILED_COUNT + 1))
        fi
    else
        print_error "  Failed to archive: $basename"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    
    echo ""
done

# ============================================
# Итоги
# ============================================
echo ""
echo "=========================================="
echo "Cleanup Summary"
echo "=========================================="

if [ "$DRY_RUN" == "true" ]; then
    print_warning "DRY RUN MODE - No changes were made"
    echo "Releases that would be processed: $RELEASE_COUNT"
else
    echo "Total processed: $RELEASE_COUNT"
    echo "Successfully archived: $ARCHIVED_COUNT"
    echo "Failed: $FAILED_COUNT"
    
    NEW_SIZE=$(du -sh "$RELEASES_DIR" | cut -f1)
    ARCHIVE_SIZE=$(du -sh "$ARCHIVE_DIR" | cut -f1)
    
    echo ""
    echo "Storage Information:"
    echo "  Releases directory: $NEW_SIZE"
    echo "  Archives directory: $ARCHIVE_SIZE"
fi

echo "=========================================="

if [ "$DRY_RUN" == "true" ]; then
    echo ""
    print_info "To perform actual cleanup, run:"
    echo "  DRY_RUN=false $0"
fi

if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
fi

exit 0

