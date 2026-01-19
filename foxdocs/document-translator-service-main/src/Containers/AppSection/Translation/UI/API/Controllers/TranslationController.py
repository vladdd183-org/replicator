"""
Translation Controller

HTTP контроллер для работы с переводом текста.
"""

from dishka import FromDishka
from dishka.integrations.litestar import inject
from litestar import Controller, post, get
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from litestar.exceptions import HTTPException
import logfire

from src.Containers.AppSection.Translation.Actions.TranslateAction import TranslateAction
from src.Containers.AppSection.Translation.Data.TranslationSchemas import (
    TranslationRequest,
    TranslationResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    TranslationStatus,
)
from src.Containers.AppSection.Translation.Exceptions.TranslationExceptions import (
    TranslationException,
    TranslationServiceNotInitializedException,
    LanguagePackageNotInstalledException,
    UnsupportedLanguagePairException,
    EmptyTextException,
)


class TranslationController(Controller):
    """
    Контроллер для работы с переводом текста.
    
    Предоставляет HTTP API для выполнения операций перевода.
    """
    
    path = "/api/translation"
    tags = ["Translation"]
    
    @post("/translate", summary="Перевод текста", status_code=HTTP_200_OK)
    @inject
    async def translate_text(
        self,
        data: TranslationRequest,
        translate_action: FromDishka[TranslateAction],
    ) -> TranslationResponse:
        """
        Перевод одного текста.
        
        Args:
            data: Запрос на перевод
            translate_action: Action для выполнения перевода
            
        Returns:
            TranslationResponse: Ответ с переведённым текстом
        """
        try:
            logfire.info(
                "Translation request received",
                from_lang=data.from_language.value,
                to_lang=data.to_language.value,
                text_length=len(data.text)
            )
            
            result = await translate_action.translate_text(data)
            
            logfire.info(
                "Translation completed successfully",
                from_lang=data.from_language.value,
                to_lang=data.to_language.value,
                original_length=len(result.original_text),
                translated_length=len(result.translated_text),
                has_intermediate=result.intermediate_text is not None
            )
            
            return result
            
        except EmptyTextException as e:
            logfire.error("Empty text provided for translation", error=str(e))
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Empty text cannot be translated: {str(e)}"
            )
            
        except UnsupportedLanguagePairException as e:
            logfire.error(
                "Unsupported language pair",
                from_lang=e.from_lang,
                to_lang=e.to_lang,
                error=str(e)
            )
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language pair {e.from_lang} -> {e.to_lang}: {str(e)}"
            )
            
        except TranslationServiceNotInitializedException as e:
            logfire.error("Translation service not initialized", error=str(e))
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Translation service is not available: {str(e)}"
            )
            
        except LanguagePackageNotInstalledException as e:
            logfire.error(
                "Language package not installed",
                from_lang=e.from_lang,
                to_lang=e.to_lang,
                error=str(e)
            )
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Required language package {e.from_lang} -> {e.to_lang} is not installed: {str(e)}"
            )
            
        except TranslationException as e:
            logfire.error("Translation error", error=str(e))
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Translation failed: {str(e)}"
            )
            
        except Exception as e:
            logfire.error("Unexpected error during translation", error=str(e), error_type=type(e).__name__)
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: An unexpected error occurred"
            )
    
    @post("/translate/batch", summary="Пакетный перевод текстов", status_code=HTTP_200_OK)
    @inject
    async def translate_batch(
        self,
        data: BatchTranslationRequest,
        translate_action: FromDishka[TranslateAction],
    ) -> BatchTranslationResponse:
        """
        Пакетный перевод множества текстов.
        
        Args:
            data: Запрос на пакетный перевод
            translate_action: Action для выполнения перевода
            
        Returns:
            BatchTranslationResponse: Ответ с переведёнными текстами
        """
        try:
            logfire.info(
                "Batch translation request received",
                from_lang=data.from_language.value,
                to_lang=data.to_language.value,
                texts_count=len(data.texts)
            )
            
            result = await translate_action.translate_batch(data)
            
            logfire.info(
                "Batch translation completed",
                from_lang=data.from_language.value,
                to_lang=data.to_language.value,
                requested_count=len(data.texts),
                completed_count=result.total_count
            )
            
            return result
            
        except TranslationServiceNotInitializedException as e:
            logfire.error("Translation service not initialized", error=str(e))
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Translation service is not available: {str(e)}"
            )
            
        except UnsupportedLanguagePairException as e:
            logfire.error(
                "Unsupported language pair in batch",
                from_lang=e.from_lang,
                to_lang=e.to_lang,
                error=str(e)
            )
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language pair {e.from_lang} -> {e.to_lang}: {str(e)}"
            )
            
        except TranslationException as e:
            logfire.error("Batch translation error", error=str(e))
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Batch translation failed: {str(e)}"
            )
            
        except Exception as e:
            logfire.error("Unexpected error during batch translation", error=str(e), error_type=type(e).__name__)
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: An unexpected error occurred"
            )
    
    @get("/status", summary="Статус системы перевода", status_code=HTTP_200_OK)
    @inject
    async def get_status(
        self,
        translate_action: FromDishka[TranslateAction],
    ) -> TranslationStatus:
        """
        Получение статуса системы перевода.
        
        Args:
            translate_action: Action для получения статуса
            
        Returns:
            TranslationStatus: Статус с информацией о доступных пакетах и маршрутах
        """
        try:
            logfire.info("Translation status request received")
            
            result = await translate_action.get_status()
            
            logfire.info(
                "Translation status retrieved",
                packages_count=len(result.available_packages),
                routes_count=len(result.supported_routes)
            )
            
            return result
            
        except TranslationServiceNotInitializedException as e:
            logfire.error("Translation service not initialized", error=str(e))
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Translation service is not available: {str(e)}"
            )
            
        except Exception as e:
            logfire.error("Unexpected error getting translation status", error=str(e), error_type=type(e).__name__)
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: An unexpected error occurred"
            )


__all__ = ["TranslationController"]
