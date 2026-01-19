"""SearchModule Tasks.

Atomic operations for search indexing.
"""

from src.Containers.AppSection.SearchModule.Tasks.IndexEntityTask import (
    IndexableEntity,
    IndexEntityTask,
    RemoveFromIndexTask,
)

__all__ = [
    "IndexEntityTask",
    "IndexableEntity",
    "RemoveFromIndexTask",
]
