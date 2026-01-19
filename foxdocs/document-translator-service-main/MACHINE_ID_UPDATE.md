# Обновление системы получения Machine ID

## Проблема

На разных компьютерах разных пользователей на сервер отправлялся **один и тот же machine ID**, что делало невозможным корректное лицензирование на базе уникального идентификатора машины.

### Причины проблемы в старой реализации:

1. **Использование `wmic` на Windows** - может возвращать одинаковые UUID на клонированных системах или виртуальных машинах
2. **Использование `dmidecode` на Linux** - требует прав root, часто падает в fallback
3. **Fallback на MAC адрес** - может быть одинаковым на виртуальных машинах или измененным вручную
4. **Комбинация UUID + серийный номер диска** - может быть одинаковой на клонированных системах

## Решение

Переход на библиотеку **[py-machineid](https://github.com/keygen-sh/py-machineid)** - надежное и кросс-платформенное решение для получения уникального идентификатора машины.

### Преимущества py-machineid:

✅ **Работает без прав администратора** - не требует elevated privileges  
✅ **Кросс-платформенность** - Windows, Linux, macOS  
✅ **Надежные источники данных:**
- **Windows**: `MachineGuid` из реестра (`HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography`)
- **Linux**: `/etc/machine-id` или `/var/lib/dbus/machine-id`
- **macOS**: `IOPlatformUUID` через `ioreg`

✅ **Стабильность** - ID не меняется при обновлениях ОС  
✅ **Уникальность** - использует системные GUID, уникальные для каждой установки ОС

## Изменения в коде

### 1. Добавлена зависимость

**`pyproject.toml`:**
```toml
"py-machineid>=0.6.0",  # Надежное получение уникального machine ID
```

**`license_helper/requirements.txt`:**
```
py-machineid>=0.6.0
```

**`build-windows.ps1`:**
```powershell
"py-machineid>=0.6.0" `
```

### 2. Обновлен код получения Machine ID

#### `src/Ship/Licensing/machine_id.py`

Раньше:
```python
# Старая реализация использовала wmic/dmidecode
def _get_machine_id_windows():
    cmd_uuid = 'wmic csproduct get uuid'
    # ... сложная логика с fallback на MAC
```

Теперь:
```python
import machineid

def get_machine_id() -> str:
    """Использует py-machineid для надежного получения ID"""
    if machineid is not None:
        # Используем надежную библиотеку
        machine_id = machineid.hashed_id('document-translator-service')
        return machine_id
    else:
        # Fallback только если библиотека не установлена
        # ...
```

#### `license_helper/license_helper.py`

Аналогичные изменения в standalone helper сервисе.

## Особенности реализации

### Graceful Degradation

Код поддерживает fallback, если библиотека `py-machineid` не установлена:

```python
try:
    import machineid
except ImportError:
    machineid = None
    # Используем старый fallback метод
```

### Application ID

Для дополнительной уникальности используется `app_id`:

```python
machine_id = machineid.hashed_id('document-translator-service')
```

Это гарантирует, что даже если два разных приложения используют py-machineid, они получат разные хеши.

### Формат вывода

Библиотека возвращает **SHA256 хеш** (64 символа), что соответствует формату старой реализации:

```
Before: a1b2c3d4e5f6...  (SHA256 от комбинации UUID:SerialNumber)
After:  x9y8z7w6v5u4...  (SHA256 от system machine ID + app_id)
```

## Совместимость с PyInstaller

Библиотека `py-machineid` хорошо работает с PyInstaller:

- **Не требует дополнительных hooks** (чистый Python)
- **Нет бинарных зависимостей** (использует только стандартные системные вызовы)
- **Работает в режиме onefile** и **onedir**

### Тестирование в build-windows

```powershell
# Установка зависимостей
.\build-windows.ps1 -DepsOnly

# Сборка ONE-DIR
.\build-windows.ps1

# Сборка ONE-FILE
.\build-onefile.ps1
```

## Миграция существующих лицензий

### ⚠️ ВАЖНО: Machine ID изменится!

После обновления **все machine ID пользователей изменятся**, потому что:

- Старая реализация: `SHA256(UUID:DiskSerial)`
- Новая реализация: `SHA256(MachineGuid:AppID)`

### План миграции:

1. **Вариант A: Переактивация** (рекомендуется)
   - Пользователям нужно будет повторно получить свой новый Machine ID
   - Обновить лицензию на сервере с новым Machine ID

2. **Вариант B: Двойная проверка** (переходный период)
   - Сохранить старую реализацию как fallback
   - Сервер проверяет оба варианта Machine ID (старый и новый)
   - Постепенный переход пользователей на новую систему

### Код для получения нового Machine ID:

```python
# Пользователь может получить свой новый ID через:
GET http://localhost:9999/machine-id

# Ответ:
{
    "machine_id": "новый_sha256_hash",
    "message": "Use this Machine ID to register your license"
}
```

## Тестирование

### 1. Локальное тестирование

```python
# test_machine_id.py
from src.Ship.Licensing.machine_id import get_machine_id

# Получаем machine ID
mid = get_machine_id()
print(f"Machine ID: {mid}")

# Проверяем стабильность (должен быть одинаковым)
mid2 = get_machine_id()
assert mid == mid2, "Machine ID должен быть стабильным!"
```

### 2. Тестирование в разных окружениях

```bash
# Docker контейнер
docker run -it ubuntu:22.04 bash
apt update && apt install python3-pip
pip3 install py-machineid
python3 -c "import machineid; print(machineid.id())"

# Виртуальная машина Windows
python -c "import machineid; print(machineid.id())"

# Физический компьютер
python -c "import machineid; print(machineid.id())"
```

### 3. Тестирование уникальности

- Запустите на нескольких компьютерах
- Убедитесь, что Machine ID разные
- Проверьте, что на одном компьютере ID стабильный

## Дополнительная информация

### Как py-machineid получает ID на Windows

1. Читает реестр: `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography\MachineGuid`
2. Этот GUID генерируется при установке Windows
3. Уникален для каждой установки (даже на одном железе)
4. Не меняется при обновлениях Windows

### Как py-machineid получает ID на Linux

1. Читает `/etc/machine-id` (systemd)
2. Или `/var/lib/dbus/machine-id` (fallback)
3. Генерируется при установке системы
4. Уникален для каждой установки

## Заключение

Переход на `py-machineid`:
- ✅ Решает проблему одинаковых Machine ID
- ✅ Упрощает код (меньше зависимостей от системных команд)
- ✅ Повышает надежность (работает без прав администратора)
- ✅ Улучшает кросс-платформенность
- ⚠️ Требует переактивации существующих лицензий

## Ссылки

- [py-machineid на GitHub](https://github.com/keygen-sh/py-machineid)
- [py-machineid на PyPI](https://pypi.org/project/py-machineid/)
- [Документация по лицензированию проекта](./LICENSING_ARCHITECTURE.md)

