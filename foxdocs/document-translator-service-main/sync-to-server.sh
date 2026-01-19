#!/bin/bash

# Скрипт для синхронизации проекта на сервер через rsync
# Использование: ./sync-to-server.sh

# Конфигурация
REMOTE_USER="kubeadmin"
REMOTE_HOST="79.111.12.145"
REMOTE_PATH="~/pupupu"
LOCAL_PATH="/home/vladdd183/Рабочий стол/document-translator-service"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔄 Начинаю синхронизацию с сервером...${NC}"
echo "Локальная папка: $LOCAL_PATH"
echo "Удалённая папка: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"
echo ""

# Выполняем rsync с исключениями
rsync -avz --progress \
  --delete \
  --exclude-from="$LOCAL_PATH/.rsyncignore" \
  --exclude='.git/' \
  --exclude='.gitignore' \
  --exclude='*.log' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='venv/' \
  --exclude='env/' \
  --exclude='.venv/' \
  --exclude='ENV/' \
  --exclude='.env' \
  --exclude='.env.local' \
  --exclude='*.db' \
  --exclude='*.sqlite*' \
  --exclude='.pytest_cache/' \
  --exclude='.mypy_cache/' \
  --exclude='.ruff_cache/' \
  --exclude='.coverage' \
  --exclude='htmlcov/' \
  --exclude='.DS_Store' \
  --exclude='Thumbs.db' \
  --exclude='*.tmp' \
  --exclude='*.bak' \
  --exclude='*.swp' \
  --exclude='*~' \
  --exclude='.vscode/' \
  --exclude='.idea/' \
  --exclude='.cursor/' \
  --exclude='foxdocs/' \
  --exclude='translation_benchmark/venv/' \
  --exclude='license_helper/venv/' \
  --exclude='.logfire/' \
  --exclude='node_modules/' \
  --exclude='dist/' \
  --exclude='build/' \
  "$LOCAL_PATH/" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"

# Проверяем результат
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Синхронизация завершена успешно!${NC}"
else
    echo ""
    echo -e "${RED}❌ Ошибка при синхронизации!${NC}"
    exit 1
fi




