"""Main Litestar application factory."""

from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.exceptions import NotAuthorizedException
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
import logfire

from src.Containers.AppSection.OCR.UI.API.Controllers import (
    OCRController,
    OCRTestWebSocketListener,
    OCRProcessImageWebSocketListener,
    OCRProcessPolygonsWebSocketListener,
)
from src.Containers.AppSection.Translation.UI.API.Controllers import TranslationController
from src.Containers.AppSection.Translation.UI.API.Controllers import TranslationTestWebSocketListener, TranslationWebSocketListener, BatchTranslationWebSocketListener, TranslationStatusWebSocketListener
from src.Containers.AppSection.DocsTranslate.UI.API.Controllers import (
    DocsTranslateController,
    DocsTranslateTestWebSocketListener,
    DocsTranslateProcessImageWebSocketListener,
    DocsTranslateProcessRegionsWebSocketListener,
    DocsTranslateStatusWebSocketListener,
    # Streaming WebSocket Listeners
    DocsTranslateProcessImageStreamingWebSocketListener,
    DocsTranslateProcessRegionsStreamingWebSocketListener,
)
from src.Containers.AppSection.License.UI.API.Controllers import LicenseController

from src.Containers.AppSection.OCR.Services.OCRService import OCRService
from src.Containers.AppSection.Translation.Services.TranslationService import TranslationService
from src.Ship.Configs import get_settings
from src.Ship.Exceptions import exception_handler, license_exception_handler
from src.Ship.Parents import PortoException
from src.Ship.Plugins import LogfirePlugin
from src.Ship.Providers import get_all_providers


async def initialize_ocr_service(app: Litestar) -> None:
    """
    Инициализация OCR сервиса при старте приложения.
    
    Предварительно загружает модели PaddleOCR для ускорения первых запросов.
    """
    try:
        logfire.info("Starting OCR service initialization...")
        
        # Создаём и инициализируем синглтон OCRService
        ocr_service = OCRService()
        
        # Проверяем успешную инициализацию
        if ocr_service.is_initialized():
            engine_info = ocr_service.get_engine_info()
            logfire.info(
                "OCR service initialized successfully at startup",
                **engine_info
            )
            
            # Сохраняем ссылку на сервис в состоянии приложения для удобства
            app.state.ocr_service = ocr_service
        else:
            logfire.error("OCR service failed to initialize properly")
            
    except Exception as e:
        logfire.error(
            "Failed to initialize OCR service at startup",
            error=str(e),
            error_type=type(e).__name__
        )
        # В зависимости от требований можно либо поднимать исключение,
        # либо продолжать работу без предзагруженной модели
        raise


async def initialize_translation_service(app: Litestar) -> None:
    """
    Инициализация Translation сервиса при старте приложения.
    
    Скачивает и устанавливает необходимые языковые пакеты для перевода.
    """
    try:
        logfire.info("Starting Translation service initialization...")
        
        # Создаём и инициализируем синглтон TranslationService
        translation_service = TranslationService()
        await translation_service.initialize()
        
        # Проверяем успешную инициализацию
        if translation_service.is_initialized():
            status = translation_service.get_status()
            logfire.info(
                "Translation service initialized successfully at startup",
                packages_count=len(status.available_packages),
                routes_count=len(status.supported_routes),
                available_packages=[pkg.package_name for pkg in status.available_packages],
                supported_routes=status.supported_routes
            )
            
            # Сохраняем ссылку на сервис в состоянии приложения для удобства
            app.state.translation_service = translation_service
        else:
            logfire.error("Translation service failed to initialize properly")
            
    except Exception as e:
        logfire.error(
            "Failed to initialize Translation service at startup",
            error=str(e),
            error_type=type(e).__name__
        )
        # В зависимости от требований можно либо поднимать исключение,
        # либо продолжать работу без предзагруженных моделей
        raise


