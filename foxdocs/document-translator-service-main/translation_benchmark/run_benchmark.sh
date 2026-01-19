#!/bin/bash

# Скрипт для запуска бенчмарка переводчиков
# Автоматически активирует виртуальное окружение и запускает тесты

set -e

echo "🌐 Запуск бенчмарка переводчиков"
echo "================================"
echo ""

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "⚠️  Виртуальное окружение не найдено!"
    echo "📦 Создаём виртуальное окружение..."
    python3 -m venv venv
    echo "✅ Виртуальное окружение создано"
    echo ""
fi

# Активируем виртуальное окружение
echo "🔌 Активация виртуального окружения..."
source venv/bin/activate

# Проверяем наличие зависимостей
if ! python3 -c "import argostranslate" 2>/dev/null; then
    echo "⚠️  Зависимости не установлены!"
    echo "📦 Устанавливаем зависимости..."
    echo ""
    
    # Устанавливаем PyTorch CPU-only
    echo "🔧 Установка PyTorch (CPU-only)..."
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    
    # Устанавливаем остальные зависимости
    echo "🔧 Установка остальных зависимостей..."
    pip install -r requirements.txt
    
    echo ""
    echo "✅ Все зависимости установлены"
    echo ""
fi

# Проверяем CUDA
if python3 -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
    echo "⚠️  CUDA обнаружена! Этот бенчмарк использует ТОЛЬКО CPU."
    echo "📝 Устанавливаем переменную окружения для отключения CUDA..."
    export CUDA_VISIBLE_DEVICES=""
fi

# Запускаем бенчмарк
echo "🚀 Запуск бенчмарка..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 benchmark_translators.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Бенчмарк завершён!"
echo ""
echo "📄 Результаты сохранены в Markdown файл:"
ls -t benchmark_results_*.md 2>/dev/null | head -1 || echo "   (файл не найден)"
echo ""
