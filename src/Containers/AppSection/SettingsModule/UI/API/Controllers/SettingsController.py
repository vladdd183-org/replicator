"""SettingsModule API controller."""

from uuid import UUID

from dishka.integrations.litestar import FromDishka
from litestar import Controller, get, post, put, patch
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
from returns.result import Result

from src.Ship.Decorators.result_handler import result_handler
from src.Containers.AppSection.SettingsModule.Data.Repositories.SettingsRepository import SettingsRepository
from src.Containers.AppSection.SettingsModule.Data.Repositories.FeatureFlagRepository import FeatureFlagRepository
from src.Containers.AppSection.SettingsModule.Actions.SetSettingAction import SetSettingAction
from src.Containers.AppSection.SettingsModule.Actions.ToggleFeatureFlagAction import (
    ToggleFeatureFlagAction,
    ToggleFeatureFlagInput,
)
from src.Containers.AppSection.SettingsModule.Tasks.FeatureFlagTask import (
    CheckFeatureFlagTask,
    FeatureFlagCheckInput,
)
from src.Containers.AppSection.SettingsModule.Data.Schemas.Requests import (
    SetSettingRequest,
    CreateFeatureFlagRequest,
    CheckFeatureFlagRequest,
)
from src.Containers.AppSection.SettingsModule.Data.Schemas.Responses import (
    SettingResponse,
    SettingsListResponse,
    FeatureFlagResponse,
    FeatureFlagsListResponse,
    FeatureFlagCheckResponse,
)
from src.Containers.AppSection.SettingsModule.Errors import SettingsError
from src.Containers.AppSection.SettingsModule.Models.Setting import Setting
from src.Containers.AppSection.SettingsModule.Models.FeatureFlag import FeatureFlag


class SettingsController(Controller):
    """Controller for application settings."""
    
    path = "/settings"
    tags = ["Settings"]
    
    @get("/")
    async def list_settings(
        self,
        repository: FromDishka[SettingsRepository],
        category: str | None = None,
    ) -> SettingsListResponse:
        """List all settings, optionally filtered by category."""
        if category:
            settings = await repository.get_by_category(category)
        else:
            settings = await repository.get_all()
        
        return SettingsListResponse(
            settings=[
                SettingResponse(
                    id=s.id,
                    key=s.key,
                    value=s.value,
                    parsed_value=repository.parse_value(s),
                    value_type=s.value_type,
                    description=s.description,
                    category=s.category,
                    is_readonly=s.is_readonly,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
                for s in settings
            ],
            total=len(settings),
        )
    
    @get("/{key:str}")
    async def get_setting(
        self,
        key: str,
        repository: FromDishka[SettingsRepository],
    ) -> SettingResponse | None:
        """Get a specific setting by key."""
        setting = await repository.get_by_key(key)
        if not setting:
            return None
        
        return SettingResponse(
            id=setting.id,
            key=setting.key,
            value=setting.value,
            parsed_value=repository.parse_value(setting),
            value_type=setting.value_type,
            description=setting.description,
            category=setting.category,
            is_readonly=setting.is_readonly,
            created_at=setting.created_at,
            updated_at=setting.updated_at,
        )
    
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
        repository: FromDishka[FeatureFlagRepository],
        enabled_only: bool = False,
    ) -> FeatureFlagsListResponse:
        """List all feature flags."""
        if enabled_only:
            flags = await repository.get_enabled()
        else:
            flags = await repository.get_all()
        
        return FeatureFlagsListResponse(
            flags=[
                FeatureFlagResponse(
                    id=f.id,
                    name=f.name,
                    description=f.description,
                    enabled=f.enabled,
                    rollout_percentage=f.rollout_percentage,
                    user_allowlist=f.user_allowlist,
                    user_denylist=f.user_denylist,
                    metadata=f.metadata,
                    created_at=f.created_at,
                    updated_at=f.updated_at,
                )
                for f in flags
            ],
            total=len(flags),
        )
    
    @get("/{name:str}")
    async def get_flag(
        self,
        name: str,
        repository: FromDishka[FeatureFlagRepository],
    ) -> FeatureFlagResponse | None:
        """Get a specific feature flag by name."""
        flag = await repository.get_by_name(name)
        if not flag:
            return None
        
        return FeatureFlagResponse(
            id=flag.id,
            name=flag.name,
            description=flag.description,
            enabled=flag.enabled,
            rollout_percentage=flag.rollout_percentage,
            user_allowlist=flag.user_allowlist,
            user_denylist=flag.user_denylist,
            metadata=flag.metadata,
            created_at=flag.created_at,
            updated_at=flag.updated_at,
        )
    
    @post("/")
    async def create_flag(
        self,
        data: CreateFeatureFlagRequest,
        repository: FromDishka[FeatureFlagRepository],
    ) -> FeatureFlagResponse:
        """Create a new feature flag."""
        flag = await repository.create_flag(
            name=data.name,
            description=data.description,
            enabled=data.enabled,
            rollout_percentage=data.rollout_percentage,
        )
        
        return FeatureFlagResponse(
            id=flag.id,
            name=flag.name,
            description=flag.description,
            enabled=flag.enabled,
            rollout_percentage=flag.rollout_percentage,
            user_allowlist=flag.user_allowlist,
            user_denylist=flag.user_denylist,
            metadata=flag.metadata,
            created_at=flag.created_at,
            updated_at=flag.updated_at,
        )
    
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
        task: FromDishka[CheckFeatureFlagTask],
        user_id: UUID | None = None,
    ) -> FeatureFlagCheckResponse:
        """Check if a feature flag is enabled for a user."""
        enabled = task.run(FeatureFlagCheckInput(
            flag_name=flag_name,
            user_id=user_id,
        ))
        
        return FeatureFlagCheckResponse(
            flag_name=flag_name,
            enabled=enabled,
            user_id=user_id,
        )



