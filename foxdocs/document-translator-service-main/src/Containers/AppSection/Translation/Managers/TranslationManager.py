"""
Translation Manager

Менеджер для взаимодействия с другими контейнерами через Translation функциональность.
"""

from typing import Optional

from src.Ship.Parents import Manager
from src.Containers.AppSection.Translation.Actions.TranslateAction import TranslateAction


class TranslationManager(Manager):
    """
    Менеджер для работы с переводом текста.
    
    Предоставляет интерфейс для других контейнеров для использования
    функциональности перевода.
    """
    
    def __init__(self, action_provider: Optional[TranslateAction] = None):
        """
        Инициализация менеджера.
        
        Args:
            action_provider: Провайдер для получения TranslateAction
        """
        super().__init__()
        self.action_provider = action_provider
    
    async def translate_chinese_to_russian(self, text: str) -> str:
        """
        Перевод с китайского на русский через английский.
        
        Удобный метод для основного случая использования.
        
        Args:
            text: Текст на китайском языке
            
        Returns:
            str: Переведённый текст на русском языке
        """
        if not self.action_provider:
            raise RuntimeError("TranslateAction not provided")
        
        from src.Containers.AppSection.Translation.Data.TranslationSchemas import (
            TranslationRequest,
            SupportedLanguage,
        )
        
        request = TranslationRequest(
            text=text,
            from_language=SupportedLanguage.CHINESE,
            to_language=SupportedLanguage.RUSSIAN
        )
        
        response = await self.action_provider.translate_text(request)
        return response.translated_text
    
    async def translate_english_to_russian(self, text: str) -> str:
        """
        Перевод с английского на русский.
        
        Args:
            text: Текст на английском языке
            
        Returns:
            str: Переведённый текст на русском языке
        """
        if not self.action_provider:
            raise RuntimeError("TranslateAction not provided")
        
        from src.Containers.AppSection.Translation.Data.TranslationSchemas import (
            TranslationRequest,
            SupportedLanguage,
        )
        
        request = TranslationRequest(
            text=text,
            from_language=SupportedLanguage.ENGLISH,
            to_language=SupportedLanguage.RUSSIAN
        )
        
        response = await self.action_provider.translate_text(request)
        return response.translated_text
    
    async def is_translation_available(self) -> bool:
        """
        Проверка доступности сервиса перевода.
        
        Returns:
            bool: True если сервис доступен
        """
        if not self.action_provider:
            return False
        
        try:
            status = await self.action_provider.get_status()
            return len(status.available_packages) > 0
        except Exception:
            return False


__all__ = ["TranslationManager"]




