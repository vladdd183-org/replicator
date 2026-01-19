# Сравнение: GitHub Actions (Windows runners) vs Docker (Wine-based)

## 📊 Краткое сравнение

| Параметр | GitHub Actions (оригинал) | Docker + Wine |
|----------|---------------------------|---------------|
| **Runner** | `windows-latest` | `ubuntu-latest` |
| **Время сборки** | ~15-20 минут | ~20-25 минут |
| **Стоимость** | Высокая (Windows = 2x Linux) | Низкая (Linux = 1x) |
| **Параллелизм** | 2 jobs (license-helper + DocumentTranslator) | 1 job (оба EXE) |
| **Сложность** | Простая (нативный Windows) | Средняя (Wine эмуляция) |
| **Совместимость** | 100% | ~95% (Wine edge cases) |
| **Портируемость** | Только GitHub Actions / Azure DevOps | Любая CI/CD с Docker |

---

## 💰 Экономия в GitHub Actions

### Стоимость минут в GitHub Actions

- **Linux (Ubuntu)**: 1x множитель
- **Windows**: 2x множитель  
- **macOS**: 10x множитель

**Пример расчета для публичного репозитория:**

```
Оригинальный workflow (Windows):
- Job 1 (license-helper): 10 минут × 2 = 20 минут
- Job 2 (DocumentTranslator): 15 минут × 2 = 30 минут
- Job 3 (Package): 5 минут × 1 = 5 минут
ИТОГО: 55 минут (эквивалентных Linux минут)

Docker-based workflow (Linux):
- Job 1 (Docker build): 25 минут × 1 = 25 минут
- Job 2 (Package): 5 минут × 1 = 5 минут
ИТОГО: 30 минут

Экономия: 45% минут!
```

**Для приватного репозитория с платным планом - экономия ~$$$:**

```
GitHub Team: $4/user/month включает 3000 минут
Сверх лимита:
- Linux: $0.008/минута
- Windows: $0.016/минута

Оригинальный workflow: 50 минут Windows = $0.80
Docker-based: 25 минут Linux = $0.20

Экономия: $0.60 на сборку или 75%!
```

---

## ⚡ Детальное сравнение workflow

### Оригинальный: `build-release-package.yml`

```yaml
build-windows-exe:
  runs-on: windows-latest  # 💰 Дорого: 2x множитель
  steps:
    - Setup Python 3.11
    - pip install pyarmor pyinstaller
    - pip install -r license_helper/requirements.txt
    - pyarmor gen (обфускация)
    - pyinstaller (сборка EXE)
    - Upload via Posh-SSH

build-document-translator-exe:
  runs-on: windows-latest  # 💰 Дорого: еще 2x множитель
  steps:
    - Setup Python 3.11
    - .\build-windows.ps1 -DepsOnly
    - .\build-onefile.ps1
    - Upload via Posh-SSH

build-and-package:
  runs-on: ubuntu-latest
  needs: [build-windows-exe, build-document-translator-exe]
  # Создание релиза на сервере
```

**Проблемы:**
- 🐌 Два последовательных Windows jobs (нельзя запустить параллельно из-за SSH upload)
- 💰 Двойная оплата за Windows минуты
- 🔒 Привязка к GitHub Actions (Posh-SSH)

### Docker-based: `build-release-package-docker.yml`

```yaml
build-windows-exe-docker:
  runs-on: ubuntu-latest  # 💰 Дешево: 1x множитель
  steps:
    - Checkout code
    - docker build (собирает ОБА EXE в одном контейнере!)
    - docker cp (извлечение файлов)
    - sshpass scp (загрузка на сервер)

build-and-package:
  runs-on: ubuntu-latest
  needs: [build-windows-exe-docker]
  # Создание релиза на сервере
```

**Преимущества:**
- ⚡ Один job собирает оба EXE параллельно (multi-stage build)
- 💰 Дешевле в 2+ раза (Ubuntu вместо Windows)
- 🐧 Работает на любой CI/CD с Docker
- 📦 Reproducible builds (Dockerfile = версионированная среда)

---

## 🔍 Построчное сравнение шагов

### Установка зависимостей

**Windows (оригинал):**
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install pyarmor pyinstaller
    pip install -r license_helper/requirements.txt
```

**Docker (Wine):**
```dockerfile
# В Dockerfile
RUN apt-get install wine64
RUN wget python-3.11.9-amd64.exe
RUN xvfb-run wine python-installer.exe /quiet
ENV WINE_PIP="wine C:\\Python311\\Scripts\\pip.exe"
RUN ${WINE_PIP} install pyarmor pyinstaller
RUN ${WINE_PIP} install -r requirements.txt
```

### Обфускация с PyArmor

**Windows (оригинал):**
```powershell
mkdir -p obfuscated
pyarmor gen -O obfuscated -r license_helper.py
```

**Docker (Wine):**
```dockerfile
RUN mkdir -p obfuscated && \
    wine C:\\Python311\\Scripts\\pyarmor.exe gen -O obfuscated -r license_helper.py
```

### Сборка с PyInstaller

**Windows (оригинал):**
```powershell
$buildArgs = @("--onefile", "--name", "license-helper", ...)
pyinstaller $buildArgs license_helper.py
```

**Docker (Wine):**
```dockerfile
RUN wine C:\\Python311\\Scripts\\pyinstaller.exe \
    --onefile \
    --name license-helper \
    ... \
    license_helper.py
