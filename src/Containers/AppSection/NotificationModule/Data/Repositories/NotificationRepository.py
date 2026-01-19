"""Notification repository for data access."""

from datetime import datetime, timezone
from uuid import UUID

from src.Ship.Parents.Repository import Repository
from src.Containers.AppSection.NotificationModule.Models.Notification import Notification


class NotificationRepository(Repository[Notification]):
    """Repository for Notification entity.
    
    Extends base Repository with notification-specific queries.
    """
    
    def __init__(self) -> None:
        """Initialize repository with Notification model."""
        super().__init__(Notification)
    
    # --- Notification-specific queries ---
    
    async def find_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[Notification]:
        """Find notifications for a user with pagination.
        
        Args:
            user_id: User ID to find notifications for
            limit: Maximum number of results
            offset: Number of results to skip
            unread_only: If True, only return unread notifications
            
        Returns:
            List of notifications
        """
        query = Notification.objects().where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        return await (
            query
            .limit(limit)
            .offset(offset)
            .order_by(Notification.created_at, ascending=False)
        )
    
    async def count_unread(self, user_id: UUID) -> int:
        """Count unread notifications for a user.
        
        Args:
            user_id: User ID to count notifications for
            
        Returns:
            Number of unread notifications
        """
        return await (
            Notification.count()
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
        )
    
    async def count_by_user(self, user_id: UUID) -> int:
        """Count all notifications for a user.
        
        Args:
            user_id: User ID to count notifications for
            
        Returns:
            Total number of notifications
        """
        return await Notification.count().where(Notification.user_id == user_id)
    
    async def mark_as_read(self, notification: Notification) -> Notification:
        """Mark a notification as read.
        
        Args:
            notification: Notification to mark as read
            
        Returns:
            Updated notification
        """
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        
        await Notification.update({
            Notification.is_read: True,
            Notification.read_at: notification.read_at,
        }).where(Notification.id == notification.id)
        
        return notification
    
    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user.
        
        Args:
            user_id: User ID to mark notifications for
            
        Returns:
            Number of notifications marked as read
        """
        read_at = datetime.now(timezone.utc)
        
        # Get count before update
        count = await self.count_unread(user_id)
        
        if count > 0:
            await Notification.update({
                Notification.is_read: True,
                Notification.read_at: read_at,
            }).where(
                Notification.user_id == user_id
            ).where(
                Notification.is_read == False
            )
        
        return count
    
    async def delete_by_user(self, user_id: UUID) -> int:
        """Delete all notifications for a user.
        
        Args:
            user_id: User ID to delete notifications for
            
        Returns:
            Number of notifications deleted
        """
        count = await self.count_by_user(user_id)
        
        if count > 0:
            await Notification.delete().where(Notification.user_id == user_id)
        
        return count



