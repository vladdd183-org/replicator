# 🔧 Варианты сборки DocumentTranslator

## 📋 Обзор

Доступны **два режима** сборки и **два метода** сборки:

### Режимы сборки:

1. **ONE-DIR** (рекомендуется)
   - Папка с EXE и зависимостями
   - Быстрый запуск
   - Размер: ~2-3 ГБ папка
   
2. **ONE-FILE**
   - Один большой EXE файл
   - Медленный первый запуск (распаковка в TEMP)
   - Размер: ~2-3 ГБ файл
   - Проще распространять

### Методы сборки:

1. **Native Windows** - сборка напрямую в Windows
2. **Docker** - сборка в Docker контейнере (работает на Linux/Mac)

---

## 🖥️ Метод 1: Native Windows сборка

### Системные требования:
- Windows 10/11 (64-bit)
- Python 3.11
- 8-16 ГБ RAM
- ~10-15 ГБ свободного места

### ONE-DIR (рекомендуется):

```powershell
# Полная сборка с установкой зависимостей
.\build-windows.ps1

# Или быстрая пересборка (если venv уже есть)
.\rebuild-exe.ps1
```

**Результат:** `dist\DocumentTranslator\DocumentTranslator.exe`

**Время:** 20-40 минут (полная) или 10-20 минут (быстрая)

### ONE-FILE:

```powershell
# Сначала создайте venv через полную сборку
.\build-windows.ps1

# Затем соберите onefile версию
.\build-onefile.ps1
```

**Результат:** `dist\DocumentTranslator.exe` (один файл)

**Время:** 15-40 минут

---

## 🐳 Метод 2: Docker сборка

### Системные требования:
- Linux, macOS или Windows с WSL2
- Docker и Docker Compose
- ~20 ГБ свободного места для Docker образа
- 8-16 ГБ RAM

### Установка Docker:

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**macOS:**
```bash
brew install --cask docker
```

