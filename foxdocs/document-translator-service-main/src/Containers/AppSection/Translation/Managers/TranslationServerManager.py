"""
Translation Server Manager для экспорта функциональности перевода в другие контейнеры.

Предоставляет централизованный доступ к операциям перевода текста.
"""

from typing import List, Optional
from dishka import FromDishka

from ..Actions import TranslateAction
from ..Data import (
    TranslationRequest,
    TranslationResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    TranslationStatus,
    SupportedLanguage,
)
from src.Ship.Parents import ServerManager


class TranslationServerManager(ServerManager[TranslationResponse]):
    """
    Server Manager для Translation контейнера.
    
    Предоставляет унифицированный интерфейс для:
    - Перевода одного текста
    - Пакетного перевода множества текстов
    - Получения статуса системы перевода
    
    Используется другими контейнерами для доступа к функциональности перевода.
    """
    
    def __init__(
        self,
        translate_action: FromDishka[TranslateAction],
    ):
        """
        Инициализация с Translation action.
        
        Args:
            translate_action: Action для выполнения операций перевода
        """
        self.translate_action = translate_action
    
    async def translate_text(
        self, 
        text: str, 
        from_language: SupportedLanguage, 
        to_language: SupportedLanguage
    ) -> TranslationResponse:
        """
        Перевести один текст.
        
        Args:
            text: Текст для перевода
            from_language: Исходный язык
            to_language: Целевой язык
            
        Returns:
            TranslationResponse: Результат перевода
            
        Raises:
            TranslationServiceNotInitializedException: Сервис не инициализирован
            UnsupportedLanguagePairException: Неподдерживаемая языковая пара
            EmptyTextException: Пустой текст
            TranslationFailedException: Ошибка перевода
        """
        request = TranslationRequest(
            text=text,
            from_language=from_language,
            to_language=to_language
        )
        return await self.translate_action.translate_text(request)
    
    async def translate_batch(
        self, 
        texts: List[str], 
        from_language: SupportedLanguage, 
        to_language: SupportedLanguage
    ) -> BatchTranslationResponse:
        """
        Перевести множество текстов.
        
        Args:
            texts: Список текстов для перевода
            from_language: Исходный язык
            to_language: Целевой язык
            
        Returns:
            BatchTranslationResponse: Результаты переводов
            
        Raises:
            TranslationServiceNotInitializedException: Сервис не инициализирован
            UnsupportedLanguagePairException: Неподдерживаемая языковая пара
        """
        request = BatchTranslationRequest(
            texts=texts,
            from_language=from_language,
            to_language=to_language
        )
        return await self.translate_action.translate_batch(request)
    
    async def get_status(self) -> TranslationStatus:
        """
        Получить статус системы перевода.
        
        Returns:
            TranslationStatus: Информация о доступных пакетах и маршрутах
        """
        return await self.translate_action.get_status()
    
    # Реализация абстрактных методов базового класса (для совместимости)
    async def get(self, id) -> Optional[TranslationResponse]:
        """
        Метод для совместимости с базовым интерфейсом.
        В Translation контексте не используется.
        """
        return None
    
    async def list(self, **filters) -> List[TranslationResponse]:
        """
        Метод для совместимости с базовым интерфейсом.
        В Translation контексте не используется.
        """
        return []
    
    # Дополнительные удобные методы
    async def translate_chinese_to_russian(self, text: str) -> str:
        """
        Быстрый перевод с китайского на русский.
        
        Args:
            text: Китайский текст
            
        Returns:
            str: Переведённый русский текст
        """
        result = await self.translate_text(
            text=text,
            from_language=SupportedLanguage.CHINESE,
            to_language=SupportedLanguage.RUSSIAN
        )
        return result.translated_text
    
    async def translate_texts_chinese_to_russian(self, texts: List[str]) -> List[str]:
        """
        Быстрый пакетный перевод с китайского на русский.
        
        Args:
            texts: Список китайских текстов
            
        Returns:
            List[str]: Список переведённых русских текстов
        """
        result = await self.translate_batch(
            texts=texts,
            from_language=SupportedLanguage.CHINESE,
            to_language=SupportedLanguage.RUSSIAN
        )
        return [translation.translated_text for translation in result.translations]
    
    async def is_translation_available(
        self, 
        from_language: SupportedLanguage, 
        to_language: SupportedLanguage
    ) -> bool:
        """
        Проверить доступность перевода для языковой пары.
        
        Args:
            from_language: Исходный язык
            to_language: Целевой язык
            
        Returns:
            bool: True если перевод доступен
        """
        try:
            status = await self.get_status()
            route_key = f"{from_language.value}->{to_language.value}"
            return route_key in status.supported_routes
        except Exception:
            return False


__all__ = ["TranslationServerManager"]




