# Сборка Document Translator Service для Windows

## Системные требования

- **Windows 10/11** (64-bit)
- **Python 3.11** - [Скачать с python.org](https://www.python.org/downloads/)
- **Минимум 8 ГБ RAM** (рекомендуется 16 ГБ)
- **~10-15 ГБ свободного места** на диске для сборки
- **Стабильное интернет-соединение** для загрузки зависимостей

## Быстрый старт

### Вариант 1: Через BAT файл (рекомендуется)

1. Откройте папку проекта в проводнике
2. Дважды кликните на `build-windows.bat`
3. Дождитесь завершения сборки (20-40 минут)

### Вариант 2: Через PowerShell

1. Откройте PowerShell в папке проекта
2. Выполните команду:
```powershell
.\build-windows.ps1
```

## Что делает скрипт

1. ✅ Проверяет наличие Python 3.11
2. ✅ Создаёт виртуальное окружение
3. ✅ Обновляет pip, setuptools, wheel
4. ✅ Устанавливает все зависимости в правильном порядке:
   - numpy, PyYAML, Cython
   - OpenCV (CPU-only headless версии)
   - Litestar, Pydantic, Uvicorn
   - PaddlePaddle (CPU-only)
   - PaddleX, PaddleOCR
   - PyTorch (CPU-only)
   - Stanza, argostranslate
   - PyMuPDF и другие
5. ✅ Проверяет отсутствие NVIDIA/CUDA пакетов
6. ✅ Предзагружает модели (если возможно)
7. ✅ Собирает EXE файл через PyInstaller

## Результат сборки

После успешной сборки вы найдёте:

```
dist/
└── DocumentTranslator/
    ├── DocumentTranslator.exe  <- Главный исполняемый файл
    ├── README.txt              <- Инструкция по запуску
    ├── _internal/              <- Зависимости и библиотеки
    ├── .cache/                 <- Кеш моделей (если предзагружены)
    ├── .argos/                 <- Модели перевода
    ├── .paddlex/               <- PaddleX модели
    └── .stanza/                <- Stanza модели
```

**Размер дистрибутива:** ~1.5-2.5 ГБ

## Запуск собранного приложения

⚠️ **ВАЖНО:** EXE должен запускаться в production режиме, иначе будет ошибка с множественными процессами!

### Рекомендуемый способ (через скрипты)

1. Перейдите в папку `dist\DocumentTranslator\`
2. Запустите через скрипт:
   - **PowerShell:** `.\RUN-EXE.ps1`
   - **CMD:** `RUN-EXE.bat`
3. Сервер запустится на `http://localhost:8000`

Скрипты автоматически устанавливают правильные переменные окружения.

### Ручной запуск

Если запускаете напрямую, **обязательно** установите переменные:

**PowerShell:**
```powershell
cd dist\DocumentTranslator
$env:APP_ENV = "production"
.\DocumentTranslator.exe
```

**CMD:**
```cmd
cd dist\DocumentTranslator
set APP_ENV=production
DocumentTranslator.exe
```

### Параметры запуска

Вы можете настроить через переменные окружения:

**PowerShell:**
```powershell
$env:APP_ENV = "production"    # Обязательно!
$env:APP_PORT = "9000"
$env:APP_HOST = "127.0.0.1"
.\DocumentTranslator.exe
```

**CMD:**
```cmd
set APP_ENV=production
set APP_PORT=9000
set APP_HOST=127.0.0.1
DocumentTranslator.exe
```

## Распространение

Для распространения просто скопируйте всю папку `dist\DocumentTranslator\` на целевой компьютер.

**Требования на целевом ПК:**
- Windows 10/11 (64-bit)
- Visual C++ Redistributable 2015-2022 ([скачать](https://aka.ms/vs/17/release/vc_redist.x64.exe))
- ~2-3 ГБ свободного места

## Решение проблем

### ❌ Ошибка: Множественные процессы / "Started reloader process"

**Симптомы:**
```
INFO: Will watch for changes in these directories
INFO: Started reloader process [8872] using WatchFiles
INFO: Started reloader process [6972] using WatchFiles
```

**Причина:** EXE запущен без переменной `APP_ENV=production`

**Решение:**
1. Остановите все запущенные процессы (CTRL+C)
2. Установите переменную окружения:
   ```powershell
   $env:APP_ENV = "production"
   .\DocumentTranslator.exe
   ```
3. Или используйте готовые скрипты: `RUN-EXE.ps1` или `RUN-EXE.bat`

📄 Подробности в файле `PYINSTALLER-RELOAD-FIX.md`

### Ошибка: "Python не найден"

Установите Python 3.11:
1. Скачайте с [python.org](https://www.python.org/downloads/)
2. При установке отметьте "Add Python to PATH"
3. Перезапустите PowerShell/CMD

### Ошибка: "Недостаточно памяти"

- Закройте другие программы
- Увеличьте размер файла подкачки Windows
- Попробуйте на машине с большим объёмом RAM

### Ошибка: "Не удаётся скачать пакеты"

- Проверьте интернет-соединение
- Попробуйте использовать VPN
- Проверьте настройки proxy

### EXE не запускается

1. Установите Visual C++ Redistributable 2015-2022
2. Проверьте что антивирус не блокирует файл
3. Запустите из командной строки для просмотра ошибок:
   ```cmd
   cd dist\DocumentTranslator
   DocumentTranslator.exe
   ```

### Долгий первый запуск

При первом запуске могут загружаться дополнительные модели. Это нормально.
Подождите 5-10 минут. Последующие запуски будут быстрее.

## Файлы проекта

- `build-windows.ps1` - Основной скрипт сборки PowerShell
- `build-windows.bat` - Wrapper для запуска PowerShell скрипта
- `DocumentTranslator.spec.template` - Шаблон конфигурации PyInstaller
- `.pip-constraints.txt` - Ограничения для pip (блокирует CUDA пакеты)

## Очистка после сборки

Для очистки временных файлов:

```powershell
Remove-Item -Recurse -Force venv, build, __pycache__, *.spec
```

Для полной очистки (включая дистрибутив):

```powershell
Remove-Item -Recurse -Force venv, build, dist, __pycache__, *.spec, .cache, .argos, .paddlex, .stanza
```

## Известные ограничения

1. **CPU-only** - без GPU ускорения (медленнее, но работает везде)
2. **Большой размер** - ~2 ГБ из-за ML библиотек
3. **Windows only** - для Linux используйте Docker
4. **Долгая сборка** - 20-40 минут из-за компиляции нативных расширений

## Техническая поддержка

При возникновении проблем предоставьте:
1. Полный текст ошибки
2. Вывод команды `python --version`
3. Версию Windows (`winver`)
4. Объём RAM

## Лицензия

См. LICENSE файл в корне проекта.

