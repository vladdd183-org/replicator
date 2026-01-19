"""SettingsModule API controller."""

from uuid import UUID

from dishka.integrations.litestar import FromDishka
from litestar import Controller, get, patch, post, put
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
from returns.result import Result

from src.Containers.AppSection.SettingsModule.Actions.CreateFeatureFlagAction import (
    CreateFeatureFlagAction,
)
from src.Containers.AppSection.SettingsModule.Actions.SetSettingAction import SetSettingAction
from src.Containers.AppSection.SettingsModule.Actions.ToggleFeatureFlagAction import (
    ToggleFeatureFlagAction,
    ToggleFeatureFlagInput,
)
from src.Containers.AppSection.SettingsModule.Data.Schemas.Requests import (
    CreateFeatureFlagRequest,
    SetSettingRequest,
)
from src.Containers.AppSection.SettingsModule.Data.Schemas.Responses import (
    FeatureFlagCheckResponse,
    FeatureFlagResponse,
    FeatureFlagsListResponse,
    SettingResponse,
    SettingsListResponse,
)
from src.Containers.AppSection.SettingsModule.Errors import (
    FeatureFlagNotFoundError,
    SettingNotFoundError,
    SettingsError,
)
from src.Containers.AppSection.SettingsModule.Models.FeatureFlag import FeatureFlag
from src.Containers.AppSection.SettingsModule.Models.Setting import Setting
from src.Containers.AppSection.SettingsModule.Queries.CheckFeatureFlagQuery import (
    CheckFeatureFlagQuery,
    CheckFeatureFlagQueryInput,
)
from src.Containers.AppSection.SettingsModule.Queries.GetFeatureFlagQuery import (
    GetFeatureFlagQuery,
    GetFeatureFlagQueryInput,
)
from src.Containers.AppSection.SettingsModule.Queries.GetSettingQuery import (
    GetSettingQuery,
    GetSettingQueryInput,
)
from src.Containers.AppSection.SettingsModule.Queries.ListFeatureFlagsQuery import (
    ListFeatureFlagsQuery,
    ListFeatureFlagsQueryInput,
)
from src.Containers.AppSection.SettingsModule.Queries.ListSettingsQuery import (
    ListSettingsQuery,
    ListSettingsQueryInput,
)
from src.Ship.Core.Errors import DomainException
from src.Ship.Decorators.result_handler import result_handler


class SettingsController(Controller):
    """Controller for application settings."""

    path = "/settings"
    tags = ["Settings"]

    @get("/")
    async def list_settings(
        self,
        query: FromDishka[ListSettingsQuery],
        category: str | None = None,
    ) -> SettingsListResponse:
        """List all settings, optionally filtered by category."""
        result = await query.execute(ListSettingsQueryInput(category=category))

        return SettingsListResponse(
            settings=[SettingResponse.from_setting(s) for s in result.settings],
            total=result.total,
        )

    @get("/{key:str}")
    async def get_setting(
        self,
        key: str,
        query: FromDishka[GetSettingQuery],
    ) -> SettingResponse:
        """Get a specific setting by key."""
        setting = await query.execute(GetSettingQueryInput(key=key))
        if not setting:
            raise DomainException(SettingNotFoundError(key=key))

        return SettingResponse.from_setting(setting)

    @put("/")
    @result_handler(SettingResponse, success_status=HTTP_200_OK)
    async def set_setting(
        self,
        data: SetSettingRequest,
        action: FromDishka[SetSettingAction],
    ) -> Result[Setting, SettingsError]:
        """Set a configuration value (create or update)."""
        return await action.run(data)


class FeatureFlagsController(Controller):
    """Controller for feature flags."""

    path = "/feature-flags"
    tags = ["Feature Flags"]

    @get("/")
    async def list_flags(
        self,
        query: FromDishka[ListFeatureFlagsQuery],
        enabled_only: bool = False,
    ) -> FeatureFlagsListResponse:
        """List all feature flags."""
        result = await query.execute(ListFeatureFlagsQueryInput(enabled_only=enabled_only))

        return FeatureFlagsListResponse(
            flags=[FeatureFlagResponse.from_entity(f) for f in result.flags],
            total=result.total,
        )

    @get("/{name:str}")
    async def get_flag(
        self,
        name: str,
        query: FromDishka[GetFeatureFlagQuery],
    ) -> FeatureFlagResponse:
        """Get a specific feature flag by name."""
        flag = await query.execute(GetFeatureFlagQueryInput(name=name))
        if not flag:
            raise DomainException(FeatureFlagNotFoundError(flag_name=name))

        return FeatureFlagResponse.from_entity(flag)

    @post("/")
    @result_handler(FeatureFlagResponse, success_status=HTTP_201_CREATED)
    async def create_flag(
        self,
        data: CreateFeatureFlagRequest,
        action: FromDishka[CreateFeatureFlagAction],
    ) -> Result[FeatureFlag, SettingsError]:
        """Create a new feature flag."""
        return await action.run(data)

    @patch("/{name:str}/toggle")
    @result_handler(FeatureFlagResponse, success_status=HTTP_200_OK)
    async def toggle_flag(
        self,
        name: str,
        action: FromDishka[ToggleFeatureFlagAction],
        enabled: bool = True,
    ) -> Result[FeatureFlag, SettingsError]:
        """Toggle a feature flag on/off."""
        return await action.run(ToggleFeatureFlagInput(name=name, enabled=enabled))

    @get("/check/{flag_name:str}")
    async def check_flag(
        self,
        flag_name: str,
        query: FromDishka[CheckFeatureFlagQuery],
        user_id: UUID | None = None,
    ) -> FeatureFlagCheckResponse:
        """Check if a feature flag is enabled for a user."""
        enabled = await query.execute(
            CheckFeatureFlagQueryInput(
                flag_name=flag_name,
                user_id=user_id,
            )
        )

        return FeatureFlagCheckResponse(
            flag_name=flag_name,
            enabled=enabled,
            user_id=user_id,
        )