**Windows (WSL2):**
- Установите [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- Включите интеграцию с WSL2

### ONE-DIR через Docker:

```bash
./build-in-docker.sh onedir
```

**Результат:** `dist/DocumentTranslator/DocumentTranslator.exe`

**Время:** 40-90 минут (первая сборка), 30-60 минут (последующие)

### ONE-FILE через Docker:

```bash
./build-in-docker.sh onefile
```

**Результат:** `dist/DocumentTranslator.exe`

**Время:** 40-90 минут

### Использование docker-compose напрямую:

```bash
# ONE-DIR
docker-compose -f docker-compose.build.yml run --rm build-onedir

# ONE-FILE
docker-compose -f docker-compose.build.yml run --rm build-onefile
```

---

## 📊 Сравнение режимов

| Параметр | ONE-DIR | ONE-FILE |
|----------|---------|----------|
| **Размер дистрибутива** | ~2-3 ГБ (папка) | ~2-3 ГБ (файл) |
| **Скорость первого запуска** | ⚡ Быстро (~5 сек) | 🐌 Медленно (~30-60 сек) |
| **Скорость последующих запусков** | ⚡ Быстро | ⚡ Быстро |
| **Распространение** | Нужно копировать папку | Один файл |
| **Использование диска при запуске** | Только размер папки | +2-3 ГБ в TEMP |
| **Рекомендуется для** | Разработки, тестирования | Конечных пользователей |

---

## 🚀 Быстрый старт

### Windows (рекомендуется для начала):

```powershell
# Клонируйте репозиторий
git clone <repo-url>
cd document-translator-service

# Соберите ONE-DIR версию
.\build-windows.ps1

# Запустите
cd dist\DocumentTranslator
$env:APP_ENV = "production"
.\DocumentTranslator.exe
```

### Linux/Mac (через Docker):

```bash
# Клонируйте репозиторий
git clone <repo-url>
cd document-translator-service

# Соберите ONE-DIR версию
chmod +x build-in-docker.sh
./build-in-docker.sh onedir

# Перенесите dist/DocumentTranslator/ на Windows машину
# и запустите DocumentTranslator.exe
```

---

## 📁 Структура файлов сборки

```
document-translator-service/
├── build-windows.ps1                    # Native Windows: полная сборка ONE-DIR
├── rebuild-exe.ps1                      # Native Windows: быстрая пересборка ONE-DIR
├── build-onefile.ps1                    # Native Windows: сборка ONE-FILE
├── build-in-docker.sh                   # Docker: сборка (onedir или onefile)
├── DocumentTranslator.spec.template     # PyInstaller spec для ONE-DIR
├── DocumentTranslator.onefile.spec.template  # PyInstaller spec для ONE-FILE
├── Dockerfile.windows-build             # Docker образ для сборки
├── docker-compose.build.yml             # Docker Compose для сборки
├── pyi_rth_logfire.py                   # Runtime hook для logfire
├── pyi_rth_paddlex.py                   # Runtime hook для PaddleX
└── hook-multipart.py                    # PyInstaller hook для multipart
```

---

## 🔧 Продвинутое использование

### Кастомизация сборки

#### Изменить версию Python:
Отредактируйте `build-windows.ps1` или `Dockerfile.windows-build`:
```powershell
$PYTHON_VERSION = "3.12"  # или другая версия
```

#### Добавить дополнительные зависимости:
Отредактируйте `DocumentTranslator.spec.template`:
```python
hidden_imports = [
    # ... existing imports ...
    'your_module',
    'another_module',
]
```

#### Изменить название EXE:
Отредактируйте spec файлы:
```python
exe = EXE(
    ...
    name='YourAppName',  # вместо 'DocumentTranslator'
    ...
)
```

### Оптимизация размера

ONE-FILE можно сжать с помощью UPX (⚠️ осторожно, может вызвать проблемы):

```python
# В spec файле
exe = EXE(
    ...
    upx=True,
    upx_exclude=[],
)
```

---

## 🐛 Решение проблем

### Windows сборка

**Проблема:** Python не найден
```powershell
# Установите Python 3.11
# При установке отметьте "Add Python to PATH"
python --version  # Должно показать 3.11.x
```

**Проблема:** Не хватает памяти
```powershell
# Закройте другие программы
# Увеличьте файл подкачки Windows
```

**Проблема:** EXE не запускается
```powershell
# Установите Visual C++ Redistributable
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### Docker сборка

**Проблема:** Docker не найден
```bash
# Linux
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Mac
brew install --cask docker
```

**Проблема:** Permission denied
```bash
# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER
# Перелогиньтесь
```

**Проблема:** Out of memory
```bash
# Увеличьте память для Docker
# Docker Desktop -> Settings -> Resources -> Memory -> 8 GB+
```

---

## 📝 Логирование и отладка

### Включить debug режим

**Native Windows:**
```powershell
# В spec файле
exe = EXE(
    ...
    debug=True,  # Включить debug вывод
    console=True,  # Показывать консоль
)
```

**Docker:**
```bash
# Добавьте в docker-compose.build.yml
environment:
  - PYINSTALLER_DEBUG=1
```

### Просмотр логов сборки

**Windows:**
```powershell
# Логи PyInstaller в build/warn-*.txt
type build\warn-DocumentTranslator.txt
```

**Docker:**
```bash
# Логи в контейнере
docker-compose -f docker-compose.build.yml run --rm build-onedir sh -c "cat /build/build/warn-*.txt"
```

---

## 🎯 Рекомендации

### Для разработки:
- ✅ Используйте **Native Windows** сборку
- ✅ Используйте **ONE-DIR** режим
- ✅ Используйте `rebuild-exe.ps1` для быстрой пересборки

### Для тестирования:
- ✅ Используйте **ONE-DIR** режим
- ✅ Тестируйте на чистой Windows машине
- ✅ Проверьте работу без интернета

### Для production:
- ✅ Используйте **ONE-FILE** для простоты распространения
- ✅ Или **ONE-DIR** для лучшей производительности
- ✅ Включите в дистрибутив VC++ Redistributable
- ✅ Создайте installer (NSIS, Inno Setup)

### Для CI/CD:
- ✅ Используйте **Docker** сборку
- ✅ Настройте автоматическую сборку через GitHub Actions
- ✅ Сохраняйте артефакты в releases

---

## 🔗 Дополнительная информация

- [BUILD-WINDOWS-README.md](BUILD-WINDOWS-README.md) - подробная инструкция по Windows сборке
- [PYINSTALLER-RELOAD-FIX.md](PYINSTALLER-RELOAD-FIX.md) - решённые проблемы PyInstaller
- [КОМАНДЫ-ДЛЯ-ИСПРАВЛЕНИЯ.txt](КОМАНДЫ-ДЛЯ-ИСПРАВЛЕНИЯ.txt) - быстрые команды

---

*Версия документа: 1.0 | Дата: 2025-11-01*

