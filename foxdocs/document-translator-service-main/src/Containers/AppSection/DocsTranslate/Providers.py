"""
DocsTranslate Providers

Провайдеры зависимостей для контейнера DocsTranslate.
Регистрирует все компоненты контейнера в DI контейнере.
"""

from dishka import Provider, Scope, provide

# Импорты Actions
from .Actions.ProcessFullImageAction import ProcessFullImageAction
from .Actions.ProcessRegionsAction import ProcessRegionsAction
from .Actions.GetStatusAction import GetStatusAction
# Streaming Actions
from .Actions.StreamingProcessFullImageAction import StreamingProcessFullImageAction
from .Actions.StreamingProcessRegionsAction import StreamingProcessRegionsAction
# Deprecated - для обратной совместимости
from .Actions.ProcessDocumentAction import ProcessDocumentAction

# Импорты Tasks
from .Tasks.ProcessAndTranslateImageTask import ProcessAndTranslateImageTask
from .Tasks.ProcessRegionsAndTranslateTask import ProcessRegionsAndTranslateTask
from .Tasks.GetDocsTranslateStatusTask import GetDocsTranslateStatusTask
# Streaming Tasks
from .Tasks.StreamingProcessAndTranslateTask import StreamingProcessAndTranslateTask
from .Tasks.StreamingProcessRegionsAndTranslateTask import StreamingProcessRegionsAndTranslateTask

# Импорты Managers
from .Managers.OCRClientManager import OCRClientManager
from .Managers.TranslationClientManager import TranslationClientManager

# Импорты зависимостей из других контейнеров
from src.Containers.AppSection.OCR.Managers import OCRServerManager
from src.Containers.AppSection.Translation.Managers import TranslationServerManager

# Импорты Controllers/WebSocket Listeners
from .UI.API.Controllers import (
    DocsTranslateController,
    DocsTranslateTestWebSocketListener,
    DocsTranslateProcessImageWebSocketListener,
    DocsTranslateProcessRegionsWebSocketListener,
    DocsTranslateStatusWebSocketListener,
    # Streaming WebSocket Listeners
    DocsTranslateProcessImageStreamingWebSocketListener,
    DocsTranslateProcessRegionsStreamingWebSocketListener,
)

# Импорты для streaming (нужен OCRService напрямую)
from src.Containers.AppSection.OCR.Services import OCRService


