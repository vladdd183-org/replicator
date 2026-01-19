"""UpdateUserAction - Use case for updating existing users."""

from uuid import UUID

from pydantic import BaseModel
from returns.result import Failure, Result, Success

from src.Containers.AppSection.UserModule.Data.Schemas.Requests import UpdateUserRequest
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Errors import UserError, UserNotFoundError
from src.Containers.AppSection.UserModule.Events import UserUpdated
from src.Containers.AppSection.UserModule.Models.User import AppUser
from src.Ship.Parents.Action import Action


class UpdateUserInput(BaseModel):
    """Input for UpdateUserAction.

    Attributes:
        user_id: UUID of user to update
        data: Update request with fields to change
    """

    model_config = {"frozen": True}

    user_id: UUID
    data: UpdateUserRequest


class UpdateUserAction(Action[UpdateUserInput, AppUser, UserError]):
    """Use Case: Update an existing user.

    Steps:
    1. Find user by ID
    2. Update provided fields
    3. Save to database
    4. Publish UserUpdated event

    Example:
        action = UpdateUserAction(uow)
        result = await action.run(UpdateUserInput(
            user_id=user_id,
            data=UpdateUserRequest(name="New Name"),
        ))
    """

    def __init__(self, uow: UserUnitOfWork) -> None:
        self.uow = uow

    async def run(
        self,
        data: UpdateUserInput,
    ) -> Result[AppUser, UserError]:
        """Execute the update user use case.

        Args:
            data: UpdateUserInput with user_id and update data

        Returns:
            Result[AppUser, UserError]: Success with updated user or Failure with error
        """
        # Step 1: Find user
        user = await self.uow.users.get(data.user_id)
        if user is None:
            return Failure(UserNotFoundError(user_id=data.user_id))

        # Step 2: Track changed fields
        changed_fields: list[str] = []

        # Update provided fields
        if data.data.name is not None:
            user.name = data.data.name
            changed_fields.append("name")

        if data.data.is_active is not None:
            user.is_active = data.data.is_active
            changed_fields.append("is_active")

        # Step 3-4: Save and publish event
        if changed_fields:
            async with self.uow:
                await self.uow.users.update(user)

                # Add domain event (published after commit)
                self.uow.add_event(
                    UserUpdated(
                        user_id=user.id,
                        updated_fields=changed_fields,
                    )
                )

                await self.uow.commit()

        return Success(user)
