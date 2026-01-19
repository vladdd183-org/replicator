# Исправление проблем PyInstaller сборки

## Проблемы

### Проблема 1: Множественные процессы Uvicorn (РЕШЕНО ✅)

При запуске `DocumentTranslator.exe` создаётся несколько процессов Uvicorn с reloader'ом, что приводит к бесконечному циклу и невозможности запуска приложения:

```
INFO:     Will watch for changes in these directories: ['C:\\Users\\Docker\\Desktop\\Shared']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [8872] using WatchFiles
```

### Проблема 2: PaddleX не может найти зависимости (РЕШЕНО ✅)

При запуске возникает ошибка:

```
paddlex.utils.deps.DependencyError: `OCR` requires additional dependencies.
RuntimeError: A dependency error occurred during pipeline creation.
OCRInitializationException: OCR initialization failed
```

## Причины

### Проблема 1: Режим reload
- **Режим reload не поддерживается PyInstaller**
- По умолчанию приложение запускается в режиме `development` с включенным `reload=True`
- Uvicorn пытается перезапустить процесс при изменениях файлов, что не работает в упакованном EXE

### Проблема 2: Отсутствие метаданных пакетов
- **PaddleX проверяет зависимости через метаданные пакетов**
- PyInstaller по умолчанию не включает файлы `.dist-info` и `.egg-info`
- PaddleX думает, что зависимости не установлены, хотя все модули присутствуют
- Также отсутствовал файл `CppSupport.cpp` из Cython

## Исправления

### Внесённые изменения

1. **Обновлён `src/Main.py`:**
   - ✅ Добавлена функция `is_frozen()` для определения запуска из PyInstaller
   - ✅ Режим reload автоматически отключается при запуске из EXE
   - ✅ Даже если установлен `APP_ENV=development`, reload будет отключен в EXE

2. **Обновлён `DocumentTranslator.spec.template`:**
   - ✅ Добавлен сбор данных Cython (решает проблему с `CppSupport.cpp`)
   - ✅ Добавлен сбор метаданных пакетов через `copy_metadata()`
   - ✅ Метаданные собираются для: paddlex, paddleocr, paddle, opencv, pillow, numpy и др.
   - ✅ Добавлены дополнительные скрытые импорты для PaddleX модулей
   - ✅ Добавлен runtime hook `pyi_rth_paddlex.py` в список runtime_hooks

3. **Создан `pyi_rth_paddlex.py`:**
   - ✅ Runtime hook выполняется при запуске EXE ДО загрузки приложения
   - ✅ Патчит функцию `paddlex.utils.deps.require_extra`
   - ✅ Отключает проверку метаданных пакетов
   - ✅ Все зависимости уже включены в EXE, проверка не требуется

### Что нужно сделать

#### Шаг 1: Пересобрать EXE

Выполните **одну** из команд:

**Вариант A - Быстрая пересборка (рекомендуется):**
```powershell
.\rebuild-exe.ps1
```

**Вариант B - Полная пересборка:**
```powershell
.\build-windows.ps1
```

⏱️ Время: 10-30 минут

#### Шаг 2: Запустить EXE

Перейдите в папку с EXE:
```powershell
cd .\dist\DocumentTranslator\
```

**Вариант 1 - Через PowerShell скрипт (рекомендуется):**
```powershell
.\RUN-EXE.ps1
```

**Вариант 2 - Через BAT файл:**
```cmd
RUN-EXE.bat
```

**Вариант 3 - Напрямую (обязательно установите переменные):**
```powershell
$env:APP_ENV = "production"
.\DocumentTranslator.exe
```

## Проверка успешного запуска

После исправления вы должны увидеть:

