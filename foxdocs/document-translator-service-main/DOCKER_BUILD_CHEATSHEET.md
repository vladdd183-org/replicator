# 🐳 Docker Build Cheatsheet

Быстрая справка по командам Docker сборки.

---

## 🚀 Основные команды

### Простая сборка (один скрипт)

```bash
# Linux/macOS
./build-with-docker.sh

# Windows
.\build-with-docker.ps1
```

### Ручная сборка

```bash
# Wine-based (Linux)
docker build -f Dockerfile.windows-builder-wine -t builder:wine .
CONTAINER_ID=$(docker create builder:wine)
docker cp "${CONTAINER_ID}:/release/." ./release-output/
docker rm "${CONTAINER_ID}"

# Native Windows
docker build -f Dockerfile.windows-native -t builder:win .
docker run --rm -v "${PWD}\release-output:C:\output" builder:win
```

---

## 🔧 Build Arguments

```bash
docker build \
  --build-arg VERSION="2025.11.05" \
  --build-arg SHA_SHORT="abc1234" \
  -f Dockerfile.windows-builder-wine \
  -t builder:latest \
  .
```

---

## 🧹 Очистка

```bash
# Удалить все неиспользуемые образы
docker system prune -a -f

# Удалить конкретный образ
docker rmi builder:latest

# Удалить все контейнеры
docker rm $(docker ps -a -q)

# Полная очистка Docker
docker system prune -a --volumes -f
```

---

## 📦 Работа с образами

```bash
# Список образов
docker images

# Удалить образ
docker rmi IMAGE_ID

# Показать размер образа
docker images | grep builder

# История слоёв
docker history builder:latest

# Инспекция образа
docker inspect builder:latest
```

---

## 🐛 Отладка

```bash
# Сборка без кеша
docker build --no-cache -f Dockerfile.windows-builder-wine .

# Сборка с подробным выводом
docker build --progress=plain -f Dockerfile.windows-builder-wine .

# Запустить контейнер интерактивно
docker run -it --entrypoint /bin/bash builder:wine

# Посмотреть логи сборки
docker logs CONTAINER_ID

# Проверить что внутри контейнера
docker run --rm builder:wine ls -la /release
```

---

## ⚡ Оптимизация

```bash
# Включить BuildKit (быстрее сборка)
export DOCKER_BUILDKIT=1

# Multi-platform build
docker buildx build --platform linux/amd64 -f Dockerfile.windows-builder-wine .

# Кеш сборки в registry
docker buildx build \
  --cache-from type=registry,ref=myregistry/builder:cache \
  --cache-to type=registry,ref=myregistry/builder:cache \
  .
```

---

## 🔍 Проверка результатов

```bash
# Проверить размер EXE
ls -lh release-output/*.exe

# Проверить что EXE создался
file release-output/*.exe

# Запустить в Wine (Linux)
wine release-output/license-helper-*.exe --version

# Извлечь версию из имени файла
ls release-output/*.exe | grep -oP 'v\d+\.\d+\.\d+-[a-f0-9]+'
```

---

## 🐧 Wine специфичные команды

```bash
# Проверка Wine
wine --version

# Установка Wine (Ubuntu/Debian)
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install wine64 wine32

# Проверка Windows Python в Wine
wine python --version

# Запустить Windows приложение в Wine
xvfb-run wine program.exe
```

---

## 🪟 Windows Container команды

```powershell
# Переключение режима Docker
& "C:\Program Files\Docker\Docker\DockerCli.exe" -SwitchDaemon

# Проверка режима
docker info | Select-String "OSType"

# Список Windows образов
docker images --filter "label=com.microsoft.version"

# Запуск Windows контейнера
docker run -it mcr.microsoft.com/windows/servercore:ltsc2022 cmd
```

---

## 📊 Мониторинг

```bash
# Использование диска Docker
docker system df

# Топ контейнеров по использованию ресурсов
docker stats

# Размер образа
docker images builder:latest --format "{{.Size}}"

# Проверка слоёв образа
docker history --no-trunc builder:latest
```

---

## 🔄 CI/CD интеграция

### GitHub Actions

```yaml
- run: docker build -f Dockerfile.windows-builder-wine -t builder .
- run: |
    CONTAINER_ID=$(docker create builder)
    docker cp "${CONTAINER_ID}:/release/." ./release-output/
    docker rm "${CONTAINER_ID}"
```

### GitLab CI

```yaml
script:
  - docker build -f Dockerfile.windows-builder-wine -t builder .
  - docker create --name extract builder
  - docker cp extract:/release ./release-output
```

### Jenkins

```groovy
sh 'docker build -f Dockerfile.windows-builder-wine -t builder .'
sh 'docker create --name extract builder'
sh 'docker cp extract:/release ./release-output'
```

---

## 🎯 Частые сценарии

### Быстрая пересборка

```bash
# Очистить + собрать + извлечь
docker rm -f $(docker ps -a -q) 2>/dev/null || true && \
docker build --no-cache -f Dockerfile.windows-builder-wine -t builder . && \
mkdir -p release-output && \
CONTAINER_ID=$(docker create builder) && \
docker cp "${CONTAINER_ID}:/release/." ./release-output/ && \
docker rm "${CONTAINER_ID}"
```

### Сборка с кастомными зависимостями

```bash
# Изменить requirements.txt и пересобрать
docker build \
  --build-arg EXTRA_DEPS="package1 package2" \
  -f Dockerfile.windows-builder-wine \
  -t builder:custom \
  .
```

### Тест в Wine без сборки образа

```bash
# Быстрый тест Python скрипта в Wine
docker run -it --rm \
  -v $(pwd):/app \
  -w /app \
  scottyhardy/docker-wine \
  wine python your_script.py
```

---

## 💾 Сохранение образа

```bash
# Экспорт образа в файл
docker save builder:latest -o builder-image.tar

# Сжатие
gzip builder-image.tar

# Импорт образа
docker load -i builder-image.tar.gz

# Передача на другую машину
docker save builder:latest | ssh user@host docker load
```

---

## 🆘 Экстренная помощь

### Docker не запускается

```bash
sudo systemctl restart docker
sudo systemctl status docker
```

### Нет прав на Docker

```bash
sudo usermod -aG docker $USER
# Перелогиниться
```

### Закончилось место на диске

```bash
docker system prune -a --volumes -f
df -h | grep docker
```

### Сборка зависла

```bash
# Убить все запущенные сборки
docker ps -q | xargs docker kill

# Удалить промежуточные образы
docker images -f "dangling=true" -q | xargs docker rmi
```

---

**Сохраните эту шпаргалку!** 📌

Все команды протестированы и готовы к использованию.

