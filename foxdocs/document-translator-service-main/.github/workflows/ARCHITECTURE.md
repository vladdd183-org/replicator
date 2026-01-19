# Архитектура CI/CD для релизов

## 🎯 Общая схема

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GitHub Actions Workflow                      │
│                     build-release-package.yml                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
        ┌───────────────────────┐     ┌──────────────────────────┐
        │   JOB 1: Windows EXE  │     │  JOB 2: Docker + Package │
        │  GitHub Windows Runner│     │   Удалённый сервер (SSH) │
        └───────────────────────┘     └──────────────────────────┘
                    │                             │
                    │                             │
            1. Checkout code              1. Checkout code
            2. Setup Python 3.11          2. Download EXE artifact
            3. PyArmor obfuscation        3. Copy files to server
            4. PyInstaller build          4. Build Docker image
            5. Upload artifact            5. Save Docker as tar.gz
                    │                     6. Create release package
                    │                             │
                    ▼                             ▼
        ┌───────────────────────┐     ┌──────────────────────────┐
        │  GitHub Artifacts     │────▶│  Server: /root/licenser- │
        │  (хранится 1 день)    │     │  server/releases/<дата>/ │
        └───────────────────────┘     └──────────────────────────┘
```

---

## 📦 Компоненты релиза

### 1. Windows EXE (license-helper)

**Где собирается:** GitHub Windows runner  
**Как:** PyArmor → PyInstaller  
**Размер:** ~50-100 MB  
**Формат:** `license-helper-v2025.01.15-abc1234-windows.exe`

**Почему нативная сборка?**
- ✅ Лучшая совместимость с Windows
- ✅ PyInstaller работает стабильнее на целевой платформе
- ✅ Не нужен Wine или кросс-компиляция
- ✅ GitHub предоставляет Windows runner бесплатно

### 2. Docker Image

**Где собирается:** Удалённый сервер через SSH  
**Как:** Docker build → docker save → gzip  
**Размер:** ~2-3 GB (сжатый)  
**Формат:** `docker-image-v2025.01.15-abc1234.tar.gz`

**Почему на сервере?**
- ✅ Экономия GitHub runner minutes (Docker сборка долгая)
- ✅ Не расходуется GitHub storage quota
- ✅ Прямое хранение релизов на сервере
- ✅ Полный контроль над релизами

### 3. Дополнительные файлы

Генерируются автоматически на сервере:
- `docker-compose.yml` - конфигурация для запуска
- `install.sh` - скрипт установки для Linux
- `install.bat` - скрипт установки для Windows
- `README.md` - инструкции для клиента
- `release-manifest.json` - метаданные релиза

---

## 🔄 Процесс сборки

### Шаг 1: Trigger (запуск)

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
```

**Запускается при:**
- Push в main (изменения в src/, license_helper/, Dockerfile и т.д.)
- Ручной запуск через GitHub UI

### Шаг 2: Job 1 - Windows EXE

```
1. Checkout репозитория
2. Setup Python 3.11 на Windows runner
3. Установка зависимостей (pyarmor, pyinstaller)
4. Обфускация кода PyArmor
5. Сборка exe с PyInstaller
6. Генерация версии (v2025.01.15-abc1234)
7. Upload в GitHub Artifacts
```

**Время выполнения:** ~5-7 минут

### Шаг 3: Job 2 - Docker + Packaging

```
1. Checkout репозитория
2. Download Windows EXE из artifacts
3. Copy всех файлов на сервер через SCP
4. SSH подключение к серверу:
   - Клонирование репо (для Dockerfile)
   - Docker build
   - Docker save + gzip
   - Копирование Windows EXE в релиз
   - Генерация конфигов и скриптов
   - Создание манифеста
   - Очистка временных файлов
```

**Время выполнения:** ~15-30 минут (зависит от Docker cache)

### Шаг 4: Финализация

Релиз готов в `/root/licenser-server/releases/<дата>/`

---

## 🔐 Безопасность

### GitHub Secrets

```
SSH_HOST         - IP/hostname сервера
SSH_USERNAME     - Имя пользователя
SSH_PRIVATE_KEY  - Приватный SSH ключ
SSH_PORT         - Порт SSH (обычно 22)
```

### Обфускация кода

- Windows EXE обфусцируется PyArmor перед компиляцией
- Затрудняет reverse engineering
- Защищает интеллектуальную собственность

### Права доступа

- SSH ключ используется только для CI/CD
- Рекомендуется отдельный пользователь с ограниченными правами
- Файлы релизов доступны только авторизованным пользователям

---

## 📊 Использование ресурсов

