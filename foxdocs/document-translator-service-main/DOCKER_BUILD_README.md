# 🐳 Docker Build для Windows EXE

Быстрый старт для сборки Windows EXE файлов через Docker.

---

## 🚀 Быстрый старт

### Linux/macOS (Wine-based)

```bash
# 1. Сделать скрипт исполняемым
chmod +x build-with-docker.sh

# 2. Запустить сборку
./build-with-docker.sh

# 3. Найти результаты
ls -lh release-output/
```

### Windows (Native Container)

```powershell
# 1. Убедиться что Docker в Windows containers режиме
docker version  # Should show "OS/Arch: windows/amd64"

# 2. Запустить сборку
.\build-with-docker.ps1

# 3. Найти результаты
Get-ChildItem release-output
```

---

## 📦 Что создаётся?

После сборки в `release-output/` будут:

```
release-output/
├── license-helper-v2025.11.05-abc1234-windows.exe  (~15 MB)
├── DocumentTranslator-v2025.11.05-abc1234.exe      (~350 MB)
├── README.md
├── WINDOWS_SETUP_GUIDE.md
├── docker-compose.yml
├── *.bat (Windows скрипты)
└── *.ps1 (PowerShell скрипты)
```

---

## 🎯 Два подхода

| Подход | Файл | Требует | Для чего |
|--------|------|---------|----------|
| **Wine** | `Dockerfile.windows-builder-wine` | Linux хост | CI/CD, production |
| **Native** | `Dockerfile.windows-native` | Windows Server | Максимальная совместимость |

**Рекомендация:** Используйте **Wine-based** для CI/CD (дешевле, универсальнее).

---

## 🔧 Ручная сборка

### Wine-based (подробно)

```bash
# 1. Сборка Docker образа
docker build \
  --build-arg VERSION="2025.11.05" \
  --build-arg SHA_SHORT="$(git rev-parse --short HEAD)" \
  -f Dockerfile.windows-builder-wine \
  -t doc-translator-builder:latest \
  .

# 2. Извлечение файлов из образа
mkdir -p release-output
CONTAINER_ID=$(docker create doc-translator-builder:latest)
docker cp "${CONTAINER_ID}:/release/." ./release-output/
docker rm "${CONTAINER_ID}"

# 3. Проверка результатов
ls -lh release-output/
```

### Native Windows (подробно)

```powershell
# 1. Переключить Docker в Windows режим
& "C:\Program Files\Docker\Docker\DockerCli.exe" -SwitchDaemon

# 2. Сборка Docker образа
docker build `
  --build-arg VERSION="2025.11.05" `
  --build-arg SHA_SHORT=$(git rev-parse --short HEAD) `
  -f Dockerfile.windows-native `
  -t doc-translator-builder:latest `
  .

# 3. Извлечение файлов через volume
New-Item -ItemType Directory -Force -Path release-output
docker run --rm `
  -v "${PWD}\release-output:C:\output" `
  doc-translator-builder:latest

# 4. Проверка результатов
Get-ChildItem release-output
```

---

## ⚙️ Переменные сборки

Можно кастомизировать через `--build-arg`:

```bash
docker build \
  --build-arg VERSION="1.2.3" \
  --build-arg SHA_SHORT="custom" \
  ...
```

**Доступные аргументы:**
- `VERSION` - версия (формат: YYYY.MM.DD)
- `SHA_SHORT` - короткий SHA коммита

---

## 🐛 Troubleshooting

### Проблема: Wine не может установить Python

```bash
# Решение: Используйте xvfb для GUI
docker build --no-cache ...
```

### Проблема: Docker занимает много места

```bash
# Очистка после сборки
docker system prune -a -f

# Удаление образа
docker rmi doc-translator-builder:latest
```

### Проблема: Windows container не работает

```powershell
# Проверка режима Docker
docker info | Select-String "OSType"

# Должно быть: OSType: windows
# Если linux - переключите в Docker Desktop Settings
```

### Проблема: Медленная сборка

```bash
# Используйте BuildKit для кеширования
export DOCKER_BUILDKIT=1
docker build ...
```

---

## 📚 Документация

- **[DOCKER_BUILD_GUIDE.md](./DOCKER_BUILD_GUIDE.md)** - Полное руководство по обоим подходам
- **[DOCKER_VS_GITHUB_ACTIONS.md](./DOCKER_VS_GITHUB_ACTIONS.md)** - Сравнение с GitHub Actions workflow
- **[.github/workflows/build-release-package-docker.yml](./.github/workflows/build-release-package-docker.yml)** - Пример CI/CD с Docker

---

## 💡 Примеры использования

### В CI/CD (GitLab)

```yaml
build:
  image: docker:latest
  services:
    - docker:dind
  script:
    - ./build-with-docker.sh
  artifacts:
    paths:
      - release-output/
```

### В CI/CD (Jenkins)

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh './build-with-docker.sh'
            }
        }
    }
}
```

### Локальная разработка

```bash
# Быстрая сборка для тестирования
./build-with-docker.sh

# Протестировать EXE в Wine
cd release-output
wine license-helper-*.exe --help
```

---

## ✅ Что дальше?

1. **Протестируйте локально:**
   ```bash
   ./build-with-docker.sh
   ```

2. **Проверьте EXE на Windows машине**

3. **Интегрируйте в ваш CI/CD** (см. примеры выше)

4. **Сравните с GitHub Actions** (см. DOCKER_VS_GITHUB_ACTIONS.md)

---

## 🆘 Помощь

**Если что-то не работает:**

1. Проверьте Docker установлен: `docker --version`
2. Проверьте права: `docker ps` должен работать без sudo
3. Очистите кеш: `docker system prune -a`
4. Пересоберите с нуля: `docker build --no-cache ...`
5. Откройте issue в репозитории

---

**Готово!** 🎉

Теперь вы можете собирать Windows EXE на любой платформе с Docker.

