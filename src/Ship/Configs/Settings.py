"""Application settings using Pydantic BaseSettings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.
    
    Loads configuration from environment variables and .env file.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = Field(default="Hyper-Porto API", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    app_host: str = Field(default="0.0.0.0", description="Server host")
    app_port: int = Field(default=8000, description="Server port")
    app_debug: bool = Field(default=False, description="Debug mode")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )
    
    # Deployment Mode - determines gateway adapter selection
    deployment_mode: Literal["monolith", "microservices"] = Field(
        default="monolith",
        description="Deployment mode: monolith (direct calls) or microservices (HTTP calls)",
    )
    
    # Database
    db_url: str = Field(
        default="sqlite:///data/app.db",
        description="Database URL",
    )
    
    # Redis (for cache, background tasks, and event bus)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL",
    )
    
    # RabbitMQ (for enterprise event bus)
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        description="RabbitMQ AMQP URL",
    )
    
    # Event Bus
    event_bus_backend: str = Field(
        default="auto",
        description="Event bus backend: auto, inmemory, redis, rabbitmq",
    )
    
    # JWT
    jwt_secret: str = Field(
        default="your-super-secret-key-change-in-production",
        description="JWT secret key",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT access token expiration in hours")
    jwt_refresh_expiration_days: int = Field(default=7, description="JWT refresh token expiration in days")
    
    # Security
    bcrypt_rounds: int = Field(default=12, description="Bcrypt hashing rounds")
    
    # CORS
    cors_allow_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow CORS credentials")
    cors_allow_methods: list[str] = Field(
        default=["*"],
        description="Allowed CORS methods",
    )
    cors_allow_headers: list[str] = Field(
        default=["*"],
        description="Allowed CORS headers",
    )
    
    # Logfire
    logfire_token: str | None = Field(default=None, description="Logfire token")
    
    # =========================================================================
    # Gateway Settings - External Service URLs (for microservices mode)
    # =========================================================================
    
    # Payment Service
    payment_service_url: str = Field(
        default="http://localhost:8001",
        description="PaymentModule service URL (for microservices mode)",
    )
    payment_service_timeout: float = Field(
        default=30.0,
        description="Payment service request timeout in seconds",
    )
    payment_service_api_key: str | None = Field(
        default=None,
        description="API key for Payment service authentication",
    )
    
    # Notification Service (example for future gateways)
    notification_service_url: str = Field(
        default="http://localhost:8002",
        description="NotificationModule service URL (for microservices mode)",
    )
    notification_service_timeout: float = Field(
        default=10.0,
        description="Notification service request timeout in seconds",
    )
    
    # Search Service (example for future gateways)
    search_service_url: str = Field(
        default="http://localhost:8003",
        description="SearchModule service URL (for microservices mode)",
    )
    search_service_timeout: float = Field(
        default=5.0,
        description="Search service request timeout in seconds",
    )
    
    # =========================================================================
    # Temporal.io Settings (Durable Execution, Saga Workflows)
    # =========================================================================
    
    temporal_host: str = Field(
        default="localhost:7233",
        description="Temporal server gRPC endpoint (host:port)",
    )
    temporal_namespace: str = Field(
        default="default",
        description="Temporal namespace for workflow isolation",
    )
    temporal_task_queue: str = Field(
        default="hyper-porto",
        description="Default Temporal task queue for workflows and activities",
    )
    temporal_identity: str = Field(
        default="hyper-porto-worker",
        description="Worker identity for debugging and monitoring",
    )
    temporal_max_concurrent_activities: int = Field(
        default=100,
        description="Maximum concurrent activity executions per worker",
    )
    temporal_max_concurrent_workflows: int = Field(
        default=100,
        description="Maximum concurrent workflow tasks per worker",
    )
    temporal_enable_tls: bool = Field(
        default=False,
        description="Enable TLS for Temporal connection",
    )
    temporal_client_cert_path: str | None = Field(
        default=None,
        description="Path to client TLS certificate (for mTLS)",
    )
    temporal_client_key_path: str | None = Field(
        default=None,
        description="Path to client TLS private key (for mTLS)",
    )
    temporal_data_converter_encoding_type: str = Field(
        default="json/plain",
        description="Default encoding for Temporal data converter",
    )
    
    # Transactional Outbox Pattern
    outbox_enabled: bool = Field(
        default=True,
        description="Enable Transactional Outbox pattern for reliable event delivery",
    )
    outbox_batch_size: int = Field(
        default=100,
        description="Maximum events to process per outbox worker run",
    )
    outbox_max_retries: int = Field(
        default=5,
        description="Maximum retry attempts for failed outbox events",
    )
    outbox_backoff_base_seconds: int = Field(
        default=30,
        description="Base delay for exponential backoff (seconds)",
    )
    outbox_cleanup_hours: int = Field(
        default=24,
        description="Delete published events older than this (hours)",
    )
    outbox_poll_interval_seconds: int = Field(
        default=60,
        description="Interval between outbox polling runs (seconds)",
    )
    
    # =========================================================================
    # Replicator AI Settings
    # =========================================================================
    
    # Adapter mode: determines which adapters to use
    adapter_mode: str = Field(
        default="local",
        description="Adapter mode: local, production, hybrid",
    )
    
    # OpenRouter / LLM
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key for LLM access",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter base URL",
    )
    
    # Мульти-модельная маршрутизация:
    # strategist -- мозг (COMPASS), нужно глубокое рассуждение
    strategist_model: str = Field(
        default="anthropic/claude-opus-4",
        description="Model for COMPASS strategy (deep reasoning, Opus 4.6)",
    )
    # worker -- быстрые воркеры (компиляция, декомпозиция, исполнение)
    worker_model: str = Field(
        default="openai/gpt-oss-120b",
        description="Fast worker model on Cerebras (569+ tok/s, $0.35/M)",
    )
    # reviewer -- ревью и верификация
    reviewer_model: str = Field(
        default="openai/gpt-oss-120b",
        description="Model for code review and verification",
    )
    
    # Replicator pipeline
    max_retries: int = Field(
        default=3,
        description="Maximum retries for failed pipeline steps",
    )
    k_voting_k: int = Field(
        default=1,
        description="Number of parallel agents for K-Voting (1 = no voting)",
    )
    min_confidence: float = Field(
        default=0.5,
        description="Minimum confidence threshold for COMPASS strategy",
    )
    
    # Storage paths
    storage_base_path: str = Field(
        default="./data/storage",
        description="Base path for local storage adapter",
    )
    state_db_path: str = Field(
        default="./data/state.db",
        description="Path to SQLite state database",
    )
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"
    
    @property
    def is_monolith(self) -> bool:
        """Check if running in monolith deployment mode.
        
        In monolith mode, gateways use direct adapters (in-process calls).
        """
        return self.deployment_mode == "monolith"
    
    @property
    def is_microservices(self) -> bool:
        """Check if running in microservices deployment mode.
        
        In microservices mode, gateways use HTTP adapters (network calls).
        """
        return self.deployment_mode == "microservices"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.
    
    Returns:
        Cached Settings instance.
    """
    return Settings()

