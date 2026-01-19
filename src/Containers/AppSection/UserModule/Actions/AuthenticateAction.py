"""AuthenticateAction - Use case for user authentication (login).

Validates credentials and returns JWT tokens.
"""

import anyio
from pydantic import BaseModel

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Tasks.VerifyPasswordTask import (
    VerifyPasswordTask,
    VerifyPasswordInput,
)
from src.Containers.AppSection.UserModule.Tasks.GenerateTokenTask import (
    GenerateTokenTask,
    GenerateTokenInput,
    TokenPair,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import LoginRequest
from src.Containers.AppSection.UserModule.Errors import (
    UserError,
    InvalidCredentialsError,
    UserInactiveError,
)


class AuthResult(BaseModel):
    """Result of successful authentication.
    
    Attributes:
        tokens: JWT token pair
        user_id: Authenticated user ID
        email: Authenticated user email
    """
    
    model_config = {"frozen": True}
    
    tokens: TokenPair
    user_id: str
    email: str


class AuthenticateAction(Action[LoginRequest, AuthResult, UserError]):
    """Use Case: Authenticate user and return JWT tokens.
    
    Validates user credentials (email/password) and generates
    access and refresh tokens on success.
    
    Example:
        action = AuthenticateAction(uow, verify_task, token_task)
        result = await action.run(LoginRequest(
            email="user@example.com",
            password="password123",
        ))
        
        match result:
            case Success(auth):
                print(f"Access token: {auth.tokens.access_token}")
            case Failure(error):
                print(f"Login failed: {error.message}")
    """
    
    def __init__(
        self,
        uow: UserUnitOfWork,
        verify_password_task: VerifyPasswordTask,
        generate_token_task: GenerateTokenTask,
    ) -> None:
        """Initialize action with dependencies.
        
        Args:
            uow: Unit of Work for data operations
            verify_password_task: Task for password verification
            generate_token_task: Task for token generation
        """
        self.uow = uow
        self.verify_password_task = verify_password_task
        self.generate_token_task = generate_token_task
    
    async def run(self, data: LoginRequest) -> Result[AuthResult, UserError]:
        """Execute the authentication use case.
        
        Args:
            data: Login request with email and password
            
        Returns:
            Result[AuthResult, UserError]: Success with tokens or Failure with error
        """
        # Find user by email
        user = await self.uow.users.find_by_email(data.email)
        
        if user is None:
            return Failure(InvalidCredentialsError())
        
        # Verify password (offload to thread to avoid blocking)
        is_valid = await anyio.to_thread.run_sync(
            self.verify_password_task.run,
            VerifyPasswordInput(
                password=data.password,
                password_hash=user.password_hash,
            ),
        )
        
        if not is_valid:
            return Failure(InvalidCredentialsError())
        
        # Check if user is active
        if not user.is_active:
            return Failure(UserInactiveError(user_id=user.id))
        
        # Generate tokens (lightweight CPU operation, no offload needed)
        tokens = self.generate_token_task.run(
            GenerateTokenInput(
                user_id=user.id,
                email=user.email,
            )
        )
        
        return Success(AuthResult(
            tokens=tokens,
            user_id=str(user.id),
            email=user.email,
        ))

