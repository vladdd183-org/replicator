"""CountUnreadQuery - CQRS Query for counting unread notifications."""

from uuid import UUID

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.NotificationModule.Data.Repositories.NotificationRepository import (
    NotificationRepository,
)


class CountUnreadQuery(Query[UUID, int]):
    """CQRS Query: Count unread notifications for a user.
    
    Simple query that returns just the unread count.
    Useful for showing badge counts in UI.
    
    Example:
        query = CountUnreadQuery(repository)
        count = await query.execute(user_id)
    """
    
    def __init__(self, repository: NotificationRepository) -> None:
        """Initialize query with repository.
        
        Args:
            repository: Notification repository for data access
        """
        self.repository = repository
    
    async def execute(self, user_id: UUID) -> int:
        """Execute query to count unread notifications.
        
        Args:
            user_id: User ID to count notifications for
            
        Returns:
            Number of unread notifications
        """
        return await self.repository.count_unread(user_id)



