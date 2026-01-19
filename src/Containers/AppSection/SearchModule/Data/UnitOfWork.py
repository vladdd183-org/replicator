"""Search module Unit of Work."""

from dataclasses import dataclass

from src.Ship.Parents.UnitOfWork import BaseUnitOfWork


@dataclass
class SearchUnitOfWork(BaseUnitOfWork):
    """Unit of Work for SearchModule.

    Provides transactional access and event management for search operations.
    Inherits event management from BaseUnitOfWork.

    Note:
        SearchModule doesn't have its own repository since IndexEntityTask
        handles database operations directly on SearchIndex model.
        This UoW is used primarily for domain event publishing.

    Example:
        async with uow:
            success = await index_task.run(entity_data)
            if success:
                uow.add_event(EntityIndexed(...))
            await uow.commit()
    """

    # No repositories needed - IndexEntityTask handles DB operations directly
    # This UoW is used for event publishing and transaction management
    pass
