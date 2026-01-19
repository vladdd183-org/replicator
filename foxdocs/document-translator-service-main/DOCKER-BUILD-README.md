# 🐳 Docker Build для Document Translator

## ⚠️ Важная информация

### Windows EXE сборка

**РЕКОМЕНДУЕТСЯ**: Используйте **`build-windows.ps1`** на Windows машине для создания `.exe` файлов.

**Почему?**
- ✅ Стабильно и надёжно
- ✅ Проверено и работает
- ✅ Поддерживает onedir и onefile режимы
- ✅ Все зависимости корректно собираются

**Docker + Wine для Windows EXE**:
- ❌ Очень сложная настройка
- ❌ Проблемы с GUI зависимостями
- ❌ Ненадёжно для продакшена
- ⚠️ Требует Xvfb, Wine, сложную конфигурацию

---

## ✅ Что Docker может сделать

### 1. Linux Binary (работает!)

Docker может собрать **Linux** версию приложения:

```bash
# Собрать Linux binary
sudo sh build-in-docker.sh onefile

# Результат: dist/DocumentTranslator (Linux ELF)
```

**Использование:**
```bash
# На Linux
chmod +x dist/DocumentTranslator
./dist/DocumentTranslator
```

### 2. Для Windows - используйте build-windows.ps1

```powershell
# На Windows машине с PowerShell

# ONE-DIR (рекомендуется)
.\build-windows.ps1

# ONE-FILE
.\build-onefile.ps1
```

---

## 📋 Режимы сборки

### ONE-DIR (папка с EXE)
```
dist/
└── DocumentTranslator/
    ├── DocumentTranslator.exe    # 73-85 MB
    ├── python311.dll
    ├── _internal/                # Библиотеки и зависимости
    └── ... другие файлы
```

**Плюсы:**
- ⚡ Быстрый запуск (нет распаковки)
- 🔧 Легче отладка
- 📦 Проще обновления

**Минусы:**
- 📁 Много файлов для распространения

### ONE-FILE (один большой EXE)
```
dist/
└── DocumentTranslator.exe        # ~350-450 MB
```

**Плюсы:**
- 📦 Один файл для распространения
- 💼 Проще передача

**Минусы:**
- 🐌 Медленный первый запуск (распаковка во временную папку)
- 💾 Больший размер

---

## 🚀 Быстрый старт

### На Windows (РЕКОМЕНДУЕТСЯ для .exe)

```powershell
# 1. Клонируйте репозиторий
cd document-translator-service

# 2. Запустите сборку
.\build-windows.ps1

# 3. Результат
.\dist\DocumentTranslator\DocumentTranslator.exe
```

### На Linux/Mac с Docker (для Linux binary)

```bash
# 1. Клонируйте репозиторий
cd document-translator-service

# 2. Запустите сборку
sudo sh build-in-docker.sh onefile

# 3. Результат
./dist/DocumentTranslator
```

---

## 📝 Технические детали

### Windows EXE через Wine (экспериментально)

Если **очень** нужна Docker сборка Windows EXE, возможны проблемы:

1. **libGL.so.1 ошибки** - OpenCV требует графические библиотеки
2. **XDG_RUNTIME_DIR** - Wine требует настройки окружения
3. **Медленная сборка** - 30-60 минут первый раз
4. **Нестабильность** - Wine может крашиться

### Текущий Docker (Linux binary)

`Dockerfile.windows-pyinstaller`:
- ✅ Python 3.11
- ✅ Все зависимости из `build-windows.ps1`
- ✅ PyInstaller 6.x
- ✅ Быстрая сборка (10-15 минут после кеша)
- ✅ Стабильно

---

## 💡 Рекомендации

### Для продакшена:

1. **Windows EXE** → используйте `build-windows.ps1` на Windows
2. **Linux binary** → используйте Docker
3. **Тестирование** → Docker для CI/CD

### Для разработки:

```bash
# Запуск без сборки в EXE
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
python -m src.Main
```

---

## 📚 Дополнительно

- **`BUILD-OPTIONS-README.md`** - полное описание всех опций сборки
- **`PYINSTALLER-RELOAD-FIX.md`** - решение проблем с PyInstaller
- **`build-windows.ps1`** - проверенный скрипт для Windows

---

## 🆘 Проблемы?

### Windows EXE не запускается
→ См. `PYINSTALLER-RELOAD-FIX.md`

### Docker не работает
→ Убедитесь что Docker установлен и запущен

### Нужна помощь с Wine
→ **Рекомендуем: не используйте Wine, используйте Windows машину**

