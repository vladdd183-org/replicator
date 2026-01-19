"""SearchModule - Полнотекстовый поиск и индексация.

Демонстрирует:
- Агрегация данных из разных модулей
- Full-text search (виртуальный индекс)
- Faceted search (фильтры и фасеты)
- Event-driven индексация
"""

from src.Containers.AppSection.SearchModule.UI.API.Routes import search_router

__all__ = ["search_router"]



