# Руководство по настройке CI/CD

## 🎯 Цель

Этот гайд поможет настроить автоматическую сборку релизов на вашем удалённом сервере.

---

## ✅ Checklist настройки

- [ ] Сервер с Docker и Python подготовлен
- [ ] SSH ключ создан и добавлен на сервер
- [ ] GitHub Secrets настроены
- [ ] Директория релизов создана
- [ ] Тестовый запуск workflow успешен

---

## 1️⃣ Подготовка сервера

### Установка зависимостей

```bash
# Подключитесь к серверу
ssh user@your-server.com

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Git и инструментов
sudo apt install -y \
    git \
    curl \
    wget

# Проверка установки
docker --version
git --version
```

**Примечание:** Python больше не требуется! Windows EXE собирается на GitHub Windows runner.

### Создание директории для релизов

```bash
# Создать директорию
sudo mkdir -p /root/licenser-server/releases
sudo mkdir -p /root/licenser-server/archives

# Проверить права
ls -ld /root/licenser-server/
```

---

## 2️⃣ Настройка SSH доступа

### Генерация SSH ключа

На вашей локальной машине:

```bash
# Создать новый SSH ключ для GitHub Actions
ssh-keygen -t ed25519 \
    -C "github-actions-ci" \
    -f ~/.ssh/github_actions_release \
    -N ""

# Это создаст два файла:
#   ~/.ssh/github_actions_release      (приватный ключ)
#   ~/.ssh/github_actions_release.pub  (публичный ключ)
```

### Добавление ключа на сервер

```bash
# Скопировать публичный ключ на сервер
ssh-copy-id -i ~/.ssh/github_actions_release.pub user@your-server.com

# Или вручную:
cat ~/.ssh/github_actions_release.pub | \
    ssh user@your-server.com "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### Проверка подключения

```bash
# Проверить что ключ работает
ssh -i ~/.ssh/github_actions_release user@your-server.com "echo 'SSH работает!'"

# Если всё ОК, увидите: SSH работает!
```

### Получение приватного ключа для GitHub

```bash
# Скопировать содержимое приватного ключа
cat ~/.ssh/github_actions_release

# Вывод будет примерно таким:
# -----BEGIN OPENSSH PRIVATE KEY-----
# b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtz
# ...
# -----END OPENSSH PRIVATE KEY-----

# Скопируйте ВСЁ содержимое (включая строки BEGIN и END)
```

---

## 3️⃣ Настройка GitHub Secrets

### Добавление секретов

1. Откройте ваш репозиторий на GitHub
2. Перейдите в **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Добавьте следующие секреты:

#### SSH_HOST
```
Name: SSH_HOST
Secret: your-server.com
```
*Или IP адрес, например: 192.168.1.100*

#### SSH_USERNAME
```
Name: SSH_USERNAME
Secret: root
```
*Или другой пользователь с правами sudo*

#### SSH_PRIVATE_KEY
```
Name: SSH_PRIVATE_KEY
Secret: <содержимое ~/.ssh/github_actions_release>
```
*Скопируйте полностью, включая BEGIN и END*

#### SSH_PORT
```
Name: SSH_PORT
Secret: 22
```
*Стандартный порт SSH, измените если используете другой*

### Проверка секретов

После добавления вы должны увидеть:

```
✅ SSH_HOST
✅ SSH_USERNAME
✅ SSH_PRIVATE_KEY
✅ SSH_PORT
```

---

## 4️⃣ Тестирование настройки

### Проверка SSH подключения

```bash
# На вашей локальной машине проверьте все параметры
SSH_HOST="your-server.com"
SSH_USERNAME="root"
SSH_PORT="22"

ssh -i ~/.ssh/github_actions_release \
    -p $SSH_PORT \
    $SSH_USERNAME@$SSH_HOST \
    "echo 'Подключение успешно!'"
```

### Проверка окружения на сервере

```bash
ssh -i ~/.ssh/github_actions_release user@your-server.com << 'EOF'
echo "=== Проверка окружения ==="

# Docker
echo -n "Docker: "
docker --version && echo "✅" || echo "❌"

# Git
echo -n "Git: "
git --version && echo "✅" || echo "❌"

# Директория релизов
echo -n "Releases directory: "
[ -d "/root/licenser-server/releases" ] && echo "✅" || echo "❌"

# Свободное место
echo "Disk space:"
df -h / | tail -1

echo ""
echo "✅ Python больше не требуется - Windows EXE собирается на GitHub!"
echo "=== Проверка завершена ==="
EOF
```

---

## 5️⃣ Первый тестовый запуск

### Вариант 1: Через веб-интерфейс

1. Откройте репозиторий на GitHub
2. Перейдите во вкладку **Actions**
3. Выберите workflow **Build Release Package**
4. Нажмите **Run workflow** (справа)
5. Выберите ветку `main`
6. Нажмите зелёную кнопку **Run workflow**
7. Наблюдайте за процессом сборки

### Вариант 2: Через GitHub CLI

```bash
# Установка GitHub CLI (если ещё не установлен)
# https://cli.github.com/

# Авторизация
gh auth login

# Запуск workflow
gh workflow run build-release-package.yml --ref main

# Просмотр статуса
gh run list --workflow=build-release-package.yml

# Просмотр логов последнего запуска
gh run view --log
```

### Вариант 3: Простой push в main

```bash
# Сделайте любое изменение и запушьте
git add .
git commit -m "test: trigger release build"
git push origin main

# Workflow запустится автоматически
```

---

## 6️⃣ Проверка результатов

### На GitHub

1. **Actions** → выберите последний run
2. Убедитесь что все шаги зелёные ✅
3. Проверьте логи на наличие ошибок

### На сервере

```bash
# Подключиться к серверу
ssh user@your-server.com

