"""Base schema classes for DTOs."""

from typing import TypeVar, Type

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="EntitySchema")


class EntitySchema(BaseModel):
    """Base class for Response DTOs with automatic conversion from Entity.

    Uses Pydantic V2 from_attributes for automatic mapping from ORM objects.

    Available methods:
        - from_entity(entity): Convert single ORM entity to DTO
        - from_entities(entities): Convert list of ORM entities to list of DTOs

    Example:
        class UserResponse(EntitySchema):
            id: UUID
            email: str
            name: str
            is_active: bool
            # from_entity and from_entities are already available!

        # Single entity:
        user_response = UserResponse.from_entity(user)

        # Multiple entities:
        users = await repository.get_all()
        user_responses = UserResponse.from_entities(users)
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @classmethod
    def from_entity(cls: Type[T], entity: object) -> T:
        """Create DTO from Entity (ORM model).

        Args:
            entity: ORM model instance

        Returns:
            DTO instance
        """
        return cls.model_validate(entity)

    @classmethod
    def from_entities(cls: Type[T], entities: list[object]) -> list[T]:
        """Create list of DTOs from list of Entities.

        Batch conversion method for converting multiple ORM entities
        to their corresponding DTOs in a single operation.

        Args:
            entities: List of ORM model instances to convert

        Returns:
            List of validated DTO instances

        Example:
            users = await user_repository.get_all()
            return UserResponse.from_entities(users)
        """
        return [cls.model_validate(entity) for entity in entities]
