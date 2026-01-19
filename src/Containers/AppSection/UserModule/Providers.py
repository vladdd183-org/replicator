"""User module dependency injection providers.

Consolidated providers with clear scope separation.
Dishka automatically resolves dependencies by type hints.

Architecture:
- UserModuleProvider: APP scope - stateless tasks
- UserGatewayProvider: APP scope - gateway adapters (selected by deployment_mode)
- _BaseUserRequestProvider: Base class with common REQUEST scope dependencies  
- UserRequestProvider: HTTP context (inherits base + adds UoW with emit)
- UserCLIProvider: CLI context (inherits base + adds UoW without emit)

Gateway Pattern:
    Gateways are provided at APP scope because they are stateless.
    The adapter selection is based on Settings.deployment_mode:
    - "monolith" → DirectPaymentAdapter (direct Action calls)
    - "microservices" → HttpPaymentAdapter (HTTP calls to external service)
"""

import httpx
from dishka import Provider, Scope, provide
from litestar import Request

from src.Ship.Configs.Settings import Settings
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Actions.UpdateUserAction import UpdateUserAction
from src.Containers.AppSection.UserModule.Actions.AuthenticateAction import AuthenticateAction
from src.Containers.AppSection.UserModule.Actions.ChangePasswordAction import ChangePasswordAction
from src.Containers.AppSection.UserModule.Actions.RefreshTokenAction import RefreshTokenAction
from src.Containers.AppSection.UserModule.Actions.CreateUserSubscriptionAction import CreateUserSubscriptionAction
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import ListUsersQuery
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import GetUserQuery
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask
from src.Containers.AppSection.UserModule.Tasks.VerifyPasswordTask import VerifyPasswordTask
from src.Containers.AppSection.UserModule.Tasks.GenerateTokenTask import GenerateTokenTask
from src.Containers.AppSection.UserModule.Tasks.SendWelcomeEmailTask import SendWelcomeEmailTask

# Gateway imports
from src.Containers.AppSection.UserModule.Gateways.PaymentGateway import PaymentGateway
from src.Containers.AppSection.UserModule.Gateways.Adapters.DirectPaymentAdapter import DirectPaymentAdapter
from src.Containers.AppSection.UserModule.Gateways.Adapters.HttpPaymentAdapter import HttpPaymentAdapter

# PaymentModule imports (for DirectAdapter)
from src.Containers.VendorSection.PaymentModule.Actions.CreatePaymentAction import CreatePaymentAction
from src.Containers.VendorSection.PaymentModule.Actions.RefundPaymentAction import RefundPaymentAction
from src.Containers.VendorSection.PaymentModule.Tasks.ProcessPaymentTask import ProcessPaymentTask


class UserModuleProvider(Provider):
    """Core provider for UserModule - APP scope dependencies.
    
    Stateless services that can be reused across requests.
    """
    
    scope = Scope.APP
    
    # Tasks - stateless, reusable
    hash_password_task = provide(HashPasswordTask)
    verify_password_task = provide(VerifyPasswordTask)
    generate_token_task = provide(GenerateTokenTask)
    send_welcome_email_task = provide(SendWelcomeEmailTask)


