"""
License Helper Service
Компилируется в .exe для установки на машине клиента
Один файл для всех клиентов

Компиляция:
    pip install pyinstaller fastapi uvicorn httpx
    pyinstaller --onefile --name license-helper license_helper.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import hashlib
import hmac
import httpx
import time
import sys
import os
import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

app = FastAPI(
    title="License Helper Service",
    description="Сервис проверки лицензий для Document Translator",
    version="1.0.0"
)

# Добавляем CORS для доступа из браузера
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене можно ограничить конкретными доменами
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# КОНФИГУРАЦИЯ (настройте под свой проект)
# ============================================

# ЕДИНЫЙ СЕКРЕТНЫЙ КЛЮЧ - зашит в код (один для всех клиентов)
# ⚠️ ВАЖНО: Этот же ключ должен быть в Docker контейнере!
# После релиза НЕ МЕНЯТЬ - иначе старые версии перестанут работать
EMBEDDED_SECRET = "doc-translator-secret-key-2024-v1-change-me-in-production"

# URL вашего сервера лицензий
# Можно также вынести в конфиг-файл license_config.json
LICENSE_SERVER_URL = "https://license.fatdataseo.com"


# ============================================
# RSA ПУБЛИЧНЫЙ КЛЮЧ
# ============================================

# Публичный ключ для проверки подписей от license server
# ⚠️ ВАЖНО: Получите этот ключ от /public-key endpoint вашего сервера
# и зашейте сюда при сборке .exe
RSA_PUBLIC_KEY_PEM = """
-----BEGIN PUBLIC KEY-----
ЗАМЕНИТЕ_НА_РЕАЛЬНЫЙ_КЛЮЧ_ОТ_ВАШЕГО_СЕРВЕРА
-----END PUBLIC KEY-----
"""

def load_public_key():
    """Загружает публичный RSA ключ для проверки подписей"""
    try:
        # Если ключ не установлен - пытаемся получить с сервера
        if "ЗАМЕНИТЕ" in RSA_PUBLIC_KEY_PEM:
            print("[WARN] Public key not configured, fetching from server...")
            import httpx
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{LICENSE_SERVER_URL}/public-key")
                if response.status_code == 200:
                    pem_data = response.json()["public_key"]
                    public_key = serialization.load_pem_public_key(
                        pem_data.encode(),
                        backend=default_backend()
                    )
                    print("[INFO] Fetched public key from server")
                    return public_key
                else:
                    raise Exception("Cannot fetch public key from server")
        
        # Загружаем зашитый ключ
        public_key = serialization.load_pem_public_key(
            RSA_PUBLIC_KEY_PEM.encode(),
            backend=default_backend()
        )
        return public_key
    except Exception as e:
        print(f"[ERROR] Failed to load public key: {e}")
        raise

# Загружаем публичный ключ при старте
try:
    RSA_PUBLIC_KEY = load_public_key()
    print("[INFO] RSA public key loaded successfully")
except:
    RSA_PUBLIC_KEY = None
    print("[WARN] RSA public key not loaded - signature verification disabled")

# ============================================
# ФУНКЦИИ ПОЛУЧЕНИЯ MACHINE ID
# ============================================

# Импортируем py-machineid для надежного получения machine ID
try:
    import machineid
    HAS_MACHINEID = True
except ImportError:
    HAS_MACHINEID = False
    import platform


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
    """
    try:
        if HAS_MACHINEID:
            # Используем py-machineid - более надежный способ
            # hashed_id() возвращает SHA256 хеш от machine ID
            # передаем app_id для дополнительной уникальности
            machine_id = machineid.hashed_id('document-translator-service')
            print(f"[INFO] Machine ID calculated (py-machineid): {machine_id[:16]}...")
            return machine_id
        else:
            # Fallback: если py-machineid не установлен
            # Используем комбинацию hostname + MAC адреса
            print("[WARN] py-machineid not installed, using fallback method")
            hostname = platform.node()
            mac = get_mac_address()
            combined = f"{hostname}:{mac}"
            machine_id = hashlib.sha256(combined.encode()).hexdigest()
            print(f"[INFO] Machine ID calculated (fallback): {machine_id[:16]}...")
            return machine_id
        
    except Exception as e:
        print(f"[ERROR] Failed to get machine ID: {e}")
        raise Exception(f"Cannot get machine ID: {str(e)}")


