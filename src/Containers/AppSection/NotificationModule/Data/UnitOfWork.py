"""Notification module Unit of Work."""

from dataclasses import dataclass, field

from src.Containers.AppSection.NotificationModule.Data.Repositories.NotificationRepository import (
    NotificationRepository,
)
from src.Ship.Parents.UnitOfWork import BaseUnitOfWork


@dataclass
class NotificationUnitOfWork(BaseUnitOfWork):
    """Unit of Work for NotificationModule.

    Provides transactional access to notification-related repositories.
    Inherits event management from BaseUnitOfWork.

    Example:
        async with uow:
            notification = Notification(...)
            await uow.notifications.add(notification)
            uow.add_event(NotificationCreated(...))
            await uow.commit()
    """

    # Repositories - initialized with default_factory
    notifications: NotificationRepository = field(default_factory=NotificationRepository)
