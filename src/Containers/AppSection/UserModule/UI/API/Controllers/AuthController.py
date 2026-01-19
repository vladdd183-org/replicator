"""Authentication Controller for UserModule.

Handles login, logout, token refresh, and current user endpoints.
Uses DishkaRouter - no need for @inject decorator.
Uses @result_handler for consistent Result -> Response conversion.

Rate Limiting:
    - /login: 10 req/min (prevent brute force)
    - /refresh: 20 req/min (token refresh)
    - /change-password: 5 req/min (sensitive operation)
"""

from dishka.integrations.litestar import FromDishka
from litestar import Controller, Response, get, post
from litestar.status_codes import HTTP_200_OK
from returns.result import Result

from src.Containers.AppSection.UserModule.Actions.AuthenticateAction import (
    AuthenticateAction,
    AuthResult,
)
from src.Containers.AppSection.UserModule.Actions.ChangePasswordAction import (
    ChangePasswordAction,
    ChangePasswordInput,
)
from src.Containers.AppSection.UserModule.Actions.RefreshTokenAction import RefreshTokenAction
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import (
    AuthResponse,
    TokenRefreshResponse,
    UserResponse,
)
from src.Containers.AppSection.UserModule.Errors import UserError, UserNotFoundError
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Tasks.GenerateTokenTask import TokenPair
from src.Ship.Auth.Guards import CurrentUser, auth_guard
from src.Ship.Core.Errors import DomainException
from src.Ship.Decorators.result_handler import result_handler
from src.Ship.Infrastructure.RateLimiting import (
    auth_rate_limit,
    strict_rate_limit,
)

# Note: Error HTTP status codes are now defined directly on error classes
# via http_status attribute - no need for register_error()


class AuthController(Controller):
    """Authentication API endpoints.

    Provides:
    - POST /auth/login - User login
    - GET /auth/me - Get current user (uses Query instead of Action)
    - POST /auth/logout - User logout (client-side)

    Note: @inject is not needed when using DishkaRouter.
    """

    path = "/auth"
    tags = ["Authentication"]

    @post(
        "/login",
        middleware=[auth_rate_limit.middleware],  # 10 req/min - prevent brute force
    )
    @result_handler(AuthResponse, success_status=HTTP_200_OK)
    async def login(
        self,
        data: LoginRequest,
        action: FromDishka[AuthenticateAction],
    ) -> Result[AuthResult, UserError]:
        """Authenticate user and return tokens.

        Rate Limited: 10 requests per minute per IP.
        Returns RateLimit-* headers per IETF specification.

        Args:
            data: Login credentials (email, password)
            action: Authenticate action

        Returns:
            AuthResponse with tokens and user data, or error

        Raises:
            429 Too Many Requests: When rate limit exceeded
        """
        return await action.run(data)

    @get(
        "/me",
        dependencies={"current_user": auth_guard},
    )
    async def get_current_user(
        self,
        current_user: CurrentUser,
        query: FromDishka[GetUserQuery],
    ) -> UserResponse:
        """Get current authenticated user.

        Uses CQRS Query directly instead of Action wrapper.
        Requires valid JWT token in Authorization header.

        Args:
            current_user: Authenticated user from JWT
            query: GetUserQuery for fetching user data

        Returns:
            Current user data
        """
        user = await query.execute(GetUserQueryInput(user_id=current_user.id))

        if user is None:
            raise DomainException(UserNotFoundError(user_id=current_user.id))

        return UserResponse.from_entity(user)

    @post(
        "/change-password",
        dependencies={"current_user": auth_guard},
        middleware=[strict_rate_limit.middleware],  # 3 req/min - sensitive operation
    )
    @result_handler(None, success_status=HTTP_200_OK)
    async def change_password(
        self,
        current_user: CurrentUser,
        data: ChangePasswordRequest,
        action: FromDishka[ChangePasswordAction],
    ) -> Result[None, UserError]:
        """Change current user's password.

        Rate Limited: 3 requests per minute per IP.
        Requires valid JWT token in Authorization header.

        Args:
            current_user: Authenticated user from JWT
            data: ChangePasswordRequest with current and new password
            action: ChangePasswordAction

        Returns:
            204 No Content on success, or error

        Raises:
            429 Too Many Requests: When rate limit exceeded
        """
        return await action.run(
            ChangePasswordInput(
                user_id=current_user.id,
                data=data,
            )
        )

    @post("/refresh")
    @result_handler(TokenRefreshResponse, success_status=HTTP_200_OK)
    async def refresh_token(
        self,
        data: RefreshTokenRequest,
        action: FromDishka[RefreshTokenAction],
    ) -> Result[TokenPair, UserError]:
        """Refresh access token using refresh token.

        Args:
            data: Request with refresh token
            action: RefreshTokenAction

        Returns:
            New token pair, or error if refresh token is invalid/expired
        """
        return await action.run(data)

    @post("/logout")
    async def logout(self) -> Response:
        """Logout user (client-side token invalidation).

        Note: Since JWT is stateless, actual token invalidation
        happens on the client side. This endpoint is for API
        completeness and can be extended with token blacklisting.

        Returns:
            Success message
        """
        return Response(
            content={"message": "Successfully logged out"},
            status_code=HTTP_200_OK,
        )
