"""Base Action class according to Hyper-Porto architecture.

Actions represent Use Cases of the Application.
Every Action should be responsible for performing a single use case.
Actions ALWAYS return Result[T, E] for explicit error handling.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from returns.result import Result

__all__ = ["Action"]

InputT = TypeVar("InputT", contravariant=True)
OutputT = TypeVar("OutputT", covariant=True)
ErrorT = TypeVar("ErrorT", covariant=True)


class Action(ABC, Generic[InputT, OutputT, ErrorT]):
    """Base Action class.
    
    Actions represent the Use Cases of the Application.
    Every Action should be responsible for performing a single use case.
    
    Rules:
    - One Action = one Use Case (Single Responsibility)
    - Always returns Result[OutputT, ErrorT]
    - Orchestrates Tasks, does not contain low-level logic
    - Does NOT know about HTTP, WebSocket, etc.
    - Does NOT call other Actions directly (use SubAction pattern)
    
    Example:
        class CreateUserAction(Action[CreateUserRequest, User, UserError]):
            async def run(self, data: CreateUserRequest) -> Result[User, UserError]:
                ...
    """
    
    @abstractmethod
    async def run(self, data: InputT) -> Result[OutputT, ErrorT]:
        """Execute the action.
        
        Args:
            data: Input data for the action
            
        Returns:
            Result[OutputT, ErrorT]: Success with output or Failure with error
        """
        ...