```

### Загрузка на сервер

**Windows (оригинал - сложно):**
```powershell
Install-Module -Name Posh-SSH -Force
$credential = New-Object System.Management.Automation.PSCredential (...)
$session = New-SSHSession -ComputerName ... -Credential $credential
Set-SCPItem -Path $exeFile.FullName -Destination /tmp/...
```

**Docker (Linux - просто):**
```bash
sudo apt-get install sshpass
sshpass -p '${{ secrets.SSH_PASS }}' \
  scp -r /tmp/build/* user@host:/tmp/build/
```

---

## 🛠️ Как переключиться на Docker-based

### Вариант 1: Полная замена (рекомендуется для экономии)

```bash
# Отключить оригинальный workflow
git mv .github/workflows/build-release-package.yml \
       .github/workflows/build-release-package.yml.disabled

# Включить Docker-based workflow
git mv .github/workflows/build-release-package-docker.yml \
       .github/workflows/build-release-package.yml

git commit -m "Switch to Docker-based build for cost savings"
```

### Вариант 2: Параллельно (A/B тестирование)

Оставить оба workflow, но с разными triggers:

```yaml
# build-release-package.yml (Windows)
on:
  workflow_dispatch:  # Только ручной запуск

# build-release-package-docker.yml (Docker)
on:
  push:
    branches: [main]  # Автоматический запуск
  workflow_dispatch:
```

### Вариант 3: По расписанию

```yaml
# Nightlybuild через Docker (дешево)
on:
  schedule:
    - cron: '0 2 * * *'  # 02:00 UTC каждый день

# Release build через Windows (надежно)
on:
  release:
    types: [published]
```

---

## ⚠️ Ограничения Docker + Wine

### Что может не работать:

1. **COM объекты Windows**
   ```python
   # Не будет работать в Wine
   import win32com.client
   excel = win32com.client.Dispatch("Excel.Application")
   ```

2. **WMI (Windows Management Instrumentation)**
   ```python
   # Не будет работать в Wine
   import wmi
   c = wmi.WMI()
   ```

3. **Native Windows API через ctypes**
   ```python
   # Может не работать в Wine
   import ctypes
   ctypes.windll.kernel32.GetComputerNameW(...)
   ```

4. **Hardware-специфичные библиотеки**
   - GPU ускорение (CUDA, DirectX)
   - USB устройства
   - Принтеры

### Что РАБОТАЕТ без проблем:

✅ PyInstaller + стандартная библиотека Python  
✅ FastAPI, Flask, Django  
✅ NumPy, Pandas, requests, aiohttp  
✅ Cryptography  
✅ SQLite, PostgreSQL (клиенты)  
✅ PyArmor обфускация  
✅ Большинство pure-Python пакетов

---

## 🧪 Тестирование перед переходом

### 1. Локальный тест Docker сборки

```bash
# Соберите локально
./build-with-docker.sh

# Проверьте EXE файлы
cd release-output
ls -lh *.exe

# Если есть Windows машина - протестируйте EXE
# Иначе - используйте Wine для базового теста
wine DocumentTranslator-*.exe --version
```

### 2. A/B тест в CI/CD

```yaml
# Создайте тестовый workflow
name: Test Docker Build
on: [workflow_dispatch]

jobs:
  test-docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./build-with-docker.sh
      - uses: actions/upload-artifact@v4
        with:
          name: test-exe
          path: release-output/*.exe
```

Запустите вручную и сравните размеры/результаты с оригинальными EXE.

### 3. Smoke test на Windows

Скачайте EXE из Docker сборки и проверьте:

```batch
REM Запуск должен работать
license-helper.exe --help
DocumentTranslator.exe --version

REM Проверка основных функций
license-helper.exe start
REM ... проверить API endpoints
```

---

## 📋 Checklist перехода

- [ ] Создать `Dockerfile.windows-builder-wine`
- [ ] Создать `build-with-docker.sh`
- [ ] Протестировать локально
- [ ] Создать `.github/workflows/build-release-package-docker.yml`
- [ ] Протестировать в CI/CD (workflow_dispatch)
- [ ] Сравнить результаты с оригинальными EXE
- [ ] Smoke test на Windows машине
- [ ] Проверить размеры файлов (должны быть похожи ±10%)
- [ ] Проверить что обе программы запускаются
- [ ] Переключить production builds на Docker

---

## 🎯 Рекомендация

**Для вашего проекта рекомендую Docker-based подход потому что:**

1. ✅ **Ваш код не использует специфичные Windows API**
   - FastAPI/Uvicorn отлично работают в Wine
   - Cryptography поддерживается
   - Никаких COM/WMI зависимостей

2. 💰 **Значительная экономия** (~50% минут)

3. 🐧 **Переносимость** - можно запустить на любом Linux CI/CD

4. 📦 **Reproducible builds** - Dockerfile = версионированная среда

5. ⚡ **Параллелизм** - оба EXE собираются в одном контейнере

**Начните с A/B тестирования** (оба workflow параллельно), затем полностью переключитесь на Docker если всё работает.

---

## 📚 Дополнительные ресурсы

- [Wine HQ Documentation](https://www.winehq.org/documentation)
- [PyInstaller with Wine](https://pyinstaller.org/en/stable/usage.html#supporting-multiple-platforms)
- [GitHub Actions Pricing](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions)
- [Docker Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)

