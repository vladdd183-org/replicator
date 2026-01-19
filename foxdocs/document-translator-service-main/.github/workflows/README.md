# CI/CD Workflows

## Workflows Overview

### 1. `build-license-helper.yml` - Сборка License Helper для Windows

**Когда запускается:**
- При push в main, если изменились файлы в `license_helper/`
- Вручную через workflow_dispatch

**Что делает:**
- Собирает Windows EXE файл на GitHub runners
- Обфусцирует код с помощью PyArmor
- Создаёт Release в GitHub с exe файлом

**Результат:**
- Windows exe файл в GitHub Releases

---

### 2. `build-release-package.yml` - Полная сборка релизного пакета

**Когда запускается:**
- При push в main, если изменились основные файлы проекта
- Вручную через workflow_dispatch

**Что делает:**
Состоит из двух job'ов:

**Job 1: `build-windows-exe`** (на GitHub Windows runner)
- Собирает Windows EXE нативно на Windows
- Обфусцирует код с PyArmor
- Компилирует с PyInstaller
- Сохраняет exe как артефакт

**Job 2: `build-and-package`** (на удалённом сервере через SSH)
- Скачивает Windows EXE из артефактов первого job
- Собирает Docker образ сервиса
- Сохраняет Docker образ в tar.gz файл
- Создаёт полный релизный пакет с документацией
- Генерирует скрипты установки для Linux и Windows

**Результат:**
- Релизный пакет в `/root/licenser-server/releases/<дата>/` на удалённом сервере

**Содержимое релизного пакета:**
```
/root/licenser-server/releases/2025-01-15_14-30-00/
├── docker-image-v2025.01.15-abc1234.tar.gz           # Docker образ (сжатый)
├── license-helper-v2025.01.15-abc1234-windows.exe    # License helper (Windows, нативная сборка)
├── docker-compose.yml                                 # Конфигурация для запуска
├── install.sh                                         # Скрипт установки (Linux)
├── install.bat                                        # Скрипт установки (Windows)
├── README.md                                          # Документация
└── release-manifest.json                              # Манифест релиза
```

---

## Настройка GitHub Secrets

Для работы workflows необходимо настроить следующие secrets в GitHub:

### Для `build-release-package.yml`

1. **SSH_HOST** - IP адрес или hostname удалённого сервера
   ```
   Пример: 192.168.1.100 или server.example.com
   ```

2. **SSH_USERNAME** - Имя пользователя для SSH
   ```
   Пример: root или deploy
   ```

3. **SSH_PRIVATE_KEY** - Приватный SSH ключ для подключения
   ```
   Содержимое файла id_rsa или id_ed25519
   ```

4. **SSH_PORT** - Порт SSH (обычно 22)
   ```
   Пример: 22 или 2222
   ```

### Для `build-license-helper.yml`

- **GITHUB_TOKEN** - автоматически предоставляется GitHub (не требует настройки)

---

## Как добавить secrets в GitHub

1. Перейдите в репозиторий на GitHub
2. Settings → Secrets and variables → Actions
3. Нажмите "New repository secret"
4. Введите имя секрета (например, `SSH_HOST`)
5. Введите значение секрета
6. Нажмите "Add secret"
7. Повторите для всех необходимых секретов

---

## Требования к удалённому серверу

Для работы `build-release-package.yml` на сервере должно быть установлено:

- **Git** - для клонирования репозитория
- **Docker** - для сборки образов
- **Достаточно места на диске** - минимум 10 GB свободного места

**Примечание:** Python больше не требуется на сервере! Windows EXE собирается на GitHub Windows runner.

### Установка зависимостей на Ubuntu/Debian

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Git
sudo apt install -y git

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Дополнительные инструменты
sudo apt install -y curl wget
```

### Создание SSH ключа для доступа

```bash
# На своей машине
ssh-keygen -t ed25519 -C "github-actions@your-repo" -f ~/.ssh/github_actions

# Копирование публичного ключа на сервер
ssh-copy-id -i ~/.ssh/github_actions.pub user@server

# Проверка подключения
ssh -i ~/.ssh/github_actions user@server

# Содержимое приватного ключа нужно добавить в GitHub Secret SSH_PRIVATE_KEY
cat ~/.ssh/github_actions
```

---

## Ручной запуск workflows

### Через веб-интерфейс GitHub

1. Перейдите в репозиторий на GitHub
2. Actions → выберите нужный workflow
3. Нажмите "Run workflow"
4. Выберите ветку (обычно main)
5. Нажмите "Run workflow"

### Через GitHub CLI

```bash
# Установка GitHub CLI (если ещё не установлен)
# https://cli.github.com/

# Запуск build-release-package
gh workflow run build-release-package.yml

# Запуск build-license-helper
gh workflow run build-license-helper.yml

# Просмотр статуса
gh run list
```

---

## Доступ к релизам

### На удалённом сервере

```bash
# Подключение к серверу
ssh user@server

# Просмотр всех релизов
ls -la /root/licenser-server/releases/

# Переход в конкретный релиз
cd /root/licenser-server/releases/2025-01-15_14-30-00/

# Просмотр содержимого
ls -lh

# Чтение документации
cat README.md

# Просмотр манифеста
cat release-manifest.json
```

### Скачивание релиза с сервера

```bash
# Скачать весь релиз
scp -r user@server:/root/licenser-server/releases/2025-01-15_14-30-00/ ./

