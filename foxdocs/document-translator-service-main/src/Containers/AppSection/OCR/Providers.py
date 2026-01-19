"""
OCR Container Dependency Injection Providers

Конфигурация зависимостей для OCR контейнера.
"""
from dishka import Provider, Scope, provide

from src.Containers.AppSection.OCR.Services import OCRService
from src.Containers.AppSection.OCR.Managers import OCREngineManager, OCRServerManager
from src.Containers.AppSection.OCR.Tasks import (
    ValidateImageTask,
    ProcessFullImageTask,
    ProcessPolygonRegionTask,
)
from src.Containers.AppSection.OCR.Actions import (
    ProcessImageAction,
    ProcessPolygonsAction,
)
from src.Containers.AppSection.OCR.UI.API.Controllers import (
    OCRController,
    OCRTestWebSocketListener,
    OCRProcessImageWebSocketListener,
    OCRProcessPolygonsWebSocketListener,
)


class OCRProvider(Provider):
    """
    DI Provider для OCR контейнера.
    
    Регистрирует все зависимости OCR модуля:
    - Service (основная логика OCR)
    - Manager (для связи с другими контейнерами)
    - Tasks (атомарные операции)
    - Actions (бизнес-логика)
    - Controllers (HTTP endpoints)
    """
    
    scope = Scope.APP
    
    @provide(scope=Scope.APP)
    def provide_ocr_service(self) -> OCRService:
        """
        Предоставляет синглтон сервис OCR.
        
        Инициализируется один раз при старте приложения.
        """
        return OCRService()
    
    @provide(scope=Scope.APP)
    def provide_ocr_manager(self, ocr_service: OCRService) -> OCREngineManager:
        """
        Предоставляет менеджер для связи с другими контейнерами.
        
        Args:
            ocr_service: OCR сервис
        """
        return OCREngineManager(action_provider=None)
    
    @provide(scope=Scope.REQUEST)
    def provide_ocr_server_manager(
        self,
        process_image_action: ProcessImageAction,
        process_polygons_action: ProcessPolygonsAction,
    ) -> OCRServerManager:
        """
        Предоставляет OCR Server Manager для экспорта функциональности.
        
        Args:
            process_image_action: Action для обработки изображений
            process_polygons_action: Action для обработки полигонов
        """
        return OCRServerManager(
            process_image_action=process_image_action,
            process_polygons_action=process_polygons_action,
        )
    
    @provide(scope=Scope.REQUEST)
    def provide_validate_image_task(self) -> ValidateImageTask:
        """Предоставляет Task для валидации изображений."""
        return ValidateImageTask()
    
    @provide(scope=Scope.REQUEST)
    def provide_process_full_image_task(
        self,
        ocr_service: OCRService
    ) -> ProcessFullImageTask:
        """Предоставляет Task для обработки полного изображения."""
        return ProcessFullImageTask(ocr_service)
    
    @provide(scope=Scope.REQUEST)
    def provide_process_polygon_task(
        self,
        ocr_service: OCRService
    ) -> ProcessPolygonRegionTask:
        """Предоставляет Task для обработки полигональных областей."""
        return ProcessPolygonRegionTask(ocr_service)
    
    @provide(scope=Scope.REQUEST)
    def provide_process_image_action(
        self,
        validate_task: ValidateImageTask,
        process_task: ProcessFullImageTask,
    ) -> ProcessImageAction:
        """Предоставляет Action для обработки изображений."""
        return ProcessImageAction(
            validate_task=validate_task,
            process_task=process_task,
        )
    
    @provide(scope=Scope.REQUEST)
    def provide_process_polygons_action(
        self,
        validate_task: ValidateImageTask,
        process_polygon_task: ProcessPolygonRegionTask,
    ) -> ProcessPolygonsAction:
        """Предоставляет Action для обработки полигонов."""
        return ProcessPolygonsAction(
            validate_task=validate_task,
            process_polygon_task=process_polygon_task,
        )
    
    @provide(scope=Scope.APP)
    def provide_ocr_controller(self) -> type[OCRController]:
        """Предоставляет Controller для OCR endpoints."""
        return OCRController
    
    @provide(scope=Scope.APP)
    def provide_ocr_test_websocket_listener(self) -> type[OCRTestWebSocketListener]:
        """Предоставляет Test WebSocket Listener для диагностики."""
        return OCRTestWebSocketListener
    
    @provide(scope=Scope.APP)
    def provide_ocr_process_image_websocket_listener(self) -> type[OCRProcessImageWebSocketListener]:
        """Предоставляет WebSocket Listener для обработки изображений."""
        return OCRProcessImageWebSocketListener
    
    @provide(scope=Scope.APP)
    def provide_ocr_process_polygons_websocket_listener(self) -> type[OCRProcessPolygonsWebSocketListener]:
        """Предоставляет WebSocket Listener для обработки полигонов."""
        return OCRProcessPolygonsWebSocketListener
    

__all__ = ["OCRProvider"]
