"""Task for verifying passwords."""

import bcrypt

from pydantic import BaseModel

from src.Ship.Parents.Task import SyncTask


class VerifyPasswordInput(BaseModel):
    """Input for password verification.
    
    Attributes:
        password: Plain text password to verify
        password_hash: Stored password hash
    """
    
    model_config = {"frozen": True}
    
    password: str
    password_hash: str


class VerifyPasswordTask(SyncTask[VerifyPasswordInput, bool]):
    """Synchronous task for verifying passwords against bcrypt hash.
    
    Uses SyncTask because bcrypt is CPU-bound and doesn't require I/O.
    
    Atomic operation for password verification.
    Reusable across different actions.
    
    Example:
        task = VerifyPasswordTask()
        is_valid = task.run(VerifyPasswordInput("password", stored_hash))
    """
    
    def run(self, data: VerifyPasswordInput) -> bool:
        """Verify password against stored hash.
        
        Args:
            data: Input with password and hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                data.password.encode("utf-8"),
                data.password_hash.encode("utf-8"),
            )
        except Exception:
            return False

