"""Base Task class according to Hyper-Porto architecture.

Tasks are atomic, reusable operations.
They hold shared business logic between multiple Actions.

Usage:
- Inherit from Task for async operations (I/O, external services)
- Inherit from SyncTask for CPU-bound operations (hashing, validation)

Note: SyncTask.run() is synchronous, but can be called from async code directly.
For CPU-heavy operations in async context, wrap with anyio.to_thread.run_sync().
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Task(ABC, Generic[InputT, OutputT]):
    """Base async Task class.
    
    Tasks are classes that hold shared business logic between
    multiple Actions across different Containers.
    
    Rules:
    - One Task = one atomic operation (Single Responsibility)
    - Reusable between Actions
    - Does NOT call other Tasks directly
    - May return plain value or Result[T, E]
    
    Example:
        class SendEmailTask(Task[EmailData, bool]):
            async def run(self, data: EmailData) -> bool:
                await email_client.send(data)
                return True
    """
    
    @abstractmethod
    async def run(self, data: InputT) -> OutputT:
        """Execute the async task."""
        ...


class SyncTask(ABC, Generic[InputT, OutputT]):
    """Synchronous Task class for CPU-bound operations.
    
    Use for operations that don't require I/O:
    - Password hashing
    - Data transformation  
    - Calculations
    - Synchronous validation
    
    Example:
        class HashPasswordTask(SyncTask[str, str]):
            def run(self, password: str) -> str:
                salt = bcrypt.gensalt(rounds=12)
                return bcrypt.hashpw(password.encode(), salt).decode()
    
    For CPU-heavy operations in async context:
        import anyio
        result = await anyio.to_thread.run_sync(task.run, data)
    """
    
    @abstractmethod
    def run(self, data: InputT) -> OutputT:
        """Execute the synchronous task."""
        ...

