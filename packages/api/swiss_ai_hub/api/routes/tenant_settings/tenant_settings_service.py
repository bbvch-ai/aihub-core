import asyncio

from swiss_ai_hub.core.infrastructure import trace_fn
from swiss_ai_hub.core.persistence import TenantSettingsEntity

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.tenant_settings.dto.tenant_settings_dto import TenantSettingsDTO


class TenantSettingsService:
    @staticmethod
    @trace_fn
    async def get_settings(tenant_id: str) -> TenantSettingsDTO:
        text = await asyncio.to_thread(TenantSettingsEntity.get_chat_disclaimer, tenant_id)
        if text is None:
            text = ApiLocaleString.from_i18n_path("api.tenant_settings.default_disclaimer")
        return TenantSettingsDTO(chat_disclaimer=text)

    @staticmethod
    @trace_fn
    async def update_settings(tenant_id: str, settings: TenantSettingsDTO) -> TenantSettingsDTO:
        await asyncio.to_thread(TenantSettingsEntity.set_chat_disclaimer, tenant_id, settings.chat_disclaimer)
        return settings
