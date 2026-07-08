from typing import NamedTuple

from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import trace_fn

from swiss_ai_hub.api.routes.access.dto.access_preset_dto import AccessPresetDTO


class _PresetDefinition(NamedTuple):
    rule: str
    i18n_key: str
    category: str


_PRESET_DEFINITIONS: list[_PresetDefinition] = [
    _PresetDefinition("aihub.user.>", "user_everything", "everything"),
    _PresetDefinition("aihub.admin.>", "admin_everything", "everything"),
    _PresetDefinition("aihub.user.agent.>", "user_all_agents", "agents"),
    _PresetDefinition("aihub.admin.agent.>", "admin_all_agents", "agents"),
    _PresetDefinition("aihub.user.process.>", "user_all_processes", "processes"),
    _PresetDefinition("aihub.admin.process.>", "admin_all_processes", "processes"),
    _PresetDefinition("aihub.user.model.>", "user_all_models", "models"),
    _PresetDefinition("aihub.admin.knowledge.>", "admin_knowledge", "knowledge"),
]


class AccessPresetService:
    """Curated, described access rules covering the common authoring cases.

    Mirrors the patterns seeded as default roles in ``initialize_db._DEFAULT_ROLE_DEFINITIONS``.
    """

    @staticmethod
    @trace_fn
    def get_presets(t: LocaleHandler) -> list[AccessPresetDTO]:
        return [
            AccessPresetDTO.from_definition(
                rule=definition.rule, i18n_key=definition.i18n_key, category=definition.category, t=t
            )
            for definition in _PRESET_DEFINITIONS
        ]
