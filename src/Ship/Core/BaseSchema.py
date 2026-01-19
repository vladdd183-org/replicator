"""Base schema classes for DTOs."""

from typing import TypeVar, Type

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="EntitySchema")


class EntitySchema(BaseModel):
    """Base class for Response DTOs with automatic conversion from Entity.
    
    Uses Pydantic V2 from_attributes for automatic mapping from ORM objects.
    
    Example:
        class UserResponse(EntitySchema):
            id: UUID
            email: str
            name: str
            is_active: bool
            # from_entity is already available from base class!
            
        # Usage:
        user_response = UserResponse.from_entity(user)
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

