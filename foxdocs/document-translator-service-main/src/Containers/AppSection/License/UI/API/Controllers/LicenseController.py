"""
License Controller

HTTP контроллер для получения информации о лицензии через веб-интерфейс.
"""

from litestar import Controller, get
from litestar.status_codes import HTTP_200_OK
import logfire

from src.Containers.AppSection.License.Data.LicenseSchemas import (
    LicenseInfoResponse,
)
from src.Ship.Licensing import check_license
from src.Ship.Licensing.machine_id import get_machine_id


class LicenseController(Controller):
    """
    Контроллер для работы с информацией о лицензии.
    
    Предоставляет HTTP API для получения информации о лицензии через веб-интерфейс.
    Напрямую проверяет лицензию на сервере без использования helper service.
    """
    
    path = "/api/license"
    tags = ["License"]
    
    @get("/info", summary="Информация о лицензии", status_code=HTTP_200_OK)
    async def get_license_info(self) -> LicenseInfoResponse:
        """
        Получение информации о лицензии для веб-интерфейса.
        
        Использует интегрированный механизм check_license() который:
        1. Получает machine_id локально
        2. Проверяет лицензию на сервере напрямую
        3. Проверяет RSA подпись от сервера
        4. Возвращает информацию о лицензии
        
        Returns:
            LicenseInfoResponse: Информация о лицензии
        """
        try:
            logfire.info("License info request from web UI")
            
            # Используем интегрированный механизм проверки
            license_data = await check_license()
            
            logfire.info(
                "License info retrieved successfully",
                status=license_data.get("status"),
                cached=license_data.get("cached", False)
            )
            
            return LicenseInfoResponse(
                status=license_data.get("status", "unknown"),
                machine_id=license_data.get("machine_id"),
                expires_at=license_data.get("expires_at"),
                message="License is valid" if license_data.get("status") == "valid" else None,
                cached=license_data.get("cached", False)
            )
            
        except Exception as e:
            # Если check_license() выбросил исключение - значит проблема с лицензией
            logfire.error("License check failed", error=str(e), error_type=type(e).__name__)
            
            # Пытаемся получить machine_id для отображения
            try:
                machine_id = get_machine_id()
            except:
                machine_id = None
            
            # Возвращаем информативный ответ вместо ошибки HTTP
            return LicenseInfoResponse(
                status="error",
                machine_id=machine_id,
                expires_at=None,
                message=str(e),
                cached=False
            )
    
    @get("/machine-id", summary="Получить Machine ID", status_code=HTTP_200_OK)
    async def get_machine_id_info(self) -> dict:
        """
        Получение machine_id для регистрации/покупки лицензии.
        
        Клиент использует этот endpoint чтобы узнать свой Machine ID
        и зарегистрировать лицензию на сервере.
        
        Returns:
            dict: {"machine_id": "...", "message": "..."}
        """
        try:
            logfire.info("Machine ID request from web UI")
            
            machine_id = get_machine_id()
            
            logfire.info(f"Machine ID retrieved: {machine_id[:16]}...")
            
            return {
                "machine_id": machine_id,
                "message": "Use this Machine ID to register your license"
            }
            
        except Exception as e:
            logfire.error(f"Failed to get machine ID: {e}")
            return {
                "machine_id": None,
                "message": f"Error: {str(e)}"
            }


__all__ = ["LicenseController"]