### GitHub

| Ресурс | Использование |
|--------|---------------|
| Runner minutes (Windows) | ~5-7 мин/сборка |
| Runner minutes (Linux) | ~1-2 мин/сборка |
| Artifacts storage | Временно (~100 MB × 1 день) |
| Total per release | ~8-10 минут |

**Лимиты Free tier:** 2000 минут/месяц → ~200 сборок/месяц

### Сервер

| Ресурс | Использование |
|--------|---------------|
| CPU | Высокое во время Docker build |
| RAM | 4-8 GB рекомендуется |
| Disk | ~3-4 GB на релиз |
| Network | ~100-200 MB трафик (upload) |

**Рекомендации:**
- Минимум 50 GB свободного места
- Автоматическая очистка старых релизов (30 дней)
- Регулярный `docker system prune`

---

## 🚀 Оптимизация

### Ускорение Docker build

```dockerfile
# Используем Docker cache
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### Параллелизация

Jobs выполняются последовательно (Windows EXE → Docker), так как есть зависимость. Но внутри job'ов можно распараллелить:

```yaml
- name: Install dependencies
  run: |
    pip install -r requirements.txt &
    npm install &
    wait
```

### Условный запуск

Можно добавить условия для пропуска сборки:

```yaml
if: "!contains(github.event.head_commit.message, '[skip ci]')"
```

---

## 🔧 Расширение

### Добавление других платформ

Можно добавить параллельные job'ы для других платформ:

```yaml
jobs:
  build-windows-exe:
    runs-on: windows-latest
  
  build-linux-binary:
    runs-on: ubuntu-latest
  
  build-macos-binary:
    runs-on: macos-latest
  
  package-release:
    needs: [build-windows-exe, build-linux-binary, build-macos-binary]
```

### Тестирование релиза

Можно добавить job для автоматического тестирования:

```yaml
  test-release:
    needs: build-and-package
    runs-on: ubuntu-latest
    steps:
      - name: Download release from server
      - name: Test Docker image
      - name: Test installation script
```

### Deployment

Можно добавить автоматический deploy на staging:

```yaml
  deploy-staging:
    needs: test-release
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to staging environment
```

---

## 📈 Мониторинг

### Метрики для отслеживания

1. **Время сборки**
   - Job 1 (Windows): норма 5-7 мин
   - Job 2 (Docker): норма 15-30 мин

2. **Размер релизов**
   - Docker image: ~2-3 GB
   - Windows EXE: ~50-100 MB
   - Total: ~3-4 GB

3. **Успешность сборок**
   - Target: >95% успешных сборок
   - Алерты при провалах

4. **Использование диска на сервере**
   - Мониторинг свободного места
   - Автоочистка при <20% свободного

### Dashboard

Можно использовать GitHub Actions dashboard или настроить:
- Grafana для метрик сервера
- Datadog/New Relic для CI/CD метрик
- Custom Slack/Telegram уведомления

---

## 🐛 Типичные проблемы

### 1. Windows EXE не работает на клиенте

**Причины:**
- Антивирус блокирует
- Несовместимая версия Windows
- Отсутствуют системные библиотеки

**Решение:**
- Добавить exe в исключения антивируса
- Проверить минимальную версию Windows (7+)
- Включить все зависимости в PyInstaller

### 2. Docker build fails

**Причины:**
- Недостаточно места на диске
- Проблемы с сетью (download packages)
- Изменения в Dockerfile

**Решение:**
- `docker system prune -a`
- Проверить connectivity к package repositories
- Локальное тестирование Dockerfile

### 3. SSH connection timeout

**Причины:**
- Firewall блокирует
- Неправильный SSH ключ
- Сервер недоступен

**Решение:**
- Проверить firewall rules
- Проверить SSH ключ локально
- Мониторинг uptime сервера

---

## 📚 Связанные документы

- [README по workflows](.github/workflows/README.md)
- [Руководство по релизам](../RELEASE_GUIDE.md)
- [Руководство по настройке](.github/SETUP_GUIDE.md)
- [Архитектура лицензирования](../LICENSING_ARCHITECTURE.md)

---

## 🔄 История изменений

### v2.0 (текущая)
- ✅ Нативная сборка Windows EXE на GitHub runner
- ✅ Два отдельных job'а (Windows + Docker)
- ✅ Передача через GitHub Artifacts
- ✅ Поддержка Windows и Linux клиентов

### v1.0 (устаревшая)
- ❌ Сборка exe на Linux через PyInstaller
- ❌ Все в одном job на сервере
- ❌ Проблемы с совместимостью exe

