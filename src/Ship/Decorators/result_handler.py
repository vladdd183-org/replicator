"""Result handler decorator for automatic Result -> Response conversion.

Works with Problem Details (RFC 9457) by raising errors as exceptions.
"""

from functools import wraps
from typing import TypeVar, Callable, Type, Any, Protocol, runtime_checkable

from litestar import Response
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Core.Errors import BaseError, DomainException

T = TypeVar("T")
E = TypeVar("E")


@runtime_checkable
class FromEntityProtocol(Protocol):
    """Protocol for DTOs that can be created from entities."""
    
    @classmethod
    def from_entity(cls, entity: object) -> "FromEntityProtocol":
        """Create DTO from entity."""
        ...


def result_handler(
    response_dto: Type[BaseModel] | None,
    success_status: int = 200,
) -> Callable[[Callable[..., Result[T, E]]], Callable[..., Any]]:
    """Decorator for automatic Result -> Response conversion.
    
    On Success: returns HTTP response with serialized DTO.
    On Failure: raises DomainException for Problem Details handling.
    
    DTO conversion priority:
    1. If response_dto is None or value is None -> empty response
    2. If DTO has from_entity() method -> use it
    3. If value is already a BaseModel -> use directly
    4. Otherwise -> use model_validate with from_attributes
    
    Args:
        response_dto: Pydantic model for serializing Success value (None for 204)
        success_status: HTTP status code for successful response
        
    Returns:
        Decorator function
        
    Example:
        @post("/users")
        @result_handler(UserResponse, success_status=201)
        async def create_user(
            data: CreateUserRequest,
            action: FromDishka[CreateUserAction],
        ) -> Result[User, UserError]:
            return await action.run(data)
    """
    def decorator(func: Callable[..., Result[T, E]]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            
            match result:
                case Success(value):
                    # Handle 204 No Content
                    if response_dto is None or value is None:
                        return Response(content=None, status_code=success_status)
                    
                    # Convert to DTO using appropriate method
                    content = _convert_to_dto(response_dto, value)
                    return Response(content=content, status_code=success_status)
                
                case Failure(error):
                    # Wrap BaseError in DomainException for Problem Details handling
                    if isinstance(error, BaseError):
                        raise DomainException(error)
                    else:
                        # Wrap unknown errors in DomainException for consistent handling
                        from src.Ship.Core.Errors import UnexpectedError
                        raise DomainException(UnexpectedError(
                            message=str(error),
                            details={"original_type": type(error).__name__},
                        ))
        
        return wrapper
    return decorator


def _convert_to_dto(dto_class: Type[BaseModel], value: Any) -> BaseModel:
    """Convert value to DTO using the most appropriate method.
    
    Args:
        dto_class: Target Pydantic model class
        value: Value to convert
        
    Returns:
        DTO instance
    """
    # If DTO has from_entity method, use it
    if isinstance(dto_class, type) and hasattr(dto_class, "from_entity"):
        return dto_class.from_entity(value)
    
    # If value is already the correct type
    if isinstance(value, dto_class):
        return value
    
    # If value is any BaseModel, convert via dict
    if isinstance(value, BaseModel):
        return dto_class.model_validate(value.model_dump())
    
    # Otherwise use from_attributes for ORM models
    return dto_class.model_validate(value, from_attributes=True)
