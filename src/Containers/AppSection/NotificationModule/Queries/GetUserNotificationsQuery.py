"""GetUserNotificationsQuery - CQRS Query for listing user notifications."""

from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.NotificationModule.Models.Notification import Notification
from src.Containers.AppSection.NotificationModule.Data.Repositories.NotificationRepository import (
    NotificationRepository,
)


class GetUserNotificationsInput(BaseModel):
    """Input parameters for GetUserNotificationsQuery."""
    
    model_config = ConfigDict(frozen=True)
    
    user_id: UUID
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    unread_only: bool = False


@dataclass(frozen=True)
class GetUserNotificationsOutput:
    """Output of GetUserNotificationsQuery."""
    
    notifications: list[Notification]
    total: int
    unread_count: int
    limit: int
    offset: int


class GetUserNotificationsQuery(Query[GetUserNotificationsInput, GetUserNotificationsOutput]):
    """CQRS Query: Get notifications for a user.
    
    Read-only operation optimized for data retrieval.
    
    Example:
        query = GetUserNotificationsQuery(repository)
        result = await query.execute(GetUserNotificationsInput(
            user_id=user_id,
            limit=20,
            unread_only=True,
        ))
    """
    
    def __init__(self, repository: NotificationRepository) -> None:
        """Initialize query with repository.
        
        Args:
            repository: Notification repository for data access
        """
        self.repository = repository
    
    async def execute(self, params: GetUserNotificationsInput) -> GetUserNotificationsOutput:
        """Execute query to get user notifications.
        
        Args:
            params: Query input parameters
            
        Returns:
            GetUserNotificationsOutput with notifications and counts
        """
        notifications = await self.repository.find_by_user(
            user_id=params.user_id,
            limit=params.limit,
            offset=params.offset,
            unread_only=params.unread_only,
        )
        
        total = await self.repository.count_by_user(params.user_id)
        unread_count = await self.repository.count_unread(params.user_id)
        
        return GetUserNotificationsOutput(
            notifications=notifications,
            total=total,
            unread_count=unread_count,
            limit=params.limit,
            offset=params.offset,
        )



