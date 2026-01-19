"""AuditModule - Логирование и аудит действий пользователей.

Демонстрирует:
- Decorator-based автоматическое логирование
- Middleware для HTTP запросов
- Хранение истории изменений
- Event-driven архитектуру
"""

from src.Containers.AppSection.AuditModule.UI.API.Routes import audit_router

__all__ = ["audit_router"]



