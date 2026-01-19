# Руководство по релизам и развёртыванию

## 📦 Быстрый старт

### Автоматическая сборка релиза

Релизы собираются автоматически при push в `main` ветку:

```bash
git add .
git commit -m "Release: новая версия"
git push origin main
```

После push:
1. GitHub Actions запустит workflow `build-release-package`
2. **Job 1**: Windows EXE соберётся нативно на GitHub Windows runner
3. **Job 2**: Docker образ соберётся на удалённом сервере
4. Всё объединится и сохранится в `/root/licenser-server/releases/<дата>/`

### Ручной запуск сборки

Через веб-интерфейс GitHub:
1. Перейдите в **Actions**
2. Выберите **Build Release Package**
3. Нажмите **Run workflow** → **Run workflow**

Через командную строку:
```bash
gh workflow run build-release-package.yml
```

---

## 🔍 Просмотр релизов на сервере

```bash
# Список всех релизов
./scripts/list-releases.sh user@server.com

# Список последних 50 релизов
./scripts/list-releases.sh user@server.com 50

# Список всех релизов
./scripts/list-releases.sh user@server.com all
```

---

## ⬇️ Скачивание релиза

```bash
# Скачать последний релиз
./scripts/download-release.sh user@server.com

# Скачать конкретный релиз
./scripts/download-release.sh user@server.com 2025-01-15_14-30-00

# Скачать в определённую директорию
./scripts/download-release.sh user@server.com latest ./my-releases/
```

---

## 🚀 Развёртывание у клиента

### Метод 1: Автоматическая установка (рекомендуется)

```bash
# 1. Скачать релиз
./scripts/download-release.sh user@server.com

# 2. Перейти в директорию релиза
cd <дата-релиза>/

# 3. Запустить установку
chmod +x install.sh
sudo ./install.sh
```

### Метод 2: Ручная установка

```bash
# 1. Распаковать Docker образ
gunzip docker-image-*.tar.gz

# 2. Загрузить в Docker
docker load -i docker-image-*.tar

# 3. Запустить
docker-compose up -d

# 4. Проверить
docker-compose ps
curl http://localhost:8000/health
```

### Метод 3: Передача клиенту без интернета

#### Linux клиент:
```bash
# 1. Скачать релиз на машину с интернетом
./scripts/download-release.sh user@server.com

# 2. Скопировать на флешку/диск
cp -r <дата-релиза> /media/usb/

# 3. На машине клиента (без интернета)
cd /media/usb/<дата-релиза>/
chmod +x install.sh
sudo ./install.sh
```

#### Windows клиент:
```bash
# 1. Скачать релиз на машину с интернетом
./scripts/download-release.sh user@server.com

# 2. Скопировать на флешку
cp -r <дата-релиза> /mnt/d/

# 3. На Windows машине клиента (без интернета)
# - Установите Docker Desktop (если еще не установлен)
# - Запустите Docker Desktop и дождитесь "Engine started"
# - Перейдите в папку с релизом на флешке
# - Дважды кликните load-image.bat (для загрузки образа)
# - Дважды кликните start.bat (для запуска сервиса)
# - Дважды кликните license-helper-*.exe (для запуска License Helper)
```

> **Для Windows пользователей:** В релизе есть подробная инструкция **WINDOWS_SETUP_GUIDE.md**

---

## 🔧 Настройка CI/CD

### Необходимые GitHub Secrets

Добавьте следующие secrets в репозитории:

1. **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Описание | Пример |
|------------|----------|--------|
| `SSH_HOST` | IP или hostname сервера | `192.168.1.100` |
| `SSH_USERNAME` | Имя пользователя | `root` |
| `SSH_PRIVATE_KEY` | Приватный SSH ключ | Содержимое `~/.ssh/id_rsa` |
| `SSH_PORT` | Порт SSH | `22` |

### Создание SSH ключа

```bash
# Генерация ключа
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions

# Копирование на сервер
ssh-copy-id -i ~/.ssh/github_actions.pub user@server

# Содержимое приватного ключа для GitHub Secret
cat ~/.ssh/github_actions
```

---

## 🛠️ Требования к серверу

Убедитесь, что на сервере установлено:

```bash
# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Git
sudo apt install -y git

# Создание директории для релизов
sudo mkdir -p /root/licenser-server/releases
```

**Примечание:** Python больше не требуется! Windows EXE собирается нативно на GitHub Windows runner.

---

## 🧹 Очистка старых релизов

### Ручная очистка

```bash
# Посмотреть что будет удалено (dry run)
ssh user@server "DRY_RUN=true /path/to/cleanup-old-releases.sh"

# Удалить релизы старше 30 дней
ssh user@server "/path/to/cleanup-old-releases.sh"

# Удалить релизы старше 60 дней
ssh user@server "DAYS_OLD=60 /path/to/cleanup-old-releases.sh"
```

### Автоматическая очистка (cron)

На сервере:
```bash
# Скопировать скрипт на сервер
scp scripts/cleanup-old-releases.sh user@server:/usr/local/bin/

# Сделать исполняемым
ssh user@server "chmod +x /usr/local/bin/cleanup-old-releases.sh"

# Настроить cron (каждое воскресенье в 2:00)
ssh user@server "crontab -e"
```

Добавить строку:
```cron
0 2 * * 0 /usr/local/bin/cleanup-old-releases.sh >> /var/log/cleanup-releases.log 2>&1
```

---

## 📋 Структура релиза

Каждый релиз содержит:

```
/mnt/storage/translator/releases/2025-01-15_14-30-00/
├── docker-image-v2025.01.15-abc1234.tar              # Docker образ (~2-3 GB)
├── license-helper-v2025.01.15-abc1234-windows.exe    # License helper для Windows (нативная сборка)
├── docker-compose.yml                                 # Конфигурация для запуска
├── README.md                                          # Инструкции (копия RELEASE_README.md)
├── WINDOWS_SETUP_GUIDE.md                            # Подробное руководство для Windows
├── load-image.bat                                     # Загрузка образа (Windows CMD)
├── load-image.ps1                                     # Загрузка образа (PowerShell)
├── start.bat                                          # Запуск сервиса (Windows CMD)
├── start.ps1                                          # Запуск сервиса (PowerShell)
├── stop.bat                                           # Остановка сервиса (Windows CMD)
└── stop.ps1                                           # Остановка сервиса (PowerShell)
```

---

## 🔍 Мониторинг сборки

### Через веб-интерфейс

1. Перейдите в репозиторий на GitHub
2. **Actions** → выберите последний run
3. Просмотрите логи каждого step

### Через CLI

```bash
# Установка GitHub CLI
sudo apt install gh  # или с https://cli.github.com/

# Авторизация
gh auth login

# Просмотр статуса
gh run list

# Просмотр конкретного run
gh run view <run-id> --log

# Просмотр последнего run
gh run view --log
```

---

## ❗ Troubleshooting

### Проблема: Недостаточно места на сервере

```bash
# Проверить место
ssh user@server "df -h"

# Очистить Docker
ssh user@server "docker system prune -a -f"

# Очистить старые релизы
ssh user@server "/usr/local/bin/cleanup-old-releases.sh"
```

### Проблема: SSH connection timeout в Actions

1. Проверьте файрвол на сервере:
   ```bash
   sudo ufw status
   sudo ufw allow 22/tcp
   ```

2. Проверьте SSH доступ локально:
   ```bash
   ssh -i ~/.ssh/github_actions user@server
   ```

3. Проверьте правильность секретов в GitHub

### Проблема: Docker build fails

```bash
# На сервере проверить логи
docker logs <container-id>

# Проверить Dockerfile локально
docker build -t test .

# Очистить кэш Docker
docker builder prune -a
```

### Проблема: PyInstaller fails (Windows job)

Проверьте в GitHub Actions:
1. Перейдите в **Actions** → последний run
2. Откройте **build-windows-exe** job
3. Проверьте логи шага "Build EXE with PyInstaller"
4. Windows EXE собирается на GitHub runner, не на вашем сервере
5. Проверьте `license_helper/requirements.txt` на наличие несовместимых зависимостей

---

## 📊 Мониторинг использования диска

Создайте скрипт мониторинга:

```bash
#!/bin/bash
# /usr/local/bin/check-releases-disk.sh

RELEASES_DIR="/root/licenser-server/releases"
THRESHOLD=80  # Предупреждение при 80% заполнения

USAGE=$(df -h $RELEASES_DIR | tail -1 | awk '{print $5}' | sed 's/%//')

echo "Disk usage: $USAGE%"

if [ $USAGE -gt $THRESHOLD ]; then
    echo "WARNING: Disk usage above threshold!"
    echo "Oldest 5 releases:"
    ls -lt $RELEASES_DIR | tail -5
fi
```

Добавить в cron:
```cron
0 9 * * * /usr/local/bin/check-releases-disk.sh | mail -s "Releases Disk Report" admin@example.com
```

---

## 🎯 Особенности архитектуры

### Почему два job'а?

1. **Windows EXE на GitHub runner**
   - ✅ Нативная сборка Windows → лучшая совместимость
   - ✅ Не нужен Wine или кросс-компиляция
   - ✅ GitHub предоставляет Windows runner бесплатно
   - ✅ PyInstaller работает стабильнее на нативной платформе

2. **Docker на удалённом сервере**
   - ✅ Экономия GitHub runner времени (Docker сборка долгая)
   - ✅ Хранение релизов на вашем сервере
   - ✅ Не расходуется GitHub storage quota
   - ✅ Полный контроль над релизами

### Передача между job'ами

- Windows EXE передаётся через **GitHub Artifacts**
- Артефакт хранится только 1 день (достаточно для сборки)
- Финальный релиз содержит всё и хранится на сервере

---

## 🔐 Безопасность

### Рекомендации:

1. **SSH ключи**
   - Используйте отдельные ключи для CI/CD
   - Регулярно ротируйте ключи
   - Ограничьте доступ ключей (authorized_keys с командами)

2. **Права доступа**
   ```bash
   # Ограничить доступ к релизам
   chmod 700 /root/licenser-server/releases
   ```

3. **Файрвол**
   ```bash
   # Разрешить только необходимые порты
   sudo ufw default deny incoming
   sudo ufw allow 22/tcp
   sudo ufw allow 8000/tcp  # API
   sudo ufw enable
   ```

4. **Секреты**
   - Никогда не коммитьте секреты в git
   - Используйте GitHub Secrets
   - Регулярно проверяйте логи на утечки

---

## 📚 Дополнительные ресурсы

- [Основной README](README.md)
- [Документация CI/CD](.github/workflows/README.md)
- [License Helper](license_helper/README.md)
- [Архитектура лицензирования](LICENSING_ARCHITECTURE.md)

---

## 📞 Контакты

При возникновении проблем:
1. Проверьте документацию
2. Посмотрите логи в GitHub Actions
3. Создайте [Issue](../../issues)
4. Обратитесь к команде разработки

