"""
License Middleware
Проверяет валидность лицензии напрямую на сервере лицензий
"""

import httpx
import hmac
import hashlib
import time
import base64
from typing import Optional

from litestar import Request, Response
from litestar.middleware import AbstractMiddleware
from litestar.exceptions import NotAuthorizedException
from litestar.datastructures import State
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

import logfire

from .machine_id import get_machine_id


# ============================================
# КОНФИГУРАЦИЯ
# ============================================

# ЕДИНЫЙ СЕКРЕТНЫЙ КЛЮЧ для подписи запросов
EMBEDDED_SECRET = "doc-translator-secret-key-2024-v1-change-me-in-production"

# URL сервера лицензий
LICENSE_SERVER_URL = "https://license.fatdataseo.com"

# RSA публичный ключ для проверки подписей от license server
# ⚠️ ВАЖНО: Получите этот ключ от /public-key endpoint вашего сервера
RSA_PUBLIC_KEY_PEM = """
-----BEGIN PUBLIC KEY-----
ЗАМЕНИТЕ_НА_РЕАЛЬНЫЙ_КЛЮЧ_ОТ_ВАШЕГО_СЕРВЕРА
-----END PUBLIC KEY-----
"""

# ============================================
# RSA KEY LOADER
# ============================================

def load_public_key():
    """Загружает публичный RSA ключ для проверки подписей"""
    try:
        # Если ключ не установлен - пытаемся получить с сервера
        if "ЗАМЕНИТЕ" in RSA_PUBLIC_KEY_PEM:
            logfire.warn("Public key not configured, fetching from server...")
            import httpx
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{LICENSE_SERVER_URL}/public-key")
                if response.status_code == 200:
                    pem_data = response.json()["public_key"]
                    public_key = serialization.load_pem_public_key(
                        pem_data.encode(),
                        backend=default_backend()
                    )
                    logfire.info("Fetched public key from server")
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
        logfire.error(f"Failed to load public key: {e}")
        return None


# Загружаем публичный ключ при старте
RSA_PUBLIC_KEY = load_public_key()
if RSA_PUBLIC_KEY:
    logfire.info("RSA public key loaded successfully")
else:
    logfire.warn("RSA public key not loaded - signature verification disabled")


# ============================================
# LICENSE VALIDATOR (для использования везде)
# ============================================

