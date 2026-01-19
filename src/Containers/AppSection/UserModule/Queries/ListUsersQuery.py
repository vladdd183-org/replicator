"""ListUsersQuery - CQRS query for listing users."""

from dataclasses import dataclass

from pydantic import BaseModel, Field, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Models.User import AppUser


class ListUsersQueryInput(BaseModel):
    """Input parameters for ListUsersQuery.
    
    Uses Pydantic for consistency with other DTOs.
    """
    
    model_config = ConfigDict(frozen=True)
    
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    active_only: bool = False


@dataclass(frozen=True)
class ListUsersQueryOutput:
    """Output of ListUsersQuery.
    
    Uses dataclass instead of Pydantic to avoid arbitrary_types_allowed.
    ORM models are handled at Query layer, not serialized to JSON.
    """
    
    users: list[AppUser]
    total: int
    limit: int
    offset: int


class ListUsersQuery(Query[ListUsersQueryInput, ListUsersQueryOutput]):
    """CQRS Query: List users with pagination.
    
    Read-only operation optimized for data retrieval.
    Does not go through UnitOfWork for better performance.
    
    Example:
        query = ListUsersQuery()
        result = await query.execute(ListUsersQueryInput(limit=10))
        return UserListResponse(users=result.users, total=result.total)
    """
    
    async def execute(self, params: ListUsersQueryInput) -> ListUsersQueryOutput:
        """Execute query to list users."""
        query = AppUser.objects()
        count_query = AppUser.count()
        
        if params.active_only:
            query = query.where(AppUser.is_active == True)
            count_query = count_query.where(AppUser.is_active == True)
        
        total = await count_query
        users = await (
            query
            .limit(params.limit)
            .offset(params.offset)
            .order_by(AppUser.created_at, ascending=False)
        )
        
        return ListUsersQueryOutput(
            users=users,
            total=total,
            limit=params.limit,
            offset=params.offset,
        )
