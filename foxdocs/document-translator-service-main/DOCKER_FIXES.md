# 🔧 Исправления Docker Build

## Проблема

При сборке Docker образа возникала ошибка:

```
wine: cannot find L"C:\\Python311\\Scripts\\pip.exe"
it looks like wine32 is missing, you should install it
```

**Причина:** Python не установился корректно в Wine из-за отсутствия wine32 и неправильной последовательности инициализации.

---

## ✅ Исправления

### 1. Добавлен wine32 и multiarch

**Было:**
```dockerfile
RUN apt-get update && apt-get install -y \
    wine64 \
    wget \
    cabextract \
    xvfb \
    && rm -rf /var/lib/apt/lists/*
```

**Стало:**
```dockerfile
RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get install -y \
    wine64 \
    wine32 \
    wget \
    cabextract \
    xvfb \
    winetricks \
    && rm -rf /var/lib/apt/lists/*
```

**Почему:** Wine требует как 64-битные, так и 32-битные библиотеки для корректной работы.

---

### 2. Добавлена инициализация Wine

**Добавлено:**
```dockerfile
# Инициализация Wine
RUN xvfb-run wineboot -i && \
    wineserver -w
```

**Почему:** Wine должен создать окружение перед установкой программ.

---

### 3. Улучшена установка Python

**Было:**
```dockerfile
RUN xvfb-run wine python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 || true && \
    sleep 10
```

**Стало:**
```dockerfile
# Устанавливаем Python в Wine (более надежно)
RUN xvfb-run wine python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 && \
    wineserver -w && \
    sleep 5

# Проверка что Python установился
RUN wine "C:\\Python311\\python.exe" --version || \
    (echo "ERROR: Python installation failed!" && exit 1)
```

**Изменения:**
- ❌ Убрали `|| true` - теперь сборка упадет если Python не установился
- ✅ Добавили `wineserver -w` - ждем завершения всех процессов Wine
- ✅ Добавили проверку установки - явная ошибка если что-то не так

---

## 📂 Новые файлы

### 1. `Dockerfile.windows-builder-wine` (исправленный)

Полная версия с двумя stages:
- Stage 1: license-helper (с PyArmor)
- Stage 2: DocumentTranslator
- Stage 3: Packaging

### 2. `Dockerfile.windows-builder-simple` (новый, рекомендуется)

Упрощенная версия - только DocumentTranslator:
- Быстрее сборка (~15 минут вместо ~25)
- Меньше размер образа
- Проще отладка

---

## 🚀 Как использовать

### Быстрый способ (рекомендуется)

```bash
# Сборка упрощенной версии (только DocumentTranslator)
./build-with-docker.sh
```

Скрипт автоматически использует `Dockerfile.windows-builder-simple`.

### Ручная сборка

```bash
# Упрощенная версия (быстро)
docker build \
  --build-arg VERSION="2025.11.05" \
  --build-arg SHA_SHORT="$(git rev-parse --short HEAD)" \
  -f Dockerfile.windows-builder-simple \
  -t builder:simple \
  .

# Полная версия (license-helper + DocumentTranslator)
docker build \
  --build-arg VERSION="2025.11.05" \
  --build-arg SHA_SHORT="$(git rev-parse --short HEAD)" \
  -f Dockerfile.windows-builder-wine \
  -t builder:full \
  .
```

---

## 🧪 Тестирование исправлений

### 1. Проверка что сборка запускается

```bash
# Должна начаться сборка без ошибок о wine32
docker build --no-cache -f Dockerfile.windows-builder-simple -t test .
```

### 2. Проверка что Python установился

```bash
# В процессе сборки должно быть:
# ✓ Python 3.11.9
# (без ошибок "cannot find pip.exe")
```

### 3. Проверка результата

```bash
# После сборки извлекаем файлы
mkdir -p test-output
CONTAINER_ID=$(docker create test)
docker cp "${CONTAINER_ID}:/release/." ./test-output/
docker rm "${CONTAINER_ID}"

# Проверяем EXE
ls -lh test-output/*.exe
# Должен быть файл ~350-450 MB
```

---

## 📊 Сравнение версий

| Параметр | Simple | Full (Wine) |
|----------|--------|-------------|
| **Stages** | 2 | 3 |
| **Собирает** | DocumentTranslator | license-helper + DocumentTranslator |
| **Время сборки** | ~15 минут | ~25 минут |
| **Размер образа** | ~3 GB | ~5 GB |
| **Сложность** | Низкая | Средняя |
| **Рекомендуется для** | Production | Полный release пакет |

---

## 🐛 Troubleshooting

### Проблема: Wine все еще не находит pip.exe

```bash
# Очистить Docker кеш полностью
docker system prune -a -f

# Пересобрать без кеша
docker build --no-cache -f Dockerfile.windows-builder-simple .
```

### Проблема: Python установка зависает

```bash
# Увеличить sleep после установки Python
# В Dockerfile изменить: sleep 5 -> sleep 15
```

### Проблема: Не хватает места на диске

```bash
# Очистить Docker
docker system prune -a --volumes -f

# Проверить доступное место
df -h
```

### Проблема: Медленная сборка

```bash
# Включить BuildKit
export DOCKER_BUILDKIT=1
docker build ...

# Использовать простую версию вместо полной
docker build -f Dockerfile.windows-builder-simple ...
```

---

## ✅ Checklist перед сборкой

- [ ] Docker установлен и работает
- [ ] Доступно минимум 10 GB свободного места
- [ ] Есть интернет (скачивается Python installer ~30 MB)
- [ ] Файл `run.py` существует в корне проекта
- [ ] Папка `src/` существует и содержит код

---

## 🎯 Следующие шаги

1. **Протестируйте локально:**
   ```bash
   ./build-with-docker.sh
   ```

2. **Проверьте результат:**
   ```bash
   ls -lh release-output/
   wine release-output/DocumentTranslator-*.exe --version
   ```

3. **Интегрируйте в CI/CD** (опционально):
   - См. `.github/workflows/build-release-package-docker.yml`

---

## 📝 Что изменилось в workflow

Если вы используете GitHub Actions:

1. **Замените** `.github/workflows/build-release-package.yml`
2. **На** `.github/workflows/build-release-package-docker.yml`

Это даст:
- 💰 Экономию ~50% минут (Ubuntu вместо Windows)
- ⚡ Быстрее сборку (один job вместо двух)
- 🐧 Возможность запуска на любом Linux CI/CD

---

**Готово!** Теперь Docker сборка должна работать без ошибок. 🎉