class UserGatewayProvider(Provider):
    """Gateway provider for UserModule - APP scope.
    
    Provides gateway adapters based on deployment mode.
    
    Deployment Modes:
    - monolith: Uses DirectPaymentAdapter (calls PaymentModule Actions directly)
    - microservices: Uses HttpPaymentAdapter (HTTP calls to PaymentModule service)
    
    The selection is done at application startup based on Settings.deployment_mode.
    This allows the same business logic to work in both deployment scenarios.
    
    Example:
        # In monolith mode
        settings.deployment_mode = "monolith"
        # PaymentGateway → DirectPaymentAdapter → CreatePaymentAction
        
        # In microservices mode
        settings.deployment_mode = "microservices"
        # PaymentGateway → HttpPaymentAdapter → HTTP POST /api/v1/payments
    """
    
    scope = Scope.APP
    
    # PaymentModule dependencies (for DirectAdapter)
    process_payment_task = provide(ProcessPaymentTask)
    create_payment_action = provide(CreatePaymentAction)
    refund_payment_action = provide(RefundPaymentAction)
    
    @provide
    def provide_http_client(self, settings: Settings) -> httpx.AsyncClient:
        """Provide shared HTTP client for gateway adapters.
        
        Only used in microservices mode, but always available
        for flexibility.
        
        Features:
        - Connection pooling
        - Keep-alive
        - Configured timeout
        """
        return httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=5.0,
                read=settings.payment_service_timeout,
                write=10.0,
                pool=5.0,
            ),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
            ),
        )
    
    @provide
    def provide_payment_gateway(
        self,
        settings: Settings,
        # Direct adapter dependencies
        create_payment_action: CreatePaymentAction,
        refund_payment_action: RefundPaymentAction,
        # HTTP adapter dependencies
        http_client: httpx.AsyncClient,
    ) -> PaymentGateway:
        """Provide PaymentGateway based on deployment mode.
        
        This is the key factory method that selects the appropriate
        adapter based on configuration.
        
        Args:
            settings: Application settings with deployment_mode
            create_payment_action: For direct adapter (monolith)
            refund_payment_action: For direct adapter (monolith)
            http_client: For HTTP adapter (microservices)
        
        Returns:
            PaymentGateway implementation (DirectPaymentAdapter or HttpPaymentAdapter)
        
        Logs:
            Logs the selected adapter type at startup for debugging.
        """
        if settings.is_microservices:
            # Microservices mode - use HTTP adapter
            try:
                import logfire
                logfire.info(
                    "PaymentGateway: Using HttpPaymentAdapter",
                    base_url=settings.payment_service_url,
                    timeout=settings.payment_service_timeout,
                )
            except ImportError:
                print(f"PaymentGateway: Using HttpPaymentAdapter → {settings.payment_service_url}")
            
            return HttpPaymentAdapter(
                base_url=settings.payment_service_url,
                client=http_client,
                timeout=settings.payment_service_timeout,
                api_key=settings.payment_service_api_key,
            )
        
        # Monolith mode - use direct adapter
        try:
            import logfire
            logfire.info("PaymentGateway: Using DirectPaymentAdapter")
        except ImportError:
            print("PaymentGateway: Using DirectPaymentAdapter (direct Action calls)")
        
        return DirectPaymentAdapter(
            create_payment_action=create_payment_action,
            refund_payment_action=refund_payment_action,
        )


class _BaseUserRequestProvider(Provider):
    """Base provider with common REQUEST scope dependencies.
    
    Contains all dependencies shared between HTTP and CLI contexts.
    Not exported - use UserRequestProvider or UserCLIProvider instead.
    """
    
    scope = Scope.REQUEST
    
    # Data Layer
    user_repository = provide(UserRepository)
    
    # Queries - CQRS read side
    list_users_query = provide(ListUsersQuery)
    get_user_query = provide(GetUserQuery)
    
    # Actions - CQRS write side
    create_user_action = provide(CreateUserAction)
    update_user_action = provide(UpdateUserAction)
    delete_user_action = provide(DeleteUserAction)
    authenticate_action = provide(AuthenticateAction)
    change_password_action = provide(ChangePasswordAction)
    refresh_token_action = provide(RefreshTokenAction)
    
    # Subscription Action (uses PaymentGateway)
    create_user_subscription_action = provide(CreateUserSubscriptionAction)


class UserRequestProvider(_BaseUserRequestProvider):
    """HTTP request-scoped provider for UserModule.
    
    Extends base provider with UnitOfWork that has event emitter.
    """
    
    @provide
    def provide_user_uow(self, request: Request) -> UserUnitOfWork:
        """Provide UserUnitOfWork with event emitter from request."""
        return UserUnitOfWork(_emit=request.app.emit, _app=request.app)


class UserCLIProvider(_BaseUserRequestProvider):
    """CLI-specific provider for UserModule.
    
    Extends base provider with UnitOfWork without event emitter.
    """
    
    @provide
    def provide_user_uow(self) -> UserUnitOfWork:
        """Provide UserUnitOfWork without event emitter for CLI."""
        return UserUnitOfWork(_emit=None, _app=None)

