"""
Machine ID Helper
Получение уникального ID машины для проверки лицензии

Использует библиотеку py-machineid для надежного получения уникального
идентификатора машины без прав администратора.
"""

import hashlib
import logfire

try:
    import machineid
except ImportError:
    # Fallback если py-machineid не установлен
    machineid = None
    import platform
    import uuid as uuid_module


def get_machine_id() -> str:
    """
    Получение уникального ID машины (Windows/Linux/macOS)
    
    Использует py-machineid библиотеку, которая:
    - Работает без прав администратора
    - Использует надежные системные идентификаторы:
      * Windows: MachineGuid из реестра
      * Linux: /etc/machine-id или /var/lib/dbus/machine-id
      * macOS: IOPlatformUUID
    - Возвращает стабильный ID который не меняется при обновлениях ОС
    
    Returns:
        str: SHA256 хеш от уникального ID машины
        
    Raises:
        Exception: Если не удается получить machine ID
    """
    try:
        if machineid is not None:
            # Используем py-machineid - более надежный способ
            # hashed_id() возвращает SHA256 хеш от machine ID
            # передаем app_id для дополнительной уникальности
            machine_id = machineid.hashed_id('document-translator-service')
            logfire.info(f"Machine ID calculated (py-machineid): {machine_id[:16]}...")
            return machine_id
        else:
            # Fallback: если py-machineid не установлен
            # Используем комбинацию hostname + MAC адреса
            logfire.warn("py-machineid not installed, using fallback method")
            hostname = platform.node()
            mac = _get_mac_address()
            combined = f"{hostname}:{mac}"
            machine_id = hashlib.sha256(combined.encode()).hexdigest()
            logfire.info(f"Machine ID calculated (fallback): {machine_id[:16]}...")
            return machine_id
        
    except Exception as e:
        logfire.error(f"Failed to get machine ID: {e}")
        raise Exception(f"Cannot get machine ID: {str(e)}")


def _get_mac_address() -> str:
    """
    Получение MAC адреса как fallback
    
    Returns:
        str: MAC адрес в формате aa:bb:cc:dd:ee:ff
    """
    mac = ':'.join(['{:02x}'.format((uuid_module.getnode() >> elements) & 0xff)
                    for elements in range(0, 2*6, 2)][::-1])
    return mac


# Для обратной совместимости
def get_mac_address() -> str:
    """
    Получение MAC адреса (deprecated, используется только как fallback)
    
    Returns:
        str: MAC адрес в формате aa:bb:cc:dd:ee:ff
    """
    return _get_mac_address()


__all__ = ["get_machine_id", "get_mac_address"]

