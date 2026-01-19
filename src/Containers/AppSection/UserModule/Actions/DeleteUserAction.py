"""DeleteUserAction - Use case for deleting users."""

from uuid import UUID

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Errors import UserError, UserNotFoundError
from src.Containers.AppSection.UserModule.Events import UserDeleted


class DeleteUserAction(Action[UUID, None, UserError]):
    """Use Case: Delete user by ID.
    
    Soft-deletes user by deactivating the account.
    For hard delete, modify the implementation.
    
    Returns Result[None, UserError] for compatibility with @result_handler.
    
    Example:
        action = DeleteUserAction(uow)
        result = await action.run(user_id)
        
        match result:
            case Success(None):
                print("User deleted")
            case Failure(UserNotFoundError()):
                print("User not found")
    """
    
    def __init__(self, uow: UserUnitOfWork) -> None:
        """Initialize action with dependencies.
        
        Args:
            uow: Unit of Work for data operations
        """
        self.uow = uow
    
    async def run(self, data: UUID) -> Result[None, UserError]:
        """Execute the delete user use case.
        
        Args:
            data: User UUID to delete
            
        Returns:
            Result[None, UserError]: Success(None) or Failure with error
        """
        user = await self.uow.users.get(data)
        
        if user is None:
            return Failure(UserNotFoundError(user_id=data))
        
        async with self.uow:
            # Soft delete - deactivate user
            await self.uow.users.deactivate(user)
            
            # Add domain event
            self.uow.add_event(UserDeleted(
                user_id=user.id,
                email=user.email,
            ))
            
            await self.uow.commit()
        
        return Success(None)
