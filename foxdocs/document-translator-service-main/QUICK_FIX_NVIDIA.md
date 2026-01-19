# ⚡ БЫСТРОЕ ИСПРАВЛЕНИЕ: Убрать NVIDIA пакеты

## 🎯 Проблема
При сборке видите:
```
=> => #  Downloading nvidia-nvjitlink-cu12
=> => #  Downloading ctranslate2
=> => #  Downloading opencv-contrib-python  # ❌ Это не headless!
=> => #  Downloading nvidia-curand-cu12
```

## ✅ Решение за 1 команду

```bash
./scripts/build-cpu-only.sh
```

**Вот и всё!** 🎉

## 📊 Что вы получите

| До | После |
|-----|--------|
| 2.5-3 ГБ | **500-800 МБ** |
| 15+ NVIDIA пакетов | **0 NVIDIA пакетов** |
| 10-15 мин сборка | **5-7 мин** |

## 🔍 Проверка

```bash
# После сборки
docker run --rm document-translator:cpu-only pip list | grep -i nvidia
# Должно быть ПУСТО!

# Проверить размер
docker images document-translator:cpu-only
# Должно быть < 1 ГБ
```

## ❓ Почему это работает?

1. **Отказались от `uv`** → используем чистый `pip` с constraints
2. **Блокируем NVIDIA пакеты** через `.pip-constraints.txt`
3. **Явно используем CPU-only версии**:
   - `opencv-python-headless` (не `opencv-python`)
   - `paddlepaddle` с CPU index
   - Environment variables: `CUDA_VISIBLE_DEVICES=""`

## 🚀 Запуск

```bash
docker run -p 8000:8000 document-translator:cpu-only
```

## 📖 Подробности

Смотрите `FIX_NVIDIA_PACKAGES.md` для полной информации.

---

**P.S.** Если всё равно видите NVIDIA пакеты - очистите Docker cache:
```bash
docker builder prune -af
```