async def cleanup_ocr_service(app: Litestar) -> None:
    """
    Очистка ресурсов OCR сервиса при завершении приложения.
    """
    try:
        logfire.info("Cleaning up OCR service resources...")
        
        # Если нужна какая-то очистка ресурсов OCR сервиса, добавить здесь
        # Пока что PaddleOCR не требует явной очистки ресурсов
        
        if hasattr(app.state, 'ocr_service'):
            delattr(app.state, 'ocr_service')
            
        logfire.info("OCR service cleanup completed")
        
    except Exception as e:
        logfire.error(
            "Error during OCR service cleanup",
            error=str(e),
            error_type=type(e).__name__
        )


async def cleanup_translation_service(app: Litestar) -> None:
    """
    Очистка ресурсов Translation сервиса при завершении приложения.
    """
    try:
        logfire.info("Cleaning up Translation service resources...")
        
        # Argos Translate не требует явной очистки ресурсов
        
        if hasattr(app.state, 'translation_service'):
            delattr(app.state, 'translation_service')
            
        logfire.info("Translation service cleanup completed")
        
    except Exception as e:
        logfire.error(
            "Error during Translation service cleanup",
            error=str(e),
            error_type=type(e).__name__
        )


def create_app() -> Litestar:
    """Create and configure Litestar application."""

    # Get settings
    settings = get_settings()

    # Create DI container
    container = make_async_container(*get_all_providers())

    # Create app
    app = Litestar(
        route_handlers=[
            # AppSection controllers
            OCRController,
            TranslationController,
            DocsTranslateController,
            LicenseController,  # Контроллер для информации о лицензии
            # OCR WebSocket listeners
            OCRTestWebSocketListener,  # Это функция-handler с декоратором
            OCRProcessImageWebSocketListener,  # Это функция-handler с декоратором
            OCRProcessPolygonsWebSocketListener,  # Это функция-handler с декоратором
            # DocsTranslate WebSocket listeners
            DocsTranslateTestWebSocketListener,  # Это функция-handler с декоратором
            DocsTranslateProcessImageWebSocketListener,  # Это функция-handler с декоратором
            DocsTranslateProcessRegionsWebSocketListener,  # Это функция-handler с декоратором
            DocsTranslateStatusWebSocketListener,  # Это функция-handler с декоратором
            # DocsTranslate Streaming WebSocket listeners
            DocsTranslateProcessImageStreamingWebSocketListener,  # Streaming обработка изображения
            DocsTranslateProcessRegionsStreamingWebSocketListener,  # Streaming обработка областей
            # Translation WebSocket listeners
            TranslationTestWebSocketListener,  # Это функция-handler с декоратором
            TranslationWebSocketListener,  # Это функция-handler с декоратором
            BatchTranslationWebSocketListener,  # Это функция-handler с декоратором
            TranslationStatusWebSocketListener,  # Это функция-handler с декоратором
        ],
        exception_handlers={
            PortoException: exception_handler,
            # Обработчик ошибок лицензии для HTTP запросов
            # (для WebSocket используется helper функция)
            NotAuthorizedException: license_exception_handler,
        },
        cors_config=CORSConfig(
            allow_origins=settings.cors_allow_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
        ),
        # Включаем поддержку WebSocket
        websocket_class=None,  # Используем стандартный класс WebSocket
        openapi_config=OpenAPIConfig(
            title=settings.app_name,
            version="0.1.0",
            path="/api/docs",
            render_plugins=[ScalarRenderPlugin()],
            create_examples=True,
        ),
        plugins=[
            LogfirePlugin(
                auto_trace_modules=["src.Containers"],
                min_duration=0.01,
            ),
        ],
        # Добавляем инициализацию сервисов при старте
        on_startup=[initialize_ocr_service, initialize_translation_service],
        on_shutdown=[cleanup_ocr_service, cleanup_translation_service],
        debug=settings.app_debug,
        # Отключаем встроенное логирование Litestar - используем только logfire
        logging_config=None,
    )
    # Expose DI container for WebSocket handlers (no @inject support for request kwarg)
    app.state.di_container = container
    # Setup Dishka
    setup_dishka(container, app)

    return app
