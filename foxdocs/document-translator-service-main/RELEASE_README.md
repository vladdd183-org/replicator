# Document Translator Service - Релизный пакет

## 📦 Содержимое релиза

- `docker-image-*.tar` - Docker образ сервиса
- `license-helper-*.exe` - License Helper для Windows (нативная сборка)
- `docker-compose.yml` - Конфигурация для запуска
- `load-image.bat` / `load-image.ps1` - Скрипт загрузки образа (Windows)
- `start.bat` / `start.ps1` - Скрипт запуска сервиса (Windows)
- `stop.bat` / `stop.ps1` - Скрипт остановки сервиса (Windows)
- `WINDOWS_SETUP_GUIDE.md` - Подробное руководство для Windows
- `README.md` - Этот файл

---

## 🚀 Быстрый старт

### 🪟 Windows (РЕКОМЕНДУЕТСЯ для начинающих)

> **Для Windows пользователей есть удобные скрипты!** 
> Подробное руководство смотрите в файле **`WINDOWS_SETUP_GUIDE.md`**

**Шаг 1: Запустите Docker Desktop**
- Откройте Docker Desktop из меню Пуск
- Дождитесь сообщения "Engine started"

**Шаг 2: Загрузите образ (только первый раз)**
- Дважды кликните на **`load-image.bat`**
- Дождитесь завершения (5-10 минут)

**Шаг 3: Запустите сервис**
- Дважды кликните на **`start.bat`**
- Откройте в браузере: http://localhost:8000/docs

**Шаг 4: Запустите License Helper**
- Дважды кликните на **`license-helper-*.exe`**
- Не закрывайте консольное окно!

**Остановка:**
- Дважды кликните на **`stop.bat`**

---

### 🐧 Linux

```bash
# 1. Загрузить Docker образ
docker load -i docker-image-*.tar

# 2. Запустить сервисы
docker-compose up -d

# 3. Проверить
curl http://localhost:8000/health
```

---

### 🪟 Windows (продвинутые пользователи)

```powershell
# PowerShell

# 1. Загрузить Docker образ
docker load -i docker-image-*.tar

# 2. Запустить сервисы
docker-compose up -d

# 3. Проверить
Invoke-RestMethod -Uri http://localhost:8000/health
```

---

## 🔧 Установка Docker

### 🪟 Windows
1. Скачать Docker Desktop: https://www.docker.com/products/docker-desktop
2. Установить и **ОБЯЗАТЕЛЬНО ПЕРЕЗАГРУЗИТЬ** компьютер
3. Запустить Docker Desktop
4. Дождаться сообщения **"Engine started"**

> **Подробная инструкция для Windows:** см. файл **`WINDOWS_SETUP_GUIDE.md`**

### 🐧 Linux (Ubuntu/Debian)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Перелогиниться
```

---

## 📝 Использование

### Основной сервис (порт 8000)

```bash
# Проверка здоровья
curl http://localhost:8000/health

# API документация
http://localhost:8000/docs

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Перезапуск
docker-compose restart
```

### License Helper (порт 9999)

#### Windows
```powershell
# Запустить exe файл
.\license-helper-*.exe

# Проверить работу
Invoke-RestMethod -Uri http://localhost:9999/health
Invoke-RestMethod -Uri http://localhost:9999/machine-id
```

#### Установка как службы (Linux)
```bash
# Скопировать в system
sudo cp license-helper /usr/local/bin/
sudo chmod +x /usr/local/bin/license-helper

# Создать systemd service
# См. документацию в license_helper/
```

---

## ⚙️ Конфигурация

### Переменные окружения

Отредактируйте `docker-compose.yml`:

```yaml
environment:
  - APP_ENV=production          # development/production
  - APP_DEBUG=false             # true/false
  - PYTHONPATH=/app
  - ARGOS_DATA_DIR=/app/.argos
```

### Порты

По умолчанию:
- **8000** - Основной API сервис
- **9999** - License Helper (если запущен)

Изменить можно в `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Изменить на 8080
```

---

## 🔍 Проверка установки

```bash
# 1. Docker работает?
docker ps

# 2. Сервис отвечает?
curl http://localhost:8000/health

# 3. Логи без ошибок?
docker-compose logs --tail=50

# 4. Версия сервиса
curl http://localhost:8000/version
```

---

## 🐛 Решение проблем

### "Cannot connect to Docker daemon"
```bash
# Убедитесь что Docker запущен
sudo systemctl start docker

# Проверьте права
sudo usermod -aG docker $USER
# Перелогиниться
```

### "Port already in use"
```bash
# Найти процесс на порту 8000
sudo lsof -i :8000
# Или изменить порт в docker-compose.yml
```

### "Image not found"
```bash
# Убедитесь что образ загружен
docker images | grep document-translator

# Загрузить заново
docker load -i docker-image-*.tar
```

### Высокое использование RAM/CPU
```bash
# Ограничить ресурсы в docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

---

## 📚 Документация

- **[🪟 Руководство для Windows](WINDOWS_SETUP_GUIDE.md)** - НАЧНИТЕ ОТСЮДА если используете Windows!
- [Основная документация](https://github.com/your-repo)
- [API документация](http://localhost:8000/docs) (после запуска)
- [License Helper](https://github.com/your-repo/tree/main/license_helper)

---

## 🔐 Безопасность

- Сервис работает в изолированном Docker контейнере
- License Helper использует локальное подключение
- Рекомендуется использовать файрвол для ограничения доступа
- В production отключите DEBUG режим

---

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs`
2. Проверьте документацию выше
3. Создайте Issue на GitHub
4. Обратитесь к команде разработки

---

**Версия релиза:** См. `release-manifest.json`  
**Дата сборки:** См. `release-manifest.json`

