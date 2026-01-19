"""
Translation Client Manager для доступа к Translation функциональности из DocsTranslate контейнера.

В монолитной архитектуре напрямую использует TranslationServerManager.
В микросервисной архитектуре будет делать HTTP запросы к Translation сервису.
"""

from typing import List, Optional
from src.Containers.AppSection.Translation.Managers import TranslationServerManager
from src.Containers.AppSection.Translation.Data import (
    TranslationResponse,
    BatchTranslationResponse,
    TranslationStatus,
    SupportedLanguage,
)
from src.Ship.Parents import ClientManager


class TranslationClientManager(ClientManager[TranslationResponse]):
    """
    Client Manager для доступа к Translation функциональности из DocsTranslate контейнера.
    
    В текущей монолитной реализации напрямую использует TranslationServerManager.
    При переходе к микросервисам будет заменён на HTTP клиент.
    """
    
    def __init__(self, translation_server_manager: TranslationServerManager):
        """
        Инициализация с Translation server manager.
        
        В микросервисной архитектуре здесь будет HTTP клиент.
        
        Args:
            translation_server_manager: Менеджер Translation сервера
        """
        super().__init__(endpoint="http://translation-service")  # Для будущей микросервисной архитектуры
        self.translation_manager = translation_server_manager
    
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
        """
        return await self.translation_manager.translate_text(text, from_language, to_language)
    
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
        """
        return await self.translation_manager.translate_batch(texts, from_language, to_language)
    
    async def get_status(self) -> TranslationStatus:
        """
        Получить статус системы перевода.
        
        Returns:
            TranslationStatus: Информация о доступных пакетах и маршрутах
        """
        return await self.translation_manager.get_status()
    
    async def translate_chinese_to_russian(self, text: str) -> str:
        """
        Быстрый перевод с китайского на русский.
        
        Args:
            text: Китайский текст
            
        Returns:
            str: Переведённый русский текст
        """
        return await self.translation_manager.translate_chinese_to_russian(text)
    
    async def translate_texts_chinese_to_russian(self, texts: List[str]) -> List[str]:
        """
        Быстрый пакетный перевод с китайского на русский.
        
        Args:
            texts: Список китайских текстов
            
        Returns:
            List[str]: Список переведённых русских текстов
        """
        return await self.translation_manager.translate_texts_chinese_to_russian(texts)
    
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
        return await self.translation_manager.is_translation_available(from_language, to_language)
    
    # Реализация абстрактных методов базового класса
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


__all__ = ["TranslationClientManager"]




