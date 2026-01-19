"""CreateUserAction - Use case for creating new users."""

import anyio
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Ship.Decorators import audited  # ← Ship Layer decorator
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Errors import UserError, UserAlreadyExistsError
from src.Containers.AppSection.UserModule.Events import UserCreated
from src.Containers.AppSection.UserModule.Models.User import AppUser
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask


@audited(action="create", entity_type="User")
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    """Use Case: Create a new user.
    
    Steps:
    1. Check if email already exists
    2. Hash password
    3. Create user entity
    4. Save to database
    5. Publish UserCreated event
    
    Example:
        action = CreateUserAction(hash_password, uow)
        result = await action.run(CreateUserRequest(
            email="user@example.com",
            password="password123",
            name="John Doe",
        ))
    """
    
    def __init__(
        self,
        hash_password: HashPasswordTask,
        uow: UserUnitOfWork,
    ) -> None:
        """Initialize action with dependencies.
        
        Args:
            hash_password: Task for hashing passwords
            uow: Unit of Work for data operations
        """
        self.hash_password = hash_password
        self.uow = uow
    
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        """Execute the create user use case.
        
        Args:
            data: CreateUserRequest with user data
            
        Returns:
            Result[AppUser, UserError]: Success with created user or Failure with error
        """
        # Step 1: Check if email already exists
        # Note: validation is handled by CreateUserRequest Pydantic model
        existing_user = await self.uow.users.find_by_email(data.email)
        if existing_user is not None:
            return Failure(UserAlreadyExistsError(email=data.email))
        
        # Step 2: Hash password (offload to thread to avoid blocking event loop)
        password_hash = await anyio.to_thread.run_sync(self.hash_password.run, data.password)
        
        # Step 3: Create user entity
        user = AppUser(
            email=data.email,
            password_hash=password_hash,
            name=data.name,
        )
        
        # Step 4-5: Save to database and publish event
        async with self.uow:
            await self.uow.users.add(user)
            
            # Add domain event (published after commit)
            self.uow.add_event(UserCreated(
                user_id=user.id,
                email=user.email,
                name=user.name,
            ))
            
            await self.uow.commit()
        
        return Success(user)
