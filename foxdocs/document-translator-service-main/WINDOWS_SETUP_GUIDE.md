# 🪟 Руководство по установке для Windows

## 📋 Требования

- **Windows 10/11** (64-bit)
- **Минимум 8 GB RAM** (рекомендуется 16 GB)
- **Минимум 20 GB свободного места** на диске
- **Docker Desktop** для Windows

---

## 🔧 Установка Docker Desktop

### Шаг 1: Скачивание

1. Перейдите на сайт: https://www.docker.com/products/docker-desktop
2. Нажмите **Download for Windows**
3. Дождитесь окончания загрузки (файл ~500 MB)

### Шаг 2: Установка

1. Запустите скачанный файл `Docker Desktop Installer.exe`
2. Следуйте инструкциям установщика:
   - ✅ Установите галочку **Use WSL 2 instead of Hyper-V** (рекомендуется)
   - ✅ Установите галочку **Add shortcut to desktop**
3. Нажмите **OK** и дождитесь завершения установки
4. **ПЕРЕЗАГРУЗИТЕ КОМПЬЮТЕР** (обязательно!)

### Шаг 3: Первый запуск

1. После перезагрузки запустите **Docker Desktop** с рабочего стола или из меню Пуск
2. При первом запуске может появиться запрос на установку WSL 2:
   - Нажмите **Install** и следуйте инструкциям
   - Перезагрузите компьютер если потребуется
3. Дождитесь сообщения **"Engine started"** в окне Docker Desktop
4. В трее (правый нижний угол) должна появиться иконка Docker с зеленым индикатором

> **Важно:** Docker Desktop должен быть запущен КАЖДЫЙ РАЗ перед работой с сервисом!

---

## 🚀 Быстрый старт

### 1️⃣ Подготовка файлов

После скачивания релиза у вас должна быть папка с файлами:

```
document-translator-service-YYYY-MM-DD/
├── docker-image-v2025.01.15-abc1234.tar   ← Docker образ
├── license-helper-v2025.01.15-abc1234-windows.exe   ← License Helper
├── docker-compose.yml   ← Конфигурация
├── load-image.bat   ← Скрипт загрузки образа
├── start.bat   ← Скрипт запуска
├── stop.bat   ← Скрипт остановки
└── README.md   ← Инструкции
```

### 2️⃣ Запуск Docker Desktop

1. Запустите **Docker Desktop**
2. Дождитесь сообщения **"Engine started"**
3. Убедитесь, что иконка в трее стала **зеленой**

### 3️⃣ Загрузка образа (первый раз)

**Вариант A: Через скрипт (рекомендуется)**

1. Откройте папку с релизом
2. **Дважды кликните** на файл **`load-image.bat`**
3. Дождитесь завершения (может занять 5-10 минут)
4. Вы увидите сообщение **"Образ успешно загружен!"**

**Вариант B: Вручную (через PowerShell)**

```powershell
# Откройте PowerShell в папке с релизом (Shift + правая кнопка мыши → "Open PowerShell window here")
docker load -i docker-image-*.tar
```

### 4️⃣ Запуск сервиса

**Вариант A: Через скрипт (рекомендуется)**

1. **Дважды кликните** на файл **`start.bat`**
2. Дождитесь сообщения **"Сервис успешно запущен!"**
3. Откройте в браузере: http://localhost:8000/docs

**Вариант B: Вручную (через PowerShell)**

```powershell
docker-compose up -d
```

### 5️⃣ Запуск License Helper

1. **Дважды кликните** на файл **`license-helper-*.exe`**
2. Откроется консольное окно (НЕ ЗАКРЫВАЙТЕ ЕГО!)
3. License Helper будет доступен на http://localhost:9999

---

## 🎯 Проверка работы

### Проверка основного сервиса

Откройте в браузере:
- **API документация:** http://localhost:8000/docs
- **Проверка здоровья:** http://localhost:8000/health

Или в PowerShell:
```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

### Проверка License Helper

В PowerShell:
```powershell
Invoke-RestMethod -Uri http://localhost:9999/health
Invoke-RestMethod -Uri http://localhost:9999/machine-id
```

---

## 🛑 Остановка сервиса

**Вариант A: Через скрипт (рекомендуется)**

1. **Дважды кликните** на файл **`stop.bat`**
2. Дождитесь сообщения **"Сервис успешно остановлен!"**

**Вариант B: Вручную**

```powershell
docker-compose down
```

> **Примечание:** License Helper (.exe) нужно останавливать вручную - просто закройте консольное окно.

---

## 📊 Просмотр логов

### Через Docker Desktop (удобно!)

1. Откройте **Docker Desktop**
2. Перейдите на вкладку **Containers**
3. Найдите **doctrans-app**
4. Кликните на него для просмотра логов

### Через командную строку

```powershell
# Показать все логи
docker-compose logs

# Следить за логами в реальном времени
docker-compose logs -f

