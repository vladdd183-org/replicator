"""User module Unit of Work."""

from dataclasses import dataclass, field
from typing import Callable, Any

from src.Ship.Parents.UnitOfWork import BaseUnitOfWork, EventEmitterFunc
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository


@dataclass
class UserUnitOfWork(BaseUnitOfWork):
    """Unit of Work for UserModule.
    
    Provides transactional access to user-related repositories.
    Inherits event management from BaseUnitOfWork.
    
    The _emit parameter is inherited from BaseUnitOfWork and injected via DI.
    
    Example:
        async with uow:
            user = User(email=data.email, ...)
            await uow.users.add(user)
            uow.add_event(UserCreated(user_id=user.id))
            await uow.commit()  # Events published here
    """
    
    # Repositories - initialized with default_factory for proper per-instance creation
    users: UserRepository = field(default_factory=UserRepository)