class DocsTranslateProvider(Provider):
    """
    Провайдер зависимостей для DocsTranslate контейнера.
    
    Регистрирует все компоненты согласно Porto архитектуре:
    - Actions (business operations)
    - Tasks (atomic operations) 
    - Managers (inter-container communication)
    """
    
    scope = Scope.REQUEST
    
    # === Client Managers ===
    @provide
    def provide_ocr_client_manager(
        self, 
        ocr_server_manager: OCRServerManager
    ) -> OCRClientManager:
        """Провайдер OCR Client Manager."""
        return OCRClientManager(ocr_server_manager)
    
    @provide
    def provide_translation_client_manager(
        self, 
        translation_server_manager: TranslationServerManager
    ) -> TranslationClientManager:
        """Провайдер Translation Client Manager."""
        return TranslationClientManager(translation_server_manager)
    
    # === Tasks ===
    @provide
    def provide_process_and_translate_image_task(
        self,
        ocr_manager: OCRServerManager,
        translation_manager: TranslationServerManager,
    ) -> ProcessAndTranslateImageTask:
        """Провайдер Task для обработки изображения с переводом."""
        return ProcessAndTranslateImageTask(ocr_manager, translation_manager)
    
    @provide
    def provide_process_regions_and_translate_task(
        self,
        ocr_manager: OCRServerManager,
        translation_manager: TranslationServerManager,
    ) -> ProcessRegionsAndTranslateTask:
        """Провайдер Task для обработки областей с переводом."""
        return ProcessRegionsAndTranslateTask(ocr_manager, translation_manager)
    
    @provide
    def provide_get_docs_translate_status_task(
        self,
        ocr_manager: OCRServerManager,
        translation_manager: TranslationServerManager,
    ) -> GetDocsTranslateStatusTask:
        """Провайдер Task для получения статуса сервиса."""
        return GetDocsTranslateStatusTask(ocr_manager, translation_manager)
    
    # === Actions ===
    @provide
    def provide_process_full_image_action(
        self,
        process_image_task: ProcessAndTranslateImageTask,
    ) -> ProcessFullImageAction:
        """Провайдер Action для обработки полного изображения с переводом."""
        return ProcessFullImageAction(process_image_task)
    
    @provide
    def provide_process_regions_action(
        self,
        process_regions_task: ProcessRegionsAndTranslateTask,
    ) -> ProcessRegionsAction:
        """Провайдер Action для обработки областей изображения с переводом."""
        return ProcessRegionsAction(process_regions_task)
    
    @provide
    def provide_get_status_action(
        self,
        status_task: GetDocsTranslateStatusTask,
    ) -> GetStatusAction:
        """Провайдер Action для получения статуса сервиса."""
        return GetStatusAction(status_task)
    
    # === Streaming Tasks ===
    @provide
    def provide_streaming_process_and_translate_task(
        self,
        ocr_service: OCRService,
        translation_manager: TranslationServerManager,
    ) -> StreamingProcessAndTranslateTask:
        """Провайдер Streaming Task для обработки изображения с переводом."""
        return StreamingProcessAndTranslateTask(ocr_service, translation_manager)
    
    @provide
    def provide_streaming_process_regions_and_translate_task(
        self,
        ocr_service: OCRService,
        translation_manager: TranslationServerManager,
    ) -> StreamingProcessRegionsAndTranslateTask:
        """Провайдер Streaming Task для обработки областей с переводом."""
        return StreamingProcessRegionsAndTranslateTask(ocr_service, translation_manager)
    
    # === Streaming Actions ===
    @provide
    def provide_streaming_process_full_image_action(
        self,
        streaming_task: StreamingProcessAndTranslateTask,
    ) -> StreamingProcessFullImageAction:
        """Провайдер Streaming Action для обработки полного изображения."""
        return StreamingProcessFullImageAction(streaming_task)
    
    @provide
    def provide_streaming_process_regions_action(
        self,
        streaming_task: StreamingProcessRegionsAndTranslateTask,
    ) -> StreamingProcessRegionsAction:
        """Провайдер Streaming Action для обработки областей."""
        return StreamingProcessRegionsAction(streaming_task)
    
    # Deprecated - для обратной совместимости
    @provide
    def provide_process_document_action(
        self,
        process_image_task: ProcessAndTranslateImageTask,
        process_regions_task: ProcessRegionsAndTranslateTask,
        status_task: GetDocsTranslateStatusTask,
    ) -> ProcessDocumentAction:
        """Провайдер главного Action для обработки документов (deprecated)."""
        return ProcessDocumentAction(
            process_image_task,
            process_regions_task,
            status_task
        )

    # === Controllers ===
    @provide(scope=Scope.APP)
    def provide_docs_translate_controller(self) -> type[DocsTranslateController]:
        """Предоставляет Controller для DocsTranslate endpoints."""
        return DocsTranslateController
    
    # === WebSocket Listeners ===
    @provide(scope=Scope.APP)
    def provide_docs_translate_test_websocket_listener(self) -> type[DocsTranslateTestWebSocketListener]:
        """Предоставляет Test WebSocket Listener для диагностики."""
        return DocsTranslateTestWebSocketListener
    
    @provide(scope=Scope.APP)
    def provide_docs_translate_process_image_websocket_listener(self) -> type[DocsTranslateProcessImageWebSocketListener]:
        """Предоставляет WebSocket Listener для обработки изображений с переводом."""
        return DocsTranslateProcessImageWebSocketListener
    
    @provide(scope=Scope.APP)
    def provide_docs_translate_process_regions_websocket_listener(self) -> type[DocsTranslateProcessRegionsWebSocketListener]:
        """Предоставляет WebSocket Listener для обработки полигонов с переводом."""
        return DocsTranslateProcessRegionsWebSocketListener
    
    @provide(scope=Scope.APP)
    def provide_docs_translate_status_websocket_listener(self) -> type[DocsTranslateStatusWebSocketListener]:
        """Предоставляет WebSocket Listener для получения статуса сервиса."""
        return DocsTranslateStatusWebSocketListener
    
    # === Streaming WebSocket Listeners ===
    @provide(scope=Scope.APP)
    def provide_docs_translate_process_image_streaming_websocket_listener(self) -> type[DocsTranslateProcessImageStreamingWebSocketListener]:
        """Предоставляет Streaming WebSocket Listener для обработки изображений."""
        return DocsTranslateProcessImageStreamingWebSocketListener
    
    @provide(scope=Scope.APP)
    def provide_docs_translate_process_regions_streaming_websocket_listener(self) -> type[DocsTranslateProcessRegionsStreamingWebSocketListener]:
        """Предоставляет Streaming WebSocket Listener для обработки областей."""
        return DocsTranslateProcessRegionsStreamingWebSocketListener


__all__ = ["DocsTranslateProvider"]


