"""Background tasks for UserModule.

Uses dishka.integrations.taskiq for automatic dependency injection.

Defines TaskIQ tasks for asynchronous operations like:
- Sending welcome emails
- Bulk user operations
- User data cleanup
"""

from dishka.integrations.taskiq import FromDishka, inject
from returns.result import Failure, Success

from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
from src.Containers.AppSection.UserModule.Tasks.SendWelcomeEmailTask import (
    SendWelcomeEmailTask,
    WelcomeEmailData,
)
from src.Ship.Infrastructure.Workers.Broker import broker


@broker.task
@inject
async def send_welcome_email_task(
    email: str,
    name: str,
    task: FromDishka[SendWelcomeEmailTask],
) -> dict:
    """Background task: Send welcome email to new user.

    Args:
        email: User's email address
        name: User's name
        task: Injected SendWelcomeEmailTask

    Returns:
        Status dict with result
    """
    result = await task.run(WelcomeEmailData(email=email, name=name))

    return {
        "status": "sent" if result else "failed",
        "email": email,
        "name": name,
        "template": "welcome",
    }


@broker.task
@inject
async def create_user_async_task(
    email: str,
    password: str,
    name: str,
    action: FromDishka[CreateUserAction],
) -> dict:
    """Background task: Create user asynchronously.

    Useful for bulk imports or delayed user creation.
    Uses Dishka DI for automatic dependency injection.

    Args:
        email: User's email
        password: User's password
        name: User's name
        action: Injected CreateUserAction

    Returns:
        Status dict with user_id or error
    """
    request = CreateUserRequest(email=email, password=password, name=name)
    result = await action.run(request)

    match result:
        case Success(user):
            # Schedule welcome email
            await send_welcome_email_task.kiq(email=user.email, name=user.name)
            return {
                "status": "created",
                "user_id": str(user.id),
                "email": user.email,
            }
        case Failure(error):
            return {
                "status": "failed",
                "error": error.message,
                "code": error.code,
            }


@broker.task
async def bulk_create_users_task(users_data: list[dict]) -> dict:
    """Background task: Create multiple users in bulk.

    Args:
        users_data: List of user dicts with email, password, name

    Returns:
        Summary of created/failed users
    """
    results = {
        "created": [],
        "failed": [],
    }

    for user_data in users_data:
        # Schedule individual user creation
        task = await create_user_async_task.kiq(
            email=user_data["email"],
            password=user_data["password"],
            name=user_data["name"],
        )
        # Track scheduled task
        results["created"].append(
            {
                "email": user_data["email"],
                "task_id": str(task.task_id),
            }
        )

    return {
        "status": "scheduled",
        "total": len(users_data),
        "tasks": results,
    }


@broker.task
async def cleanup_inactive_users_task(days_inactive: int = 30) -> dict:
    """Background task: Mark inactive users for cleanup.

    Args:
        days_inactive: Number of days of inactivity

    Returns:
        Summary of affected users
    """
    # TODO: Implement actual cleanup logic with injected repository
    import logfire

    logfire.info(
        "🧹 Cleanup task running",
        days_inactive=days_inactive,
    )

    return {
        "status": "completed",
        "days_inactive": days_inactive,
        "users_found": 0,
        "users_cleaned": 0,
    }