def get_mac_address() -> str:
    """
    Получение MAC адреса как fallback
    
    Returns:
        str: MAC адрес в формате aa:bb:cc:dd:ee:ff
    """
    import uuid
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                    for elements in range(0, 2*6, 2)][::-1])
    return mac


# ============================================
# API ENDPOINTS
# ============================================

class ValidateRequest(BaseModel):
    challenge: str  # HMAC подпись от Docker контейнера
    timestamp: str  # Unix timestamp

    class Config:
        json_schema_extra = {
            "example": {
                "challenge": "abc123...",
                "timestamp": "1234567890"
            }
        }


@app.post("/validate")
async def validate_license(req: ValidateRequest):
    """
    Основной endpoint для проверки лицензии
    
    Процесс:
    1. Проверяет challenge от Docker контейнера
    2. Получает machine_id текущей машины
    3. Отправляет запрос на сервер лицензий
    4. Возвращает результат с HMAC подписью
    
    Returns:
        dict: Статус лицензии с подписью
    """
    
    # 1. Проверка timestamp (защита от replay атак)
    current_time = int(time.time())
    try:
        request_time = int(req.timestamp)
        time_diff = abs(current_time - request_time)
        
        if time_diff > 30:  # 30 секунд окно
            print(f"[WARN] Timestamp too old: {time_diff}s difference")
            return {
                "status": "error",
                "message": "Request expired (timestamp too old)",
                "code": "TIMESTAMP_INVALID"
            }
    except ValueError:
        print(f"[WARN] Invalid timestamp format: {req.timestamp}")
        return {
            "status": "error",
            "message": "Invalid timestamp format",
            "code": "TIMESTAMP_INVALID"
        }
    
    # 2. Проверка challenge (Docker должен знать наш секрет)
    expected_challenge = hmac.new(
        EMBEDDED_SECRET.encode(),
        req.timestamp.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(req.challenge, expected_challenge):
        print("[WARN] Invalid challenge signature")
        return {
            "status": "error",
            "message": "Invalid challenge signature - Docker image may be corrupted",
            "code": "AUTH_FAILED"
        }
    
    # 3. Получаем machine_id
    try:
        machine_id = get_machine_id()
    except Exception as e:
        print(f"[ERROR] Cannot get machine ID: {e}")
        return {
            "status": "error",
            "message": f"Cannot get machine ID: {str(e)}",
            "code": "MACHINE_ID_ERROR"
        }
    
    # 4. Проверяем лицензию на сервере
    try:
        # Создаем подпись для запроса к license server
        message = f"{machine_id}:{req.timestamp}"
        signature = hmac.new(
            EMBEDDED_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        print(f"[INFO] Validating license on server: {LICENSE_SERVER_URL}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{LICENSE_SERVER_URL}/api/validate",
                json={
                    "machine_id": machine_id,
                    "timestamp": req.timestamp,
                    "signature": signature
                }
            )
            
            if response.status_code == 200:
                license_data = response.json()
                print(f"[SUCCESS] License valid until: {license_data.get('expires_at')}")
                
                # ========================================
                # ПРОВЕРКА RSA ПОДПИСИ ОТ СЕРВЕРА
                # ========================================
                
                if RSA_PUBLIC_KEY:
                    try:
                        # Получаем подпись из ответа
                        server_signature = base64.b64decode(license_data.get("signature", ""))
                        
                        # Создаем ту же строку которую подписал сервер
                        sign_data = f"{license_data['status']}:{license_data['machine_id']}:{license_data['timestamp']}:{license_data['nonce']}"
                        
                        # Проверяем RSA подпись
                        RSA_PUBLIC_KEY.verify(
                            server_signature,
                            sign_data.encode(),
                            padding.PSS(
                                mgf=padding.MGF1(hashes.SHA256()),
                                salt_length=padding.PSS.MAX_LENGTH
                            ),
                            hashes.SHA256()
                        )
                        
                        print("[SUCCESS] RSA signature verified ✓")
                        
                    except Exception as e:
                        print(f"[ERROR] RSA signature verification FAILED: {e}")
                        return {
                            "status": "error",
                            "message": "Invalid signature from license server",
                            "machine_id": machine_id,
                            "code": "SIGNATURE_INVALID"
                        }
                else:
                    print("[WARN] RSA signature verification skipped - no public key")
                
                # Создаем HMAC подпись ответа для Docker контейнера
                response_message = f"{license_data['status']}:{req.timestamp}:{license_data.get('nonce', '')}"
                response_signature = hmac.new(
                    EMBEDDED_SECRET.encode(),
                    response_message.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                return {
                    "status": license_data["status"],
                    "message": license_data.get("message", "License is valid"),
                    "expires_at": license_data.get("expires_at"),
                    "machine_id": machine_id,
                    "nonce": license_data.get("nonce"),
                    "signature": response_signature,
                    "timestamp": req.timestamp
                }
            
            elif response.status_code == 404:
                print(f"[WARN] License not found for machine: {machine_id[:16]}...")
                return {
                    "status": "no_license",
                    "message": f"Лицензия не найдена для Machine ID: {machine_id}",
                    "machine_id": machine_id,
                    "code": "NO_LICENSE"
                }
            
            elif response.status_code == 403:
                license_error = response.json()
                print(f"[WARN] License expired or invalid")
                return {
                    "status": "no_license",
                    "message": license_error.get("message", "License expired or invalid"),
                    "machine_id": machine_id,
                    "code": "LICENSE_EXPIRED"
                }
            
            else:
                error_text = response.text
                print(f"[ERROR] License server error: {response.status_code} - {error_text}")
                return {
                    "status": "error",
                    "message": f"License server returned error: {response.status_code}",
                    "machine_id": machine_id,
                    "code": "SERVER_ERROR"
                }
                
    except (httpx.TimeoutException, httpx.ReadTimeout, httpx.ConnectTimeout):
        print("[ERROR] License server timeout - no internet connection")
        return {
            "status": "error",
            "message": "Сервис запущен, но не имеет выхода в интернет",
            "machine_id": machine_id,
            "code": "NO_INTERNET"
        }
    
    except httpx.ConnectError as e:
        print(f"[ERROR] Cannot connect to license server: {e}")
        return {
            "status": "error",
            "message": f"Не удается подключиться к серверу лицензий: {LICENSE_SERVER_URL}",
            "machine_id": machine_id,
            "code": "CONNECTION_ERROR"
        }
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return {
            "status": "error",
            "message": f"License server error: {str(e)}",
            "machine_id": machine_id,
            "code": "SERVER_ERROR"
        }


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {
        "status": "ok",
        "service": "license-helper",
        "version": "1.0.0",
        "license_server": LICENSE_SERVER_URL
    }


@app.get("/machine-id")
async def get_machine_id_endpoint():
    """
    Получение machine_id для регистрации/покупки лицензии
    
    Клиент использует этот endpoint чтобы узнать свой Machine ID
    и зарегистрировать лицензию на сервере
    """
    try:
        machine_id = get_machine_id()
        return {
            "machine_id": machine_id,
            "message": "Use this Machine ID to register your license"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cannot get machine ID: {str(e)}"
        )


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🔐 License Helper Service v1.0.0")
    print("=" * 60)
    print(f"📡 License Server: {LICENSE_SERVER_URL}")
    print(f"🌐 Local endpoint: http://127.0.0.1:9999")
    print("=" * 60)
    
    try:
        # Тестируем получение machine_id при старте
        machine_id = get_machine_id()
        print(f"✅ Machine ID: {machine_id}")
        print("=" * 60)
    except Exception as e:
        print(f"⚠️  Warning: Cannot get Machine ID: {e}")
        print("=" * 60)
    
    # Запускаем сервер
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=9999,
        log_level="info",
        access_log=True
    )

