"""Temporal Client Factory — создание и управление подключением к Temporal.

Предоставляет:
- Singleton клиент для всего приложения
- Конфигурация через Settings
- TLS/mTLS поддержка
- Health check для liveness/readiness probes

Пример использования:

    # В Action/Controller (через DI)
    from dishka.integrations.litestar import FromDishka
    from temporalio.client import Client
    
    @post("/orders")
    async def create_order(
        data: CreateOrderRequest,
        client: FromDishka[Client],  # Temporal Client
    ) -> Response:
        handle = await client.start_workflow(
            CreateOrderWorkflow.run,
            data,
            id=f"order-{data.order_id}",
            task_queue="hyper-porto",
        )
        result = await handle.result()
        ...
    
    # Для получения существующего workflow
    handle = client.get_workflow_handle("order-123")
    result = await handle.result()
    
    # Отмена workflow
    await handle.cancel()

Конфигурация:
    
    # .env
    TEMPORAL_HOST=localhost:7233
    TEMPORAL_NAMESPACE=default
    TEMPORAL_TASK_QUEUE=hyper-porto
    TEMPORAL_ENABLE_TLS=false
    TEMPORAL_CLIENT_CERT_PATH=/path/to/cert.pem
    TEMPORAL_CLIENT_KEY_PATH=/path/to/key.pem
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from temporalio.client import Client, TLSConfig
from temporalio.converter import DataConverter

from src.Ship.Configs.Settings import Settings, get_settings
from src.Ship.Infrastructure.Temporal.Errors import TemporalConnectionError


@dataclass(frozen=True)
class TemporalClientConfig:
    """Configuration for Temporal Client.
    
    Immutable configuration dataclass для создания клиента.
    Можно создать из Settings или вручную для тестов.
    
    Attributes:
        host: Temporal server address (host:port)
        namespace: Temporal namespace
        identity: Client identity for debugging
        enable_tls: Enable TLS encryption
        client_cert_path: Path to client certificate (mTLS)
        client_key_path: Path to client private key (mTLS)
        data_converter: Custom data converter (default: JSON)
    
    Example:
        # From Settings (production)
        config = TemporalClientConfig.from_settings(get_settings())
        
        # Manual (testing)
        config = TemporalClientConfig(
            host="localhost:7233",
            namespace="test",
        )
    """
    
    host: str = "localhost:7233"
    namespace: str = "default"
    identity: str = "hyper-porto-client"
    enable_tls: bool = False
    client_cert_path: str | None = None
    client_key_path: str | None = None
    data_converter: DataConverter | None = None
    
    @classmethod
    def from_settings(cls, settings: Settings) -> "TemporalClientConfig":
        """Create config from application Settings.
        
        Args:
            settings: Application Settings instance
            
        Returns:
            TemporalClientConfig instance
        """
        return cls(
            host=settings.temporal_host,
            namespace=settings.temporal_namespace,
            identity=settings.temporal_identity,
            enable_tls=settings.temporal_enable_tls,
            client_cert_path=settings.temporal_client_cert_path,
            client_key_path=settings.temporal_client_key_path,
        )
    
    def build_tls_config(self) -> TLSConfig | None:
        """Build TLS configuration if enabled.
        
        Returns:
            TLSConfig or None if TLS disabled
            
        Raises:
            TemporalConnectionError: If TLS enabled but certs missing
        """
        if not self.enable_tls:
            return None
        
        # Basic TLS (server verification only)
        if not self.client_cert_path or not self.client_key_path:
            return TLSConfig()
        
        # mTLS (mutual TLS with client certificate)
        cert_path = Path(self.client_cert_path)
        key_path = Path(self.client_key_path)
        
        if not cert_path.exists():
            raise TemporalConnectionError(
                message=f"Client certificate not found: {cert_path}",
            )
        if not key_path.exists():
            raise TemporalConnectionError(
                message=f"Client key not found: {key_path}",
            )
        
        return TLSConfig(
            client_cert=cert_path.read_bytes(),
            client_private_key=key_path.read_bytes(),
        )


async def create_temporal_client(
    config: TemporalClientConfig | None = None,
) -> Client:
    """Create a new Temporal Client instance.
    
    Creates a new connection to Temporal server.
    For production, prefer get_temporal_client() for singleton.
    
    Args:
        config: Client configuration (uses Settings if None)
        
    Returns:
        Connected Temporal Client
        
    Raises:
        TemporalConnectionError: If connection fails
        
    Example:
        # With default config from Settings
        client = await create_temporal_client()
        
        # With custom config
        config = TemporalClientConfig(host="temporal:7233")
        client = await create_temporal_client(config)
    """
    if config is None:
        config = TemporalClientConfig.from_settings(get_settings())
    
    try:
        tls_config = config.build_tls_config()
        
        client = await Client.connect(
            target_host=config.host,
            namespace=config.namespace,
            identity=config.identity,
            tls=tls_config,
            data_converter=config.data_converter or DataConverter.default,
        )
        
        return client
        
    except Exception as e:
        raise TemporalConnectionError(
            message=f"Failed to connect to Temporal at {config.host}: {e}",
            host=config.host,
            namespace=config.namespace,
        ) from e


# Singleton client instance
_temporal_client: Client | None = None


async def get_temporal_client() -> Client:
    """Get singleton Temporal Client.
    
    Returns cached client or creates new one.
    Singleton ensures efficient connection reuse.
    
    Returns:
        Temporal Client instance
        
    Example:
        client = await get_temporal_client()
        handle = await client.start_workflow(...)
    """
    global _temporal_client
    
    if _temporal_client is None:
        _temporal_client = await create_temporal_client()
    
    return _temporal_client


async def close_temporal_client() -> None:
    """Close the singleton Temporal Client.
    
    Should be called on application shutdown.
    Safe to call multiple times.
    """
    global _temporal_client
    
    if _temporal_client is not None:
        await _temporal_client.close()
        _temporal_client = None


async def health_check() -> dict[str, Any]:
    """Check Temporal connection health.
    
    Returns health status for monitoring/probes.
    
    Returns:
        Dict with status and details
        
    Example:
        health = await health_check()
        # {"status": "healthy", "host": "localhost:7233", ...}
    """
    settings = get_settings()
    
    try:
        client = await get_temporal_client()
        
        # Try to list workflows to verify connection
        async for _ in client.list_workflows(query="", page_size=1):
            break  # Just need one to verify connection
        
        return {
            "status": "healthy",
            "host": settings.temporal_host,
            "namespace": settings.temporal_namespace,
            "connected": True,
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "host": settings.temporal_host,
            "namespace": settings.temporal_namespace,
            "connected": False,
            "error": str(e),
        }


__all__ = [
    "TemporalClientConfig",
    "create_temporal_client",
    "get_temporal_client",
    "close_temporal_client",
    "health_check",
]
