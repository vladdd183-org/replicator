# ruff: noqa: N999
"""Dishka-провайдер адаптеров L0 для локальной разработки."""

from dishka import Provider, Scope, provide

from src.Ship.Adapters.Compute.SubprocessAdapter import SubprocessComputeAdapter
from src.Ship.Adapters.Identity.JWTAdapter import JWTIdentityAdapter
from src.Ship.Adapters.Messaging.InMemoryAdapter import InMemoryMessagingAdapter
from src.Ship.Adapters.Protocols import (
    ComputePort,
    IdentityPort,
    MessagingPort,
    StatePort,
    StoragePort,
)
from src.Ship.Adapters.State.SQLiteAdapter import SQLiteStateAdapter
from src.Ship.Adapters.Storage.LocalAdapter import LocalStorageAdapter


class LocalAdapterProvider(Provider):
    """Адаптеры для локальной разработки."""

    scope = Scope.APP

    @provide
    def storage(self) -> StoragePort:
        return LocalStorageAdapter()

    @provide
    def messaging(self) -> MessagingPort:
        return InMemoryMessagingAdapter()

    @provide
    def identity(self) -> IdentityPort:
        return JWTIdentityAdapter()

    @provide
    def state(self) -> StatePort:
        return SQLiteStateAdapter()

    @provide
    def compute(self) -> ComputePort:
        return SubprocessComputeAdapter()


def get_adapter_provider(adapter_mode: str = "local") -> Provider:
    match adapter_mode:
        case "local" | "development":
            return LocalAdapterProvider()
        case _:
            return LocalAdapterProvider()
