"""
Translation Exceptions

Исключения для работы с переводом текста.
"""

from src.Ship.Parents import PortoException


class TranslationException(PortoException):
    """Базовое исключение для операций перевода."""
    pass


class TranslationServiceNotInitializedException(TranslationException):
    """Исключение при попытке использования неинициализированного сервиса перевода."""
    
    def __init__(self, message: str = "Translation service is not initialized"):
        super().__init__(message)


class LanguagePackageNotInstalledException(TranslationException):
    """Исключение при отсутствии необходимого языкового пакета."""
    
    def __init__(self, from_lang: str, to_lang: str):
        message = f"Language package for {from_lang} -> {to_lang} is not installed"
        super().__init__(message)
        self.from_lang = from_lang
        self.to_lang = to_lang


class UnsupportedLanguagePairException(TranslationException):
    """Исключение при попытке перевода между неподдерживаемыми языками."""
    
    def __init__(self, from_lang: str, to_lang: str):
        message = f"Translation from {from_lang} to {to_lang} is not supported"
        super().__init__(message)
        self.from_lang = from_lang
        self.to_lang = to_lang


class TranslationFailedException(TranslationException):
    """Исключение при неудачном переводе."""
    
    def __init__(self, text: str, from_lang: str, to_lang: str, error: str):
        message = f"Failed to translate text from {from_lang} to {to_lang}: {error}"
        super().__init__(message)
        self.text = text
        self.from_lang = from_lang
        self.to_lang = to_lang
        self.error = error


class PackageDownloadException(TranslationException):
    """Исключение при ошибке скачивания языкового пакета."""
    
    def __init__(self, package_name: str, error: str):
        message = f"Failed to download package {package_name}: {error}"
        super().__init__(message)
        self.package_name = package_name
        self.error = error


class PackageInstallationException(TranslationException):
    """Исключение при ошибке установки языкового пакета."""
    
    def __init__(self, package_name: str, error: str):
        message = f"Failed to install package {package_name}: {error}"
        super().__init__(message)
        self.package_name = package_name
        self.error = error


class EmptyTextException(TranslationException):
    """Исключение при попытке перевода пустого текста."""
    
    def __init__(self, message: str = "Cannot translate empty text"):
        super().__init__(message)


__all__ = [
    "TranslationException",
    "TranslationServiceNotInitializedException", 
    "LanguagePackageNotInstalledException",
    "UnsupportedLanguagePairException",
    "TranslationFailedException",
    "PackageDownloadException",
    "PackageInstallationException",
    "EmptyTextException",
]