class LicenseValidator:
    """
    Валидатор лицензий - можно использовать как в middleware, так и в WebSocket handlers
    """
    
    def __init__(self, cache_ttl: int = 0):
        self.cache_ttl = cache_ttl
        self._cached_status: Optional[str] = None
        self._cache_expires_at: float = 0
        self._last_machine_id: Optional[str] = None
    
    async def validate(self) -> dict:
        """
        Проверка лицензии напрямую на сервере
        
        Returns:
            dict: Результат проверки {"status": "valid", ...}
            
        Raises:
            NotAuthorizedException: Если лицензия невалидна
        """
        
        # Проверяем кеш (если лицензия недавно проверялась)
        if self._cached_status == "valid" and time.time() < self._cache_expires_at:
            return {
                "status": "valid", 
                "cached": True,
                "machine_id": self._last_machine_id
            }
        
        # Получаем machine_id
        try:
            machine_id = get_machine_id()
            self._last_machine_id = machine_id
        except Exception as e:
            logfire.error(f"Cannot get machine ID: {e}")
            raise NotAuthorizedException(
                f"❌ Ошибка получения Machine ID: {str(e)}\n\n"
                "Возможные причины:\n"
                "1. Отсутствуют права администратора\n"
                "2. WMIC недоступен в системе (Windows)\n"
                "3. dmidecode не установлен (Linux)\n\n"
                "Попробуйте запустить приложение от имени администратора."
            )
        
        # Генерируем timestamp для запроса
        timestamp = str(int(time.time()))
        
        # Создаем подпись для запроса к license server
        message = f"{machine_id}:{timestamp}"
        signature = hmac.new(
            EMBEDDED_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Запрос к серверу лицензий
        try:
            logfire.info(f"Validating license on server: {LICENSE_SERVER_URL}")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{LICENSE_SERVER_URL}/api/validate",
                    json={
                        "machine_id": machine_id,
                        "timestamp": timestamp,
                        "signature": signature
                    }
                )
                
                if response.status_code == 200:
                    license_data = response.json()
                    
                    # Проверка RSA подписи от сервера
                    if RSA_PUBLIC_KEY:
                        try:
                            server_signature = base64.b64decode(license_data.get("signature", ""))
                            sign_data = f"{license_data['status']}:{license_data['machine_id']}:{license_data['timestamp']}:{license_data['nonce']}"
                            
                            RSA_PUBLIC_KEY.verify(
                                server_signature,
                                sign_data.encode(),
                                padding.PSS(
                                    mgf=padding.MGF1(hashes.SHA256()),
                                    salt_length=padding.PSS.MAX_LENGTH
                                ),
                                hashes.SHA256()
                            )
                            
                            logfire.info("RSA signature verified ✓")
                            
                        except Exception as e:
                            logfire.error(f"RSA signature verification FAILED: {e}")
                            raise NotAuthorizedException(
                                "❌ Invalid signature from license server"
                            )
                    else:
                        logfire.warn("RSA signature verification skipped - no public key")
                    
                    # Обработка успешного ответа
                    result = await self._handle_license_response(license_data)
                    return result
                
                elif response.status_code == 404:
                    logfire.warn(f"License not found for machine: {machine_id[:16]}...")
                    raise NotAuthorizedException(
                        f"❌ Лицензия не найдена\n\n"
                        f"Machine ID: {machine_id}\n\n"
                        f"Для активации:\n"
                        f"1. Перейдите на https://your-site.com/activate\n"
                        f"2. Приобретите лицензию для этого Machine ID\n"
                        f"3. После оплаты лицензия активируется автоматически\n\n"
                        f"Контакты: support@your-site.com"
                    )
                
                elif response.status_code == 403:
                    license_error = response.json()
                    logfire.warn("License expired or invalid")
                    raise NotAuthorizedException(
                        f"❌ {license_error.get('message', 'License expired or invalid')}"
                    )
                
                else:
                    error_text = response.text
                    logfire.error(f"License server error: {response.status_code} - {error_text}")
                    raise NotAuthorizedException(
                        f"❌ Ошибка сервера лицензий: {response.status_code}"
                    )
                    
        except (httpx.TimeoutException, httpx.ReadTimeout, httpx.ConnectTimeout):
            logfire.error("License server timeout - no internet connection")
            raise NotAuthorizedException(
                "❌ Нет подключения к серверу лицензий\n\n"
                "Проверьте подключение к интернету:\n"
                "1. Откройте браузер и проверьте доступ к интернету\n"
                "2. Проверьте настройки firewall\n"
                "3. Убедитесь, что приложение может подключаться к серверу\n\n"
                f"Machine ID: {machine_id}"
            )
        
        except httpx.ConnectError as e:
            logfire.error(f"Cannot connect to license server: {e}")
            raise NotAuthorizedException(
                f"❌ Не удается подключиться к серверу лицензий\n\n"
                f"Сервер: {LICENSE_SERVER_URL}\n"
                f"Проверьте подключение к интернету и настройки firewall."
            )
        
        except NotAuthorizedException:
            # Пробрасываем дальше
            raise
        
        except Exception as e:
            logfire.error(f"Unexpected error during license validation: {e}")
            raise NotAuthorizedException(
                f"❌ Ошибка проверки лицензии: {str(e)}"
            )
    
    async def _handle_license_response(self, data: dict) -> dict:
        """
        Обработка ответа от сервера лицензий
        
        Args:
            data: JSON ответ от license server
            
        Returns:
            dict: Результат валидации
            
        Raises:
            NotAuthorizedException: Если лицензия невалидна
        """
        
        status = data.get("status")
        
        # Лицензия валидна
        if status == "valid":
            # Кешируем успешный результат
            self._cached_status = "valid"
            self._cache_expires_at = time.time() + self.cache_ttl
            
            logfire.info(
                "✅ License valid",
                expires_at=data.get("expires_at"),
                machine_id=self._last_machine_id[:16] + "..." if self._last_machine_id else "N/A"
            )
            
            return {
                "status": "valid",
                "expires_at": data.get("expires_at"),
                "machine_id": self._last_machine_id,
                "nonce": data.get("nonce")
            }
        
        # Неизвестный статус
        else:
            raise NotAuthorizedException(
                f"❌ Unknown license status: {status}"
            )