# Скачать только Docker образ
scp user@server:/root/licenser-server/releases/2025-01-15_14-30-00/docker-image-*.tar.gz ./

# Скачать только license-helper
scp user@server:/root/licenser-server/releases/2025-01-15_14-30-00/license-helper-* ./
```

---

## Развёртывание релиза у клиента

### Вариант 1: Автоматическая установка (рекомендуется)

```bash
# 1. Скопировать релиз на машину клиента
scp -r user@server:/root/licenser-server/releases/2025-01-15_14-30-00/ ./

# 2. Перейти в директорию релиза
cd 2025-01-15_14-30-00/

# 3. Запустить скрипт установки
chmod +x install.sh
sudo ./install.sh
```

### Вариант 2: Ручная установка

```bash
# 1. Распаковать Docker образ
gunzip docker-image-*.tar.gz

# 2. Загрузить образ в Docker
docker load -i docker-image-*.tar

# 3. Запустить сервисы
docker-compose up -d

# 4. Проверить статус
docker-compose ps
curl http://localhost:8000/health
```

---

## Мониторинг и логи

### GitHub Actions

```bash
# Просмотр логов через веб-интерфейс
# Actions → выберите run → просмотр логов каждого step

# Или через CLI
gh run list
gh run view <run-id>
gh run view <run-id> --log
```

### На удалённом сервере

```bash
# Проверка свободного места
df -h /root/licenser-server/releases/

# Количество релизов
ls -l /root/licenser-server/releases/ | wc -l

# Общий размер всех релизов
du -sh /root/licenser-server/releases/

# Удаление старых релизов (старше 30 дней)
find /root/licenser-server/releases/ -type d -mtime +30 -exec rm -rf {} \;
```

---

## Troubleshooting

### Проблема: SSH connection timeout

**Решение:**
- Проверьте, что SSH порт открыт в файрволе
- Проверьте правильность SSH_HOST и SSH_PORT
- Проверьте SSH ключ: `ssh -i ~/.ssh/key user@host`

### Проблема: Docker build fails

**Решение:**
- Проверьте место на диске: `df -h`
- Очистите старые образы: `docker system prune -a`
- Проверьте логи: посмотрите в GitHub Actions logs

### Проблема: Permission denied на сервере

**Решение:**
- Убедитесь, что пользователь в группе docker: `sudo usermod -aG docker $USER`
- Проверьте права на `/root/licenser-server/releases/`
- Возможно, нужно запустить от root

### Проблема: PyInstaller fails (Windows job)

**Решение:**
- Проверьте логи в GitHub Actions → build-windows-exe job
- Windows EXE собирается на GitHub runner, не на вашем сервере
- Проверьте файл `license_helper/requirements.txt`
- Проверьте наличие всех зависимостей в workflow

---

## Автоматизация очистки старых релизов

Создайте cron job на сервере для автоматической очистки:

```bash
# Редактировать crontab
sudo crontab -e

# Добавить задачу (запуск каждую неделю, удаление релизов старше 30 дней)
0 2 * * 0 find /root/licenser-server/releases/ -type d -mtime +30 -maxdepth 1 -exec rm -rf {} \;

# Или более безопасный вариант с архивацией
0 2 * * 0 /usr/local/bin/cleanup-old-releases.sh
```

Скрипт `/usr/local/bin/cleanup-old-releases.sh`:

```bash
#!/bin/bash
RELEASES_DIR="/root/licenser-server/releases"
ARCHIVE_DIR="/root/licenser-server/archives"
DAYS_OLD=30

mkdir -p "$ARCHIVE_DIR"

# Найти и заархивировать старые релизы
find "$RELEASES_DIR" -type d -mtime +$DAYS_OLD -maxdepth 1 | while read dir; do
    if [ "$dir" != "$RELEASES_DIR" ]; then
        basename=$(basename "$dir")
        echo "Archiving $basename..."
        tar -czf "$ARCHIVE_DIR/${basename}.tar.gz" -C "$RELEASES_DIR" "$basename"
        rm -rf "$dir"
    fi
done

echo "Cleanup completed: $(date)"
```

---

## Best Practices

1. **Версионирование**
   - Используйте семантическое версионирование
   - Храните changelog для каждого релиза

2. **Безопасность**
   - Регулярно ротируйте SSH ключи
   - Используйте ограниченные права доступа
   - Не храните секреты в коде

3. **Мониторинг**
   - Настройте уведомления о провале workflows
   - Регулярно проверяйте размер релизов
   - Следите за свободным местом на сервере

4. **Документация**
   - Обновляйте README для каждого релиза
   - Документируйте изменения в конфигурации
   - Ведите changelog

5. **Тестирование**
   - Тестируйте релизы перед отправкой клиенту
   - Проверяйте работу на чистой системе (Windows и Linux)
   - Ведите список совместимых систем

6. **Артефакты**
   - Windows EXE временно хранится как артефакт (1 день)
   - Финальный пакет на сервере содержит всё необходимое
   - Используйте `cleanup-old-releases.sh` для управления местом

---

## Контакты и поддержка

При возникновении проблем:
1. Проверьте документацию
2. Посмотрите логи в GitHub Actions
3. Создайте Issue в репозитории
4. Обратитесь к команде разработки
