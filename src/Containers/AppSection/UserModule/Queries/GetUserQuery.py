"""GetUserQuery - CQRS query for fetching user by ID."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Models.User import AppUser


class GetUserQueryInput(BaseModel):
    """Input parameters for GetUserQuery.
    
    Attributes:
        user_id: UUID of user to fetch
    """
    
    model_config = ConfigDict(frozen=True)
    
    user_id: UUID


class GetUserQuery(Query[GetUserQueryInput, AppUser | None]):
    """CQRS Query: Get user by ID.
    
    Read-only operation optimized for data retrieval.
    Does not go through UnitOfWork for better performance.
    Inherits from base Query class.
    
    Example:
        query = GetUserQuery()
        user = await query.execute(GetUserQueryInput(user_id=user_id))
        if user:
            return UserResponse.from_entity(user)
    """
    
    async def execute(self, input: GetUserQueryInput) -> AppUser | None:
        """Execute query to get user by ID.
        
        Args:
            input: Query input with user_id
            
        Returns:
            User or None if not found
        """
        return await AppUser.objects().where(AppUser.id == input.user_id).first()