# Показать последние 50 строк
docker-compose logs --tail=50
```

---

## 🔧 Управление Docker Desktop

### Автозапуск Docker Desktop

Если вы хотите, чтобы Docker запускался автоматически при включении компьютера:

1. Откройте **Docker Desktop**
2. Перейдите в **Settings** (иконка шестеренки)
3. Вкладка **General**
4. ✅ Включите **Start Docker Desktop when you log in**

### Ограничение ресурсов

Docker может потреблять много RAM и CPU. Чтобы ограничить:

1. Откройте **Docker Desktop**
2. **Settings** → **Resources**
3. Настройте:
   - **CPUs:** 2-4 (в зависимости от вашего процессора)
   - **Memory:** 4-8 GB (в зависимости от вашей RAM)
   - **Disk:** минимум 20 GB

---

## 🐛 Решение проблем

### Проблема: "Docker не запущен"

**Решение:**
1. Запустите **Docker Desktop** из меню Пуск
2. Дождитесь сообщения **"Engine started"**
3. Убедитесь, что иконка в трее **зеленая**
4. Попробуйте снова

### Проблема: "WSL 2 installation is incomplete"

**Решение:**
1. Откройте **PowerShell как администратор**
2. Выполните:
   ```powershell
   wsl --install
   ```
3. **Перезагрузите** компьютер
4. Запустите Docker Desktop снова

### Проблема: "Port 8000 is already in use"

**Решение:**

**Вариант A: Найти и закрыть программу, использующую порт**
```powershell
# Найти процесс
netstat -ano | findstr :8000

# Завершить процесс (замените PID на ID из предыдущей команды)
taskkill /PID <PID> /F
```

**Вариант B: Изменить порт в docker-compose.yml**
```yaml
ports:
  - "8080:8000"  # Используем 8080 вместо 8000
```

### Проблема: "Cannot connect to the Docker daemon"

**Решение:**
1. Убедитесь, что Docker Desktop ЗАПУЩЕН
2. Перезапустите Docker Desktop:
   - Правый клик на иконку Docker в трее → **Quit Docker Desktop**
   - Запустите снова из меню Пуск
3. Подождите "Engine started"

### Проблема: "Образ не найден"

**Решение:**
1. Убедитесь, что вы сначала загрузили образ: **`load-image.bat`**
2. Проверьте загруженные образы:
   ```powershell
   docker images
   ```
3. Если образа нет - загрузите заново

### Проблема: "Недостаточно памяти / Slow performance"

**Решение:**
1. Закройте ненужные программы
2. Ограничьте ресурсы Docker (см. раздел "Ограничение ресурсов")
3. Перезапустите Docker Desktop

### Проблема: License Helper не запускается

**Решение:**
1. Проверьте, что порт 9999 не занят:
   ```powershell
   netstat -ano | findstr :9999
   ```
2. Запустите exe **от имени администратора**:
   - Правый клик → **Запустить от имени администратора**
3. Проверьте, что Windows Defender не блокирует файл:
   - Откройте **Windows Security** → **Virus & threat protection**
   - Проверьте историю и добавьте исключение если нужно

---

## ⚙️ Дополнительные настройки

### Изменение портов

Если порты 8000 или 9999 уже заняты, отредактируйте `docker-compose.yml`:

```yaml
services:
  app:
    ports:
      - "8080:8000"  # Изменить левую часть (хост порт)
```

### Переменные окружения

Отредактируйте `docker-compose.yml`:

```yaml
environment:
  - APP_ENV=production       # development/production
  - APP_DEBUG=false          # true/false
  - PYTHONPATH=/app
  - ARGOS_DATA_DIR=/app/.argos
```

---

## 📚 Полезные команды

### Docker

```powershell
# Список запущенных контейнеров
docker ps

# Список всех контейнеров
docker ps -a

# Список образов
docker images

# Удалить остановленный контейнер
docker rm <container-id>

# Удалить образ
docker rmi <image-id>

# Очистить неиспользуемые ресурсы
docker system prune
```

### Docker Compose

```powershell
# Запустить
docker-compose up -d

# Остановить
docker-compose down

# Перезапустить
docker-compose restart

# Логи
docker-compose logs -f

# Статус
docker-compose ps
```

---

## 🔗 Полезные ссылки

- **Docker Desktop документация:** https://docs.docker.com/desktop/install/windows-install/
- **WSL 2 установка:** https://learn.microsoft.com/en-us/windows/wsl/install
- **Основная документация проекта:** README.md

---

## 📞 Поддержка

При возникновении проблем:

1. ✅ Проверьте эту документацию
2. ✅ Посмотрите логи: `docker-compose logs`
3. ✅ Проверьте Docker Desktop Dashboard
4. ✅ Создайте Issue на GitHub
5. ✅ Обратитесь к команде разработки

---

## 🎉 Готово!

Теперь у вас запущен Document Translator Service на Windows!

**Основные команды:**
- 🚀 Запуск: **`start.bat`** (дважды кликнуть)
- 🛑 Остановка: **`stop.bat`** (дважды кликнуть)
- 📊 Просмотр логов: Docker Desktop → Containers → doctrans-app
- 🌐 API: http://localhost:8000/docs

**Не забывайте:**
- Docker Desktop должен быть запущен перед использованием сервиса
- License Helper (.exe) нужно запускать отдельно

