"""Base Transformer class according to Porto architecture."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT", bound=BaseModel)


class Transformer(ABC, Generic[InputT, OutputT]):
    """Base Transformer class.

    Transformers are responsible for transforming data
    from one format to another (e.g., model to DTO).
    """

    @abstractmethod
    def transform(self, data: InputT) -> OutputT:
        """Transform data.

        Args:
            data: Input data to transform

        Returns:
            Transformed output data
        """
        raise NotImplementedError

    def transform_collection(self, data: list[InputT]) -> list[OutputT]:
        """Transform a collection of data.

        Args:
            data: List of input data

        Returns:
            List of transformed data
        """
        return [self.transform(item) for item in data]
