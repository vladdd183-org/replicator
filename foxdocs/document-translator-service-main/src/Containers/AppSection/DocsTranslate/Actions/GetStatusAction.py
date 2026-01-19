"""
Get Status Action

Action для получения статуса сервиса DocsTranslate.
Один Action = Один Use Case.
"""

import logfire

from src.Ship.Parents.Action import Action
from ..Tasks.GetDocsTranslateStatusTask import GetDocsTranslateStatusTask
from ..Data.DocsTranslateSchemas import DocsTranslateStatus


class GetStatusAction(Action[None, DocsTranslateStatus]):
    """
    Action для получения статуса сервиса DocsTranslate.
    
    Use Case: Пользователь запрашивает информацию о доступности сервиса.
    
    Этот endpoint НЕ требует лицензии (публичный).
    """
    
    # Отключаем проверку лицензии для этого endpoint
    require_license: bool = False
    
    def __init__(self, status_task: GetDocsTranslateStatusTask):
        """
        Инициализация Action.
        
        Args:
            status_task: Task для получения статуса
        """
        self.status_task = status_task
    
    async def run(self, data: None) -> DocsTranslateStatus:
        """
        Получить статус сервиса DocsTranslate.
        
        Args:
            data: Не требуется (None)
            
        Returns:
            DocsTranslateStatus: Статус с информацией о доступности сервисов
        """
        with logfire.span("get_docs_translate_status"):
            status = await self.status_task.run()
            
            logfire.info(
                "DocsTranslate status retrieved",
                service_ready=status.service_ready,
                ocr_available=status.ocr_available,
                translation_available=status.translation_available
            )
            
            return status


__all__ = ["GetStatusAction"]