# Проверить что релиз создан
ls -la /root/licenser-server/releases/

# Должна появиться папка с датой, например:
# drwxr-xr-x 2 root root 4096 Jan 15 14:30 2025-01-15_14-30-00

# Проверить содержимое релиза
cd /root/licenser-server/releases/$(ls -t /root/licenser-server/releases/ | head -1)
ls -lh

# Должны быть файлы:
# - docker-image-*.tar.gz (Docker образ)
# - license-helper-*-windows.exe (Windows EXE, нативная сборка!)
# - docker-compose.yml
# - install.sh (для Linux)
# - install.bat (для Windows)
# - README.md
# - release-manifest.json

# Проверить манифест
cat release-manifest.json
```

---

## 7️⃣ Настройка автоматической очистки (опционально)

### Копирование скрипта на сервер

```bash
# С локальной машины
scp scripts/cleanup-old-releases.sh user@your-server.com:/tmp/

# На сервере
ssh user@your-server.com
sudo mv /tmp/cleanup-old-releases.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/cleanup-old-releases.sh
```

### Настройка cron

```bash
# На сервере
sudo crontab -e

# Добавить строку (запуск каждое воскресенье в 2:00 ночи)
0 2 * * 0 /usr/local/bin/cleanup-old-releases.sh >> /var/log/cleanup-releases.log 2>&1
```

### Тестирование очистки

```bash
# Dry run (ничего не удаляет, только показывает что будет удалено)
DRY_RUN=true /usr/local/bin/cleanup-old-releases.sh

# Реальная очистка (удалит релизы старше 30 дней)
/usr/local/bin/cleanup-old-releases.sh
```

---

## 8️⃣ Настройка мониторинга (опционально)

### Email уведомления при провале сборки

В `.github/workflows/build-release-package.yml` добавьте в конец:

```yaml
      - name: Notify on failure
        if: failure()
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 465
          username: ${{ secrets.EMAIL_USERNAME }}
          password: ${{ secrets.EMAIL_PASSWORD }}
          subject: ❌ Release build failed
          body: |
            Release build failed!
            
            Workflow: ${{ github.workflow }}
            Run: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
            Commit: ${{ github.sha }}
          to: your-email@example.com
          from: GitHub Actions
```

Добавьте секреты:
- `EMAIL_USERNAME`
- `EMAIL_PASSWORD`

### Telegram уведомления

```yaml
      - name: Send Telegram notification
        if: always()
        uses: appleboy/telegram-action@master
        with:
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          message: |
            🚀 Release build ${{ job.status }}
            
            Repository: ${{ github.repository }}
            Version: ${{ steps.release_info.outputs.FULL_VERSION }}
            Status: ${{ job.status }}
```

---

## ❓ FAQ

### Q: Сколько места занимает один релиз?
A: Примерно 2-4 GB (Docker образ ~2-3 GB, exe ~50-100 MB)

### Q: Как часто нужно чистить старые релизы?
A: Рекомендуем хранить 5-10 последних релизов (или за последние 30 дней)

### Q: Можно ли собирать на локальной машине вместо сервера?
A: Можно, но нужен self-hosted runner. Сборка через SSH проще.

### Q: Как ускорить сборку?
A: Используйте Docker cache, держите базовые образы на сервере

### Q: Что делать если закончилось место?
A: Запустите `cleanup-old-releases.sh` или `docker system prune -a`

### Q: Почему Windows EXE собирается на GitHub, а не на сервере?
A: Нативная сборка на Windows даёт лучшую совместимость. PyInstaller работает лучше на той же платформе, для которой собирается exe.

### Q: Как работает передача файлов между job'ами?
A: Windows EXE временно сохраняется в GitHub Artifacts (1 день), затем скачивается в job на сервере и включается в финальный релиз.

---

## 🆘 Проблемы и решения

### "Permission denied" при SSH

```bash
# Проверьте права на ключ
chmod 600 ~/.ssh/github_actions_release

# Проверьте authorized_keys на сервере
ssh user@server "cat ~/.ssh/authorized_keys"
```

### "No space left on device"

```bash
# На сервере проверить место
df -h

# Очистить Docker
docker system prune -a -f

# Удалить старые релизы
/usr/local/bin/cleanup-old-releases.sh
```

### "Docker command not found"

```bash
# На сервере переустановить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиниться
exit
ssh user@server
```

### Workflow висит/не завершается

Проверьте:
1. Достаточно ли места на сервере
2. Не блокирует ли файрвол SSH
3. Не застрял ли Docker build
4. Посмотрите логи на сервере: `journalctl -f`

---

## ✅ Успешная настройка!

Если все шаги выполнены успешно, теперь:

✅ При каждом push в `main` автоматически собирается релиз  
✅ Windows EXE собирается нативно на GitHub Windows runner  
✅ Docker образ собирается на вашем сервере  
✅ Релизы хранятся на вашем сервере  
✅ Можно скачать релиз и передать клиенту (Windows или Linux)  
✅ Настроена автоматическая очистка старых релизов  

---

## 📚 Следующие шаги

1. Прочитайте [RELEASE_GUIDE.md](../RELEASE_GUIDE.md) для работы с релизами
2. Ознакомьтесь с [workflows README](.github/workflows/README.md)
3. Настройте мониторинг (опционально)
4. Проведите тестовое развёртывание у клиента

---

## 📞 Нужна помощь?

- [GitHub Issues](../../issues)
- [Документация workflows](./workflows/README.md)
- [Основной README](../README.md)

