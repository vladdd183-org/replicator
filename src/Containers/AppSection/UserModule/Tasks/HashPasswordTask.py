"""Task for hashing passwords."""

import bcrypt

from src.Ship.Parents.Task import SyncTask
from src.Ship.Configs import get_settings


class HashPasswordTask(SyncTask[str, str]):
    """Synchronous task for hashing passwords using bcrypt.
    
    Uses SyncTask because bcrypt is CPU-bound and doesn't require I/O.
    For async context, wrap with anyio.to_thread.run_sync().
    
    Bcrypt rounds are configured via Settings.bcrypt_rounds.
    
    Atomic operation for password hashing.
    Reusable across different actions.
    
    Example:
        task = HashPasswordTask()
        # Sync call:
        password_hash = task.run("user_password")
        # Async call (recommended for web handlers):
        password_hash = await anyio.to_thread.run_sync(task.run, "user_password")
    """
    
    def __init__(self) -> None:
        """Initialize task with settings."""
        settings = get_settings()
        self.rounds = settings.bcrypt_rounds
    
    def run(self, password: str) -> str:
        """Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt(rounds=self.rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
