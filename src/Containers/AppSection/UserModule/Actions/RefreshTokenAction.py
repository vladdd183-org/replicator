"""RefreshTokenAction - Use case for refreshing JWT tokens."""

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Ship.Auth.JWT import JWTService
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import RefreshTokenRequest
from src.Containers.AppSection.UserModule.Tasks.GenerateTokenTask import (
    GenerateTokenTask,
    GenerateTokenInput,
    TokenPair,
)
from src.Containers.AppSection.UserModule.Errors import (
    UserError,
    InvalidCredentialsError,
    UserInactiveError,
)


class RefreshTokenAction(Action[RefreshTokenRequest, TokenPair, UserError]):
    """Use Case: Refresh JWT tokens using refresh token.
    
    Validates the refresh token and generates a new token pair.
    
    Example:
        action = RefreshTokenAction(jwt_service, uow, generate_token_task)
        result = await action.run(RefreshTokenRequest(
            refresh_token="eyJ...",
        ))
        
        match result:
            case Success(tokens):
                print(f"New access token: {tokens.access_token}")
            case Failure(error):
                print(f"Refresh failed: {error.message}")
    """
    
    def __init__(
        self,
        jwt_service: JWTService,
        uow: UserUnitOfWork,
        generate_token_task: GenerateTokenTask,
    ) -> None:
        """Initialize action with dependencies.
        
        Args:
            jwt_service: JWT service for token verification
            uow: Unit of Work for data operations
            generate_token_task: Task for token generation
        """
        self.jwt_service = jwt_service
        self.uow = uow
        self.generate_token_task = generate_token_task
    
    async def run(self, data: RefreshTokenRequest) -> Result[TokenPair, UserError]:
        """Execute the refresh token use case.
        
        Args:
            data: Request with refresh token
            
        Returns:
            Result[TokenPair, UserError]: Success with new tokens or Failure
        """
        # Verify refresh token
        payload = self.jwt_service.verify_token(data.refresh_token)
        
        if payload is None:
            return Failure(InvalidCredentialsError(
                message="Invalid or expired refresh token"
            ))
        
        # Check token type
        if payload.type != "refresh":
            return Failure(InvalidCredentialsError(
                message="Invalid token type - expected refresh token"
            ))
        
        # Verify user still exists and is active
        user = await self.uow.users.get(payload.sub)
        
        if user is None:
            return Failure(InvalidCredentialsError(
                message="User not found"
            ))
        
        if not user.is_active:
            return Failure(UserInactiveError(user_id=user.id))
        
        # Generate new token pair
        tokens = self.generate_token_task.run(
            GenerateTokenInput(
                user_id=user.id,
                email=user.email,
            )
        )
        
        return Success(tokens)