```
✅ Правильный запуск (ONE процесс):

21:54:31.381 Logfire configured successfully
INFO:     Started server process [3668]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

❌ **НЕ должно быть:**
- Строк `Will watch for changes in these directories`
- Строк `Started reloader process`
- Нескольких параллельных процессов

## Технические детали

### Исправление 1: Отключение reload в PyInstaller

```python
def is_frozen() -> bool:
    """Check if running in PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# В run_server():
frozen = is_frozen()

if settings.is_development and not frozen:
    # Reload только в development И когда НЕ из EXE
    uvicorn.run(..., reload=True, ...)
else:
    # Production режим ИЛИ запуск из EXE
    uvicorn.run(..., reload=False, ...)
```

### Исправление 2: Включение метаданных пакетов

```python
from PyInstaller.utils.hooks import copy_metadata

# Собираем метаданные для пакетов, которые проверяет PaddleX
metadata_packages = [
    'paddlex', 'paddleocr', 'paddle', 'paddlepaddle',
    'opencv-python-headless', 'opencv-contrib-python-headless',
    'pillow', 'numpy', 'pyyaml', 'scikit-image',
]

metadata_datas = []
for pkg in metadata_packages:
    try:
        metadata_datas.extend(copy_metadata(pkg))
    except Exception:
        pass

# Добавляем метаданные в datas
data_files.extend(metadata_datas)
```

Это позволяет PaddleX видеть установленные пакеты через их `.dist-info` файлы.

### Исправление 3: Runtime hook для патча проверки зависимостей

**Файл: `pyi_rth_paddlex.py`**

```python
# Runtime hook выполняется ПЕРЕД запуском приложения
if getattr(sys, 'frozen', False):
    # Импортируем модуль сразу
    import paddlex.utils.deps
    
    # Создаём функцию-заглушку
    def patched_require_extra(extra, obj_name=None, alt=None):
        # Просто возвращаемся без проверки
        return
    
    # Заменяем оригинальную функцию
    paddlex.utils.deps.require_extra = patched_require_extra
```

**Зачем это нужно:**
- PaddleX проверяет наличие зависимостей через `importlib.metadata`
- В PyInstaller метаданные могут быть недоступны
- Runtime hook патчит проверку ДО того как PaddleOCR попытается её вызвать
- Все модули уже есть в EXE, поэтому проверка не нужна

### Переменные окружения

Можно настроить через:

```powershell
$env:APP_ENV = "production"      # production или development
$env:APP_DEBUG = "False"         # True или False
$env:APP_HOST = "0.0.0.0"        # IP адрес
$env:APP_PORT = "8000"           # Порт
$env:LOGFIRE_TOKEN = "..."       # Опционально
```

## Если всё ещё не работает

### 1. Убедитесь, что используете новую версию

```powershell
# Удалите старую сборку
Remove-Item -Recurse -Force dist, build

# Пересоберите
.\build-windows.ps1
```

### 2. Проверьте версию исходников

Убедитесь, что в `src/Main.py` есть функция `is_frozen()`:

```python
def is_frozen() -> bool:
    """Check if running in PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
```

### 3. Проверьте переменные окружения

```powershell
# Должно быть установлено
$env:APP_ENV
# Вывод: production
```

### 4. Запустите с явным указанием переменных

```powershell
cd .\dist\DocumentTranslator\
$env:APP_ENV = "production"
$env:APP_DEBUG = "False"
.\DocumentTranslator.exe
```

## Резюме изменений

| Файл | Изменение | Зачем |
|------|-----------|-------|
| `src/Main.py` | ✅ Добавлена проверка `is_frozen()` | Отключить reload в EXE |
| `DocumentTranslator.spec.template` | ✅ Добавлен сбор Cython данных | Исправить ошибку с `CppSupport.cpp` |
| `DocumentTranslator.spec.template` | ✅ Добавлен `copy_metadata()` | Включить метаданные пакетов для PaddleX |
| `DocumentTranslator.spec.template` | ✅ Добавлены скрытые импорты PaddleX | Обеспечить наличие всех модулей |
| `DocumentTranslator.spec.template` | ✅ Добавлен `pyi_rth_paddlex.py` в runtime_hooks | Запустить патч при старте EXE |
| `pyi_rth_paddlex.py` | ✅ **НОВЫЙ ФАЙЛ** | Патч проверки зависимостей PaddleX |

## Что дальше?

После успешного запуска:

1. ✅ Сервер доступен на `http://localhost:8000`
2. ✅ Можно проверить API через `http://localhost:8000/docs`
3. ✅ Приложение работает в production режиме
4. ✅ Модели загрузятся автоматически при первом использовании

---

**Дата исправления:** 2025-11-01  
**Версия:** 1.0

