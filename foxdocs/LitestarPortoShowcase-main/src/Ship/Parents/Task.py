"""Base Task class according to Porto architecture."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Task(ABC, Generic[InputT, OutputT]):
    """Base Task class.

    Tasks are classes that hold shared business logic between
    multiple Actions across different Containers.
    Every Task SHOULD have a single responsibility.
    """

    @abstractmethod
    async def run(self, data: InputT) -> OutputT:
        """Execute the task.

        Args:
            data: Input data for the task

        Returns:
            Output data from the task
        """
        raise NotImplementedError
