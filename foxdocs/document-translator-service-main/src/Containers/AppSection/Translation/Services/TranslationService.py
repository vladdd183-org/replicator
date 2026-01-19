"""
Translation Service

Основной сервис для работы с переводом текста с использованием Argos Translate.
Поддерживает перевод с китайского на русский через английский язык.
"""

import asyncio
import threading
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import argostranslate.package
import argostranslate.translate
import logfire

from src.Containers.AppSection.Translation.Data.TranslationSchemas import (
    SupportedLanguage,
    TranslationRequest,
    TranslationResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    LanguagePair,
    TranslationStatus,
)
from src.Containers.AppSection.Translation.Exceptions.TranslationExceptions import (
    TranslationServiceNotInitializedException,
    LanguagePackageNotInstalledException,
    UnsupportedLanguagePairException,
    TranslationFailedException,
    PackageDownloadException,
    PackageInstallationException,
    EmptyTextException,
)


class TranslationService:
    """
    Сервис для работы с переводом текста.
    
    Использует Argos Translate для локального перевода без отправки данных во внешние сервисы.
    Поддерживает прямой перевод и перевод через промежуточный язык.
    """
    
    _instance: Optional['TranslationService'] = None
    _lock = threading.RLock()
    
    def __new__(cls):
        """Создание синглтона."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация сервиса перевода."""
        # Предотвращаем повторную инициализацию
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = False
        self._instance_lock = threading.RLock()
        self._installed_packages: Dict[str, bool] = {}
        self._translation_routes: Dict[str, str] = {}
        
        # Определяем необходимые языковые пары
        self.REQUIRED_PACKAGES = [
            ("zh", "en"),  # Китайский -> Английский
            ("en", "ru"),  # Английский -> Русский
        ]
        
        logfire.info("Translation service created")
    
    def _check_required_packages_exist(self) -> bool:
        """Проверяем наличие всех требуемых пакетов локально."""
        try:
            installed = argostranslate.package.get_installed_packages()
            for from_code, to_code in self.REQUIRED_PACKAGES:
                if not any((pkg.from_code, pkg.to_code) == (from_code, to_code) for pkg in installed):
                    return False
            return True
        except Exception:
            return False
    
    async def initialize(self) -> None:
        """
        Инициализация сервиса перевода.
        
        Проверяет наличие необходимых языковых пакетов и загружает их при необходимости.
        """
        if self._initialized:
            logfire.info("Translation service already initialized")
            return
            
        with self._instance_lock:
            if self._initialized:
                return
                
            try:
                logfire.info("Initializing translation service...")
                
                # Проверяем наличие требуемых пакетов локально
                packages_exist = self._check_required_packages_exist()
                logfire.info("Translation packages availability check", packages_exist=packages_exist)
                
                if packages_exist:
                    logfire.info("All required translation packages already exist locally, skipping download")
                    # Просто сканируем установленные пакеты и настраиваем маршруты
                    self._scan_installed_packages()
                    self._setup_translation_routes()
                else:
                    logfire.info("Some translation packages missing, will download them")
                    
                    # Обновляем индекс пакетов только если нужно скачивать
                    await self._update_package_index()
                    
                    # Устанавливаем необходимые пакеты
                    await self._ensure_required_packages()
                    
                    # Проверяем установленные пакеты
                    self._scan_installed_packages()
                    
                    # Настраиваем маршруты перевода
                    self._setup_translation_routes()
                
                self._initialized = True
                logfire.info("Translation service initialized successfully")
                
            except Exception as e:
                logfire.error(
                    "Failed to initialize translation service",
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
    
    async def _update_package_index(self) -> None:
        """Обновление индекса доступных пакетов."""
        try:
            import os
            # Позволяет пропускать обновление индекса в офлайн-среде
            if os.getenv("ARGOS_SKIP_INDEX_UPDATE", "0") in {"1", "true", "True"}:
                logfire.info("Skipping Argos package index update due to ARGOS_SKIP_INDEX_UPDATE")
                return
            logfire.info("Updating package index...")
            
            # Выполняем в отдельном потоке, так как это блокирующая операция
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                argostranslate.package.update_package_index
            )
            
            logfire.info("Package index updated successfully")
            
        except Exception as e:
            logfire.error("Failed to update package index", error=str(e))
            raise PackageDownloadException("package index", str(e))
    
    async def _ensure_required_packages(self) -> None:
        """Установка необходимых языковых пакетов."""
        for from_code, to_code in self.REQUIRED_PACKAGES:
            await self._install_package_if_needed(from_code, to_code)
    
    async def _install_package_if_needed(self, from_code: str, to_code: str) -> None:
        """
        Установка языкового пакета при необходимости.
        
        Args:
            from_code: Код исходного языка
            to_code: Код целевого языка
        """
        package_key = f"{from_code}-{to_code}"
        
        try:
            # Проверяем, установлен ли уже пакет
            installed_packages = argostranslate.package.get_installed_packages()
            for package in installed_packages:
                if package.from_code == from_code and package.to_code == to_code:
                    logfire.info(f"Package {package_key} already installed")
                    return
            
            logfire.info(f"Installing package {package_key}...")
            
            # Ищем доступный пакет
            loop = asyncio.get_event_loop()
            available_packages = await loop.run_in_executor(
                None,
                argostranslate.package.get_available_packages
            )
            
            package_to_install = None
            for package in available_packages:
                if package.from_code == from_code and package.to_code == to_code:
                    package_to_install = package
                    break
            
            if not package_to_install:
                raise PackageDownloadException(
                    package_key, 
                    f"Package not found in available packages"
                )
            
            # Скачиваем и устанавливаем пакет
            download_path = await loop.run_in_executor(
                None,
                package_to_install.download
            )
            
            await loop.run_in_executor(
                None,
                argostranslate.package.install_from_path,
                download_path
            )
            
            logfire.info(f"Package {package_key} installed successfully")
            
        except Exception as e:
            logfire.error(f"Failed to install package {package_key}", error=str(e))
            raise PackageInstallationException(package_key, str(e))
    
    def _scan_installed_packages(self) -> None:
        """Сканирование установленных пакетов."""
        installed_packages = argostranslate.package.get_installed_packages()
        
        self._installed_packages.clear()
        for package in installed_packages:
            package_key = f"{package.from_code}-{package.to_code}"
            self._installed_packages[package_key] = True
            
        logfire.info(
            "Scanned installed packages", 
            packages=list(self._installed_packages.keys())
        )
    
    def _setup_translation_routes(self) -> None:
        """Настройка маршрутов перевода."""
        self._translation_routes.clear()
        
        # Прямые маршруты
        for package_key in self._installed_packages:
            from_code, to_code = package_key.split("-")
            route_key = f"{from_code}->{to_code}"
            self._translation_routes[route_key] = "direct"
        
        # Маршрут через промежуточный язык (китайский -> английский -> русский)
        if "zh-en" in self._installed_packages and "en-ru" in self._installed_packages:
            self._translation_routes["zh->ru"] = "via_en"
            
        logfire.info(
            "Translation routes configured",
            routes=list(self._translation_routes.keys())
        )
    
    def is_initialized(self) -> bool:
        """Проверка инициализации сервиса."""
        return self._initialized
    
    def get_status(self) -> TranslationStatus:
        """
        Получение статуса сервиса перевода.
        
        Returns:
            TranslationStatus: Статус с информацией о доступных пакетах и маршрутах
        """
        if not self._initialized:
            raise TranslationServiceNotInitializedException()
        
        # Формируем список доступных пакетов
        available_packages = []
        installed_packages = argostranslate.package.get_installed_packages()
        
        for package in installed_packages:
            language_pair = LanguagePair(
                from_code=package.from_code,
                to_code=package.to_code,
                package_name=package.package_path.name if package.package_path else "unknown",
                is_installed=True
            )
            available_packages.append(language_pair)
        
        return TranslationStatus(
            available_packages=available_packages,
            supported_routes=list(self._translation_routes.keys())
        )
    
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        Перевод одного текста.
        
        Args:
            request: Запрос на перевод
            
        Returns:
            TranslationResponse: Ответ с переведённым текстом
        """
        if not self._initialized:
            raise TranslationServiceNotInitializedException()
        
        if not request.text.strip():
            raise EmptyTextException()
        
        try:
            # Определяем маршрут перевода
            route_key = f"{request.from_language.value}->{request.to_language.value}"
            
            if route_key not in self._translation_routes:
                raise UnsupportedLanguagePairException(
                    request.from_language.value,
                    request.to_language.value
                )
            
            route_type = self._translation_routes[route_key]
            
            if route_type == "direct":
                return await self._translate_direct(request)
            elif route_type == "via_en":
                return await self._translate_via_english(request)
            else:
                raise UnsupportedLanguagePairException(
                    request.from_language.value,
                    request.to_language.value
                )
                
        except Exception as e:
            if isinstance(e, (TranslationServiceNotInitializedException, 
                            UnsupportedLanguagePairException, EmptyTextException)):
                raise
            
            logfire.error(
                "Translation failed",
                text=request.text[:100],  # Логируем только первые 100 символов
                from_lang=request.from_language.value,
                to_lang=request.to_language.value,
                error=str(e)
            )
            raise TranslationFailedException(
                request.text,
                request.from_language.value,
                request.to_language.value,
                str(e)
            )
    
    async def _translate_direct(self, request: TranslationRequest) -> TranslationResponse:
        """Прямой перевод между двумя языками."""
        loop = asyncio.get_event_loop()
        
        translated_text = await loop.run_in_executor(
            None,
            argostranslate.translate.translate,
            request.text,
            request.from_language.value,
            request.to_language.value
        )
        
        return TranslationResponse(
            original_text=request.text,
            translated_text=translated_text,
            from_language=request.from_language,
            to_language=request.to_language
        )
    
    async def _translate_via_english(self, request: TranslationRequest) -> TranslationResponse:
        """Перевод через промежуточный английский язык."""
        if request.from_language != SupportedLanguage.CHINESE or request.to_language != SupportedLanguage.RUSSIAN:
            raise UnsupportedLanguagePairException(
                request.from_language.value,
                request.to_language.value
            )
        
        loop = asyncio.get_event_loop()
        
        # Первый этап: китайский -> английский
        intermediate_text = await loop.run_in_executor(
            None,
            argostranslate.translate.translate,
            request.text,
            SupportedLanguage.CHINESE.value,
            SupportedLanguage.ENGLISH.value
        )
        
        # Второй этап: английский -> русский
        final_text = await loop.run_in_executor(
            None,
            argostranslate.translate.translate,
            intermediate_text,
            SupportedLanguage.ENGLISH.value,
            SupportedLanguage.RUSSIAN.value
        )
        
        return TranslationResponse(
            original_text=request.text,
            translated_text=final_text,
            from_language=request.from_language,
            to_language=request.to_language,
            intermediate_language=SupportedLanguage.ENGLISH,
            intermediate_text=intermediate_text
        )
    
    async def translate_batch(self, request: BatchTranslationRequest) -> BatchTranslationResponse:
        """
        Пакетный перевод множества текстов.
        
        Args:
            request: Запрос на пакетный перевод
            
        Returns:
            BatchTranslationResponse: Ответ с переведёнными текстами
        """
        if not self._initialized:
            raise TranslationServiceNotInitializedException()
        
        translations = []
        
        for text in request.texts:
            if text.strip():  # Пропускаем пустые тексты
                translation_request = TranslationRequest(
                    text=text,
                    from_language=request.from_language,
                    to_language=request.to_language
                )
                
                try:
                    translation = await self.translate(translation_request)
                    translations.append(translation)
                except Exception as e:
                    # В пакетном режиме логируем ошибки, но продолжаем обработку
                    logfire.error(
                        "Failed to translate text in batch",
                        text=text[:100],
                        error=str(e)
                    )
                    # Можно добавить "пустой" перевод с ошибкой или пропустить
                    continue
        
        return BatchTranslationResponse(
            translations=translations,
            total_count=len(translations)
        )


__all__ = ["TranslationService"]
