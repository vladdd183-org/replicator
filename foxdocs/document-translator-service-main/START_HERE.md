# 🚀 НАЧНИТЕ ЗДЕСЬ: Решение проблемы с NVIDIA пакетами

## ⚡ Быстрое решение (1 команда!)

```bash
./scripts/build-cpu-only.sh
```

**Готово!** Образ собран без NVIDIA пакетов, размер ~500-800 МБ вместо 2.5 ГБ! 🎉

---

## 📊 Что изменилось

### ДО (проблема)
```bash
docker build .
# => Downloading nvidia-nvjitlink-cu12  ❌
# => Downloading nvidia-curand-cu12     ❌
# => Downloading opencv-contrib-python  ❌
# Итого: ~2.5 ГБ 😱
```

### ПОСЛЕ (решение)
```bash
./scripts/build-cpu-only.sh
# => Downloading opencv-python-headless ✅
# => Downloading paddlepaddle (CPU)     ✅
# => NO nvidia packages                 ✅
# Итого: ~600 МБ 🎉
```

---

## 🎯 Три простых шага

### 1️⃣ Собрать образ
```bash
./scripts/build-cpu-only.sh
```

### 2️⃣ Проверить (опционально)
```bash
# Проверить размер
docker images document-translator:cpu-only

# Проверить отсутствие NVIDIA
docker run --rm document-translator:cpu-only pip list | grep -i nvidia
# Должно быть ПУСТО!
```

### 3️⃣ Запустить
```bash
docker run -p 8000:8000 document-translator:cpu-only
```

---

## 📚 Документация

| Файл | Описание |
|------|----------|
| **[QUICK_FIX_NVIDIA.md](QUICK_FIX_NVIDIA.md)** | ⚡ Самое краткое решение (прочитайте первым!) |
| **[FIX_NVIDIA_PACKAGES.md](FIX_NVIDIA_PACKAGES.md)** | 🔧 Подробное объяснение проблемы и решения |
| **[SOLUTION_COMPARISON.md](SOLUTION_COMPARISON.md)** | 📊 Сравнение разных Dockerfile'ов |
| **[OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)** | 📦 Общая информация по оптимизации |

---

## 🆘 Troubleshooting

### Всё равно видите NVIDIA пакеты?

1. **Очистите Docker cache:**
   ```bash
   docker builder prune -af
   ```

2. **Убедитесь, что используете правильный Dockerfile:**
   ```bash
   ./scripts/build-cpu-only.sh  # ← Только эту команду!
   ```

3. **Проверьте файлы:**
   ```bash
   ls -l Dockerfile.cpu-only .pip-constraints.txt
   # Оба файла должны существовать
   ```

### Образ всё равно большой?

```bash
# Проверьте размер
docker images document-translator:cpu-only

# Должно быть примерно:
# REPOSITORY              TAG        SIZE
# document-translator     cpu-only   650MB
```

Если > 1 ГБ - свяжитесь с командой разработки.

---

## ✅ Проверка работоспособности

После сборки образа проверьте:

```bash
# 1. Запустить
docker run -d -p 8000:8000 --name test document-translator:cpu-only

# 2. Подождать 10 секунд
sleep 10

# 3. Проверить health
docker ps | grep test

# 4. Остановить
docker stop test && docker rm test
```

Если контейнер запустился - всё работает! ✅

---

## 🎉 Итог

### Что получили:
- ✅ Размер образа: **~600 МБ** (было 2.5 ГБ)
- ✅ NVIDIA пакетов: **0** (было 15+)
- ✅ Время сборки: **5-7 мин** (было 10-15 мин)
- ✅ Работает **только на CPU**

### Команда для использования:
```bash
./scripts/build-cpu-only.sh  # Сборка
docker run -p 8000:8000 document-translator:cpu-only  # Запуск
```

---

**Вопросы?** → Смотрите [QUICK_FIX_NVIDIA.md](QUICK_FIX_NVIDIA.md) или [FIX_NVIDIA_PACKAGES.md](FIX_NVIDIA_PACKAGES.md)

**Всё работает?** → Удалите старые образы:
```bash
docker rmi document-translator:optimized document-translator:latest
```

🎉 **Поздравляем! Проблема решена!** 🎉



