"""ChangePasswordAction - Use case for changing user password."""

from uuid import UUID

import anyio
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import ChangePasswordRequest
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Errors import (
    UserError,
    UserNotFoundError,
    InvalidCredentialsError,
)
from src.Containers.AppSection.UserModule.Events import UserUpdated
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask
from src.Containers.AppSection.UserModule.Tasks.VerifyPasswordTask import (
    VerifyPasswordTask,
    VerifyPasswordInput,
)


class ChangePasswordInput(BaseModel):
    """Input for ChangePasswordAction.
    
    Attributes:
        user_id: UUID of user changing password
        data: Change password request with current and new password
    """
    
    model_config = {"frozen": True}
    
    user_id: UUID
    data: ChangePasswordRequest


class ChangePasswordAction(Action[ChangePasswordInput, None, UserError]):
    """Use Case: Change user password.
    
    Steps:
    1. Find user by ID
    2. Verify current password
    3. Hash new password
    4. Update user
    5. Publish UserUpdated event
    
    Example:
        action = ChangePasswordAction(uow, verify_password, hash_password)
        result = await action.run(ChangePasswordInput(
            user_id=user_id,
            data=ChangePasswordRequest(
                current_password="old_password",
                new_password="new_password",
            ),
        ))
    """
    
    def __init__(
        self,
        uow: UserUnitOfWork,
        verify_password: VerifyPasswordTask,
        hash_password: HashPasswordTask,
    ) -> None:
        """Initialize action with dependencies.
        
        Args:
            uow: Unit of Work for data operations
            verify_password: Task for verifying passwords
            hash_password: Task for hashing passwords
        """
        self.uow = uow
        self.verify_password = verify_password
        self.hash_password = hash_password
    
    async def run(self, request: ChangePasswordInput) -> Result[None, UserError]:
        """Execute the change password use case.
        
        Args:
            request: ChangePasswordInput with user_id and password data
            
        Returns:
            Result[None, UserError]: Success(None) or Failure with error
        """
        # Step 1: Find user
        user = await self.uow.users.get(request.user_id)
        if user is None:
            return Failure(UserNotFoundError(user_id=request.user_id))
        
        # Step 2: Verify current password (offload to thread)
        is_valid = await anyio.to_thread.run_sync(
            self.verify_password.run,
            VerifyPasswordInput(
                password=request.data.current_password,
                password_hash=user.password_hash,
            ),
        )
        
        if not is_valid:
            return Failure(InvalidCredentialsError())
        
        # Step 3: Hash new password (offload to thread)
        new_hash = await anyio.to_thread.run_sync(
            self.hash_password.run,
            request.data.new_password,
        )
        
        # Step 4-5: Update user and publish event
        user.password_hash = new_hash
        
        async with self.uow:
            await self.uow.users.update(user)
            
            self.uow.add_event(UserUpdated(
                user_id=user.id,
                updated_fields=["password_hash"],
            ))
            
            await self.uow.commit()
        
        return Success(None)
