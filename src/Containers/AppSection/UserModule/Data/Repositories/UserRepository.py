"""User repository for data access.

Uses Repository hooks for cache invalidation.
For caching reads, use cashews @cache decorator directly if needed.
"""

from datetime import datetime, timezone

from src.Ship.Parents.Repository import Repository
from src.Ship.Decorators.cache_utils import invalidate_cache
from src.Containers.AppSection.UserModule.Models.User import AppUser


class UserRepository(Repository[AppUser]):
    """Repository for AppUser entity.
    
    Extends base Repository with user-specific queries.
    Uses hooks for automatic cache invalidation.
    """
    
    def __init__(self) -> None:
        """Initialize repository with AppUser model."""
        super().__init__(AppUser)
    
    # --- Lifecycle hooks for cache invalidation ---
    
    async def _on_add(self, entity: AppUser) -> None:
        """Invalidate cache after adding user."""
        await invalidate_cache("users:list:*", "users:count")
    
    async def _on_update(self, entity: AppUser) -> None:
        """Invalidate cache after updating user."""
        await invalidate_cache(
            f"user:{entity.id}",
            "user:email:*",
            "users:list:*",
            "users:count",
        )
    
    async def _on_delete(self, entity: AppUser) -> None:
        """Invalidate cache after deleting user."""
        await invalidate_cache(
            f"user:{entity.id}",
            "user:email:*",
            "users:list:*",
            "users:count",
        )
    
    # --- User-specific queries ---
    
    async def find_by_email(self, email: str) -> AppUser | None:
        """Find user by email address."""
        return await AppUser.objects().where(AppUser.email == email).first()
    
    async def find_active(self, limit: int = 20, offset: int = 0) -> list[AppUser]:
        """Find active users with pagination."""
        return await (
            AppUser.objects()
            .where(AppUser.is_active == True)
            .limit(limit)
            .offset(offset)
            .order_by(AppUser.created_at, ascending=False)
        )
    
    async def count_active(self) -> int:
        """Count active users."""
        return await AppUser.count().where(AppUser.is_active == True)
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists.
        
        Uses find_by_email internally to avoid query duplication.
        """
        return (await self.find_by_email(email)) is not None
    
    async def deactivate(self, user: AppUser) -> AppUser:
        """Deactivate user account."""
        user.is_active = False
        return await self.update(user)
    
    # --- Override update for SQLite compatibility ---
    
    async def update(self, user: AppUser) -> AppUser:
        """Update user with SQLite-compatible timestamp handling.
        
        Uses raw UPDATE to avoid SQLite TimestamptzNow issues.
        This is a known SQLite limitation with Piccolo ORM.
        """
        await AppUser.update({
            AppUser.email: user.email,
            AppUser.password_hash: user.password_hash,
            AppUser.name: user.name,
            AppUser.is_active: user.is_active,
            AppUser.updated_at: datetime.now(timezone.utc),
        }).where(AppUser.id == user.id)
        
        # Refresh to get updated timestamp
        updated = await AppUser.objects().where(AppUser.id == user.id).first()
        if updated:
            user.updated_at = updated.updated_at
        
        # Call hook for cache invalidation
        await self._on_update(user)
        return user
