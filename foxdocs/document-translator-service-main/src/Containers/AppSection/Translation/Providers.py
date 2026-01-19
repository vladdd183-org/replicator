"""
Translation Container Dependency Injection Providers

Конфигурация зависимостей для Translation контейнера.
"""
from dishka import Provider, Scope, provide

from src.Containers.AppSection.Translation.Services.TranslationService import TranslationService
from src.Containers.AppSection.Translation.Managers.TranslationManager import TranslationManager
from src.Containers.AppSection.Translation.Managers.TranslationServerManager import TranslationServerManager
from src.Containers.AppSection.Translation.Tasks.TranslateTextTask import TranslateTextTask
from src.Containers.AppSection.Translation.Tasks.BatchTranslateTask import BatchTranslateTask
from src.Containers.AppSection.Translation.Tasks.GetTranslationStatusTask import GetTranslationStatusTask
from src.Containers.AppSection.Translation.Actions.TranslateAction import TranslateAction
from src.Containers.AppSection.Translation.UI.API.Controllers.TranslationController import TranslationController


class TranslationProvider(Provider):
    """
    DI Provider для Translation контейнера.
    
    Регистрирует все зависимости Translation модуля:
    - Service (основная логика перевода)
    - Manager (для связи с другими контейнерами)
    - Tasks (атомарные операции)
    - Actions (бизнес-логика)
    - Controllers (HTTP endpoints)
    """
    
    scope = Scope.APP
    
    @provide(scope=Scope.APP)
    def provide_translation_service(self) -> TranslationService:
        """
        Предоставляет синглтон сервис перевода.
        
        Инициализируется один раз при старте приложения.
        """
        return TranslationService()
    
    @provide(scope=Scope.APP)
    def provide_translation_manager(self) -> TranslationManager:
        """
        Предоставляет менеджер для связи с другими контейнерами.
        
        Будет настроен позже через action_provider.
        """
        return TranslationManager(action_provider=None)
    
    @provide(scope=Scope.REQUEST)
    def provide_translation_server_manager(
        self,
        translate_action: TranslateAction,
    ) -> TranslationServerManager:
        """
        Предоставляет Translation Server Manager для экспорта функциональности.
        
        Args:
            translate_action: Action для операций перевода
        """
        return TranslationServerManager(
            translate_action=translate_action,
        )
    
    @provide(scope=Scope.REQUEST)
    def provide_translate_text_task(
        self,
        translation_service: TranslationService
    ) -> TranslateTextTask:
        """Предоставляет Task для перевода одного текста."""
        return TranslateTextTask(translation_service)
    
    @provide(scope=Scope.REQUEST)
    def provide_batch_translate_task(
        self,
        translation_service: TranslationService
    ) -> BatchTranslateTask:
        """Предоставляет Task для пакетного перевода."""
        return BatchTranslateTask(translation_service)
    
    @provide(scope=Scope.REQUEST)
    def provide_status_task(
        self,
        translation_service: TranslationService
    ) -> GetTranslationStatusTask:
        """Предоставляет Task для получения статуса системы перевода."""
        return GetTranslationStatusTask(translation_service)
    
    @provide(scope=Scope.REQUEST)
    def provide_translate_action(
        self,
        translate_task: TranslateTextTask,
        batch_translate_task: BatchTranslateTask,
        status_task: GetTranslationStatusTask,
    ) -> TranslateAction:
        """Предоставляет Action для операций перевода."""
        return TranslateAction(
            translate_task=translate_task,
            batch_translate_task=batch_translate_task,
            status_task=status_task,
        )
    
    @provide(scope=Scope.APP)
    def provide_translation_controller(self) -> type[TranslationController]:
        """Предоставляет Controller для Translation endpoints."""
        return TranslationController


__all__ = ["TranslationProvider"]
