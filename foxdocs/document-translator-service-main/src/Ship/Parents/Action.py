"""Base Action class according to Porto architecture."""

import logfire
import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Optional

from dishka import FromDishka
from dishka.integrations.base import wrap_injection

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Action(ABC, Generic[InputT, OutputT]):
    """Base Action class.

    Actions represent the Use Cases of the Application.
    Every Action should be responsible for performing a single use case.
    """
    
    # Флаг для отключения проверки лицензии (для публичных endpoints)
    require_license: bool = True

    @abstractmethod
    async def run(self, data: InputT) -> OutputT:
        """Execute the action.

        Args:
            data: Input data for the action

        Returns:
            Output data from the action
        """
        raise NotImplementedError

    async def execute(self, data: InputT, skip_license_check: bool = False) -> OutputT:
        """Execute action with logging, tracing and license validation.
        
        Args:
            data: Input data for the action
            skip_license_check: Skip license check for this execution (default: False)
            
        Returns:
            Output data from the action
            
        Raises:
            NotAuthorizedException: If license validation fails
        """
        action_name = self.__class__.__name__
        
        # Use logfire span for tracing
        with logfire.span(
            f"🚀 {action_name}",
            action=action_name,
            input_type=type(data).__name__ if data is not None else "None"
        ) as span:
            try:
                # Проверяем лицензию перед выполнением action
                if self.require_license and not skip_license_check:
                    await self._check_license()
                
                # Execute the action
                logfire.info(f"▶️ Starting {action_name}", action=action_name)
                result = await self.run(data)
                
                # Log successful completion
                logfire.info(
                    f"✅ {action_name} completed successfully",
                    action=action_name,
                    output_type=type(result).__name__ if result is not None else "None"
                )
                
                return result
                
            except Exception as e:
                # Log error with full context
                logfire.error(
                    f"❌ {action_name} failed",
                    action=action_name,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise
    
    async def _check_license(self) -> None:
        """
        Проверка лицензии перед выполнением action.
        
        Raises:
            NotAuthorizedException: Если лицензия невалидна
        """
        # Импортируем здесь чтобы избежать циклических зависимостей
        from src.Ship.Licensing.Middleware import check_license
        
        try:
            await check_license()
            logfire.debug(
                f"License check passed for {self.__class__.__name__}",
                action=self.__class__.__name__
            )
        except Exception as e:
            logfire.warn(
                f"License check failed for {self.__class__.__name__}",
                action=self.__class__.__name__,
                error=str(e)
            )
            raise


# Helper for dependency injection
def inject_action(action_class: type[Action]) -> Any:
    """Inject dependencies into action."""
    return wrap_injection(
        func=action_class.run,
        container_getter=lambda _, __: FromDishka(),
        is_async=True,
    )