# Глобальный экземпляр валидатора (singleton pattern)
_license_validator = LicenseValidator()


async def check_license() -> dict:
    """
    Функция-хелпер для проверки лицензии
    Используйте в WebSocket handlers или в любом другом месте
    
    Example:
        @websocket("/ws")
        async def websocket_handler(socket: WebSocket):
            try:
                await check_license()  # Проверяем лицензию
            except NotAuthorizedException as e:
                await socket.close(code=1008, reason=str(e))
                return
            
            # ... обработка WebSocket
    
    Returns:
        dict: Информация о лицензии
        
    Raises:
        NotAuthorizedException: Если лицензия невалидна
    """
    return await _license_validator.validate()


class LicenseMiddleware(AbstractMiddleware):
    """
    Middleware для проверки лицензии перед каждым HTTP запросом
    
    ⚠️ ВАЖНО: Middleware работает только для HTTP запросов!
    Для WebSocket используйте функцию check_license() в handlers
    
    Процесс:
    1. Генерирует challenge (HMAC подпись)
    2. Отправляет запрос к helper service на хосте
    3. Helper service проверяет лицензию на сервере
    4. Проверяет подпись ответа
    5. Пропускает или блокирует запрос
    """
    
    # Пути, которые НЕ требуют проверки лицензии
    EXCLUDED_PATHS = [
        "/health",
        "/api/docs",
        "/openapi.json",
        "/openapi.yaml",
        "/schema",
        "/api/license",  # Информация о лицензии (иначе циклическая зависимость)
    ]
    
    def __init__(self, app):
        """
        Args:
            app: Litestar application
        """
        super().__init__(app)
    
    async def __call__(self, scope, receive, send):
        """Process request through middleware"""
        
        # Пропускаем WebSocket соединения (они проверяются отдельно в handlers)
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Создаем Request для удобства
        request = Request(scope, receive, send)
        
        # Проверяем исключенные пути
        if self._is_excluded_path(request.url.path):
            await self.app(scope, receive, send)
            return
        
        # Проверяем лицензию
        try:
            await check_license()
            await self.app(scope, receive, send)
            
        except NotAuthorizedException as e:
            # Логируем ошибку лицензии
            logfire.warn(
                "❌ License check failed",
                path=request.url.path,
                error=str(e)
            )
            
            # Возвращаем ошибку клиенту
            response = Response(
                content={
                    "detail": str(e),
                    "status_code": 403,
                },
                status_code=403,
                media_type="application/json"
            )
            await response(scope, receive, send)
            
        except Exception as e:
            logfire.error(
                "❌ License middleware error",
                path=request.url.path,
                error=str(e),
                exc_info=True
            )
            
            response = Response(
                content={
                    "detail": "License validation error. Please check license service.",
                    "status_code": 500
                },
                status_code=500,
                media_type="application/json"
            )
            await response(scope, receive, send)
    
    def _is_excluded_path(self, path: str) -> bool:
        """Проверка, нужно ли пропустить путь без проверки лицензии"""
        return any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS)

