# Docker Build Guide - Сборка Windows EXE через Docker

Этот гайд описывает два подхода к сборке Windows EXE файлов через Docker, которые повторяют функциональность GitHub Actions workflow (`build-release-package.yml`).

## 📋 Содержание

- [Обзор подходов](#обзор-подходов)
- [Вариант 1: Wine-based (Linux + Wine)](#вариант-1-wine-based-linux--wine)
- [Вариант 2: Native Windows Container](#вариант-2-native-windows-container)
- [Сравнение подходов](#сравнение-подходов)
- [Интеграция с CI/CD](#интеграция-с-cicd)

---

## 🎯 Обзор подходов

### Что делает GitHub Actions workflow?

1. **Job 1**: Сборка `license-helper.exe` на Windows runner
   - Обфускация с PyArmor
   - Компиляция с PyInstaller
   - Загрузка на сервер через SSH

2. **Job 2**: Сборка `DocumentTranslator.exe` на Windows runner
   - Установка зависимостей через UV
   - ONEFILE сборка с PyInstaller
   - Загрузка на сервер через SSH

3. **Job 3**: Создание релизного пакета на Linux runner
   - Сборка Docker образа (опционально, сейчас отключено)
   - Упаковка всех файлов в release директорию

### Два Docker подхода

| Файл | Описание | Требования |
|------|----------|------------|
| `Dockerfile.windows-builder-wine` | Linux + Wine + Windows Python | Любой Linux хост с Docker |
| `Dockerfile.windows-native` | Native Windows Container | Windows Server 2019+ с Docker |

---

## 🍷 Вариант 1: Wine-based (Linux + Wine)

### Преимущества

✅ **Работает на любом Linux хосте** (включая GitHub Actions Ubuntu runners)  
✅ **Не требует Windows Server**  
✅ **Дешевле в облаке** (Linux дешевле Windows)  
✅ **Быстрее запускается** (меньше размер образов)

### Недостатки

⚠️ **Возможны проблемы совместимости** с некоторыми Windows-специфичными библиотеками  
⚠️ **Wine не идеально эмулирует Windows** (могут быть edge cases)  
⚠️ **Медленнее сборка** (Wine добавляет overhead)

### Использование

#### Linux/macOS:

```bash
# Сделать скрипт исполняемым
chmod +x build-with-docker.sh

# Запустить сборку
./build-with-docker.sh
```

#### Ручная сборка:

```bash
# Сборка образа
docker build \
  --build-arg VERSION="2025.11.05" \
  --build-arg SHA_SHORT="abc1234" \
  -f Dockerfile.windows-builder-wine \
  -t document-translator-builder:wine \
  .

# Извлечение файлов
mkdir -p release-output
CONTAINER_ID=$(docker create document-translator-builder:wine)
docker cp "${CONTAINER_ID}:/release/." ./release-output/
docker rm "${CONTAINER_ID}"
```

### Структура Dockerfile

```dockerfile
# Stage 1: License Helper (с PyArmor)
FROM ubuntu:22.04 AS license-helper-builder
# - Установка Wine
# - Установка Windows Python через Wine
# - PyArmor обфускация
# - PyInstaller сборка

# Stage 2: DocumentTranslator
FROM ubuntu:22.04 AS document-translator-builder
# - Установка Wine
# - Установка Windows Python через Wine
# - UV/pip установка зависимостей
# - PyInstaller ONEFILE сборка

# Stage 3: Package
FROM alpine:latest AS packager
# - Сборка всех файлов
# - Переименование с версией
# - Создание архива
```

---

## 🪟 Вариант 2: Native Windows Container

### Преимущества

✅ **100% нативная Windows среда**  
✅ **Полная совместимость** с Windows библиотеками  
✅ **Быстрая сборка** (нет overhead от эмуляции)

### Недостатки

⚠️ **Требует Windows Server хост** (Windows Server 2019+)  
⚠️ **Дороже в облаке** (Windows лицензии)  
⚠️ **Больше размер образов** (Windows base images > 4GB)  
⚠️ **Не работает на Linux/macOS Docker**

### Требования

- Windows Server 2019 или новее
- Docker Desktop for Windows в режиме **Windows containers**
- Лицензия Windows Server (если в облаке)

### Переключение Docker в режим Windows containers

```powershell
# В Docker Desktop: Settings -> General -> Use Windows containers

# Или через командную строку
& "C:\Program Files\Docker\Docker\DockerCli.exe" -SwitchDaemon
```

### Использование

#### Windows (PowerShell):

```powershell
# Запустить сборку
.\build-with-docker.ps1
```

#### Ручная сборка:

```powershell
# Сборка образа
docker build `
  --build-arg VERSION="2025.11.05" `
  --build-arg SHA_SHORT="abc1234" `
  -f Dockerfile.windows-native `
  -t document-translator-builder:windows `
  .

# Извлечение файлов
New-Item -ItemType Directory -Force -Path release-output
docker run --rm `
  -v "${PWD}\release-output:C:\output" `
  document-translator-builder:windows
```

### Структура Dockerfile

```dockerfile
# Stage 1: Base (Windows + Python)
FROM mcr.microsoft.com/windows/servercore:ltsc2022 AS base
# - Установка Chocolatey
# - Установка Python 3.11

# Stage 2: License Helper
FROM base AS license-helper-builder
# - PyArmor обфускация
# - PyInstaller сборка

# Stage 3: DocumentTranslator
FROM base AS document-translator-builder
# - UV/pip установка зависимостей
# - PyInstaller ONEFILE сборка

# Stage 4: Package
FROM mcr.microsoft.com/windows/nanoserver:ltsc2022 AS packager
# - Сборка всех файлов
# - Переименование с версией
```

---

## ⚖️ Сравнение подходов

| Параметр | Wine-based | Native Windows |
|----------|------------|----------------|
| **Хост** | Любой Linux | Windows Server 2019+ |
| **Размер образа** | ~2-3 GB | ~6-8 GB |
| **Время сборки** | 15-25 минут | 10-15 минут |
| **Совместимость** | 95% (могут быть edge cases) | 100% (полностью нативно) |
| **Цена в облаке** | Дешево (Linux VM) | Дорого (Windows Server) |
| **GitHub Actions** | ✅ Ubuntu runners | ❌ Требует self-hosted |
| **Сложность настройки** | Низкая | Средняя |

### Рекомендации

**Используйте Wine-based если:**
- У вас Linux хост или облачная CI/CD
- Бюджет ограничен
- Нужна максимальная совместимость с разными CI/CD системами
- Ваш код не использует глубоко Windows-специфичные API

**Используйте Native Windows если:**
- У вас есть Windows Server хост
- Нужна 100% гарантия совместимости
- Используются сложные Windows-библиотеки (например, COM, WMI)
- Скорость сборки критична

---

## 🚀 Интеграция с CI/CD

### GitHub Actions (Wine-based)

Можно заменить Windows runners на Ubuntu с Docker:

```yaml
jobs:
  build-windows-exe:
    runs-on: ubuntu-latest  # Вместо windows-latest!
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Build with Docker
        run: |
          docker build \
            --build-arg VERSION="${{ steps.version.outputs.VERSION }}" \
            --build-arg SHA_SHORT="${{ steps.version.outputs.SHA_SHORT }}" \
            -f Dockerfile.windows-builder-wine \
            -t builder:latest \
            .
          
          mkdir -p release-output
          CONTAINER_ID=$(docker create builder:latest)
          docker cp "${CONTAINER_ID}:/release/." ./release-output/
          docker rm "${CONTAINER_ID}"
      
      - name: Upload to server
        # ... ваш SSH upload
```

### GitLab CI (Wine-based)

```yaml
build:windows-exe:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -f Dockerfile.windows-builder-wine -t builder .
    - docker create --name extract builder
    - docker cp extract:/release ./release-output
    - docker rm extract
  artifacts:
    paths:
      - release-output/
```

### Jenkins (Native Windows)

```groovy
pipeline {
    agent { label 'windows-docker' }
    
    stages {
        stage('Build') {
            steps {
                powershell '''
                    docker build `
                        -f Dockerfile.windows-native `
                        -t builder:latest `
                        .
                    
                    docker run --rm `
                        -v "${PWD}\\release-output:C:\\output" `
                        builder:latest
                '''
            }
        }
    }
}
```

---

## 🔧 Troubleshooting

### Wine-based

**Проблема:** `wine: could not load kernel32.dll`
```bash
# Переустановите Wine и зависимости
apt-get update
apt-get install --reinstall wine64 wine32
```

**Проблема:** Python не устанавливается в Wine
```bash
# Используйте xvfb для GUI установщика
xvfb-run wine python-installer.exe /quiet InstallAllUsers=1
```

**Проблема:** PyInstaller не находит модули
```bash
# Добавьте больше --hidden-import
pyinstaller --hidden-import <module> ...
```

### Native Windows

**Проблема:** `image operating system "linux" cannot be used`
```powershell
# Переключите Docker в Windows containers режим
& "C:\Program Files\Docker\Docker\DockerCli.exe" -SwitchDaemon
```

**Проблема:** `no matching manifest for linux/amd64`
```powershell
# Убедитесь что используете Windows base images
FROM mcr.microsoft.com/windows/servercore:ltsc2022
```

---

## 📝 Заключение

Оба подхода позволяют собирать Windows EXE файлы через Docker, повторяя функциональность вашего GitHub Actions workflow.

- **Wine-based** - универсальное решение для большинства случаев
- **Native Windows** - для максимальной совместимости при наличии Windows Server

Выбирайте подход в зависимости от вашей инфраструктуры и требований!

