"""
Translation Data Schemas

Схемы данных для работы с переводом текста.
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class SupportedLanguage(str, Enum):
    """Поддерживаемые языки для перевода."""
    CHINESE = "zh"
    ENGLISH = "en" 
    RUSSIAN = "ru"


class TranslationRequest(BaseModel):
    """Запрос на перевод текста."""
    
    text: str = Field(..., description="Текст для перевода", min_length=1)
    from_language: SupportedLanguage = Field(..., description="Исходный язык")
    to_language: SupportedLanguage = Field(..., description="Целевой язык")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "text": "你好世界",
                "from_language": "zh",
                "to_language": "ru"
            }
        }


class TranslationResponse(BaseModel):
    """Ответ с переведённым текстом."""
    
    original_text: str = Field(..., description="Исходный текст")
    translated_text: str = Field(..., description="Переведённый текст")
    from_language: SupportedLanguage = Field(..., description="Исходный язык")
    to_language: SupportedLanguage = Field(..., description="Целевой язык")
    intermediate_language: Optional[SupportedLanguage] = Field(
        None, 
        description="Промежуточный язык (если использовался)"
    )
    intermediate_text: Optional[str] = Field(
        None,
        description="Текст на промежуточном языке"
    )
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "original_text": "你好世界",
                "translated_text": "Привет мир",
                "from_language": "zh",
                "to_language": "ru",
                "intermediate_language": "en",
                "intermediate_text": "Hello World"
            }
        }


class BatchTranslationRequest(BaseModel):
    """Запрос на пакетный перевод текстов."""
    
    texts: List[str] = Field(..., description="Список текстов для перевода", min_items=1)
    from_language: SupportedLanguage = Field(..., description="Исходный язык")
    to_language: SupportedLanguage = Field(..., description="Целевой язык")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "texts": ["你好世界", "再见"],
                "from_language": "zh",
                "to_language": "ru"
            }
        }


class BatchTranslationResponse(BaseModel):
    """Ответ с пакетным переводом."""
    
    translations: List[TranslationResponse] = Field(..., description="Список переводов")
    total_count: int = Field(..., description="Общее количество переводов")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "translations": [
                    {
                        "original_text": "你好世界",
                        "translated_text": "Привет мир",
                        "from_language": "zh",
                        "to_language": "ru",
                        "intermediate_language": "en",
                        "intermediate_text": "Hello World"
                    }
                ],
                "total_count": 1
            }
        }


class LanguagePair(BaseModel):
    """Языковая пара для перевода."""
    
    from_code: str = Field(..., description="Код исходного языка")
    to_code: str = Field(..., description="Код целевого языка")
    package_name: str = Field(..., description="Название пакета для перевода")
    is_installed: bool = Field(False, description="Установлен ли пакет")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "from_code": "zh",
                "to_code": "en", 
                "package_name": "translate-zh_en",
                "is_installed": True
            }
        }


class TranslationStatus(BaseModel):
    """Статус системы перевода."""
    
    available_packages: List[LanguagePair] = Field(..., description="Доступные языковые пары")
    supported_routes: List[str] = Field(..., description="Поддерживаемые маршруты перевода")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "available_packages": [
                    {
                        "from_code": "zh",
                        "to_code": "en",
                        "package_name": "translate-zh_en", 
                        "is_installed": True
                    }
                ],
                "supported_routes": ["zh->en->ru", "en->ru"]
            }
        }


__all__ = [
    "SupportedLanguage",
    "TranslationRequest", 
    "TranslationResponse",
    "BatchTranslationRequest",
    "BatchTranslationResponse", 
    "LanguagePair",
    "TranslationStatus",
]




