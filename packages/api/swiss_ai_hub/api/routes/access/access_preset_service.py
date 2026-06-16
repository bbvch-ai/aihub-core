from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import trace_fn

from swiss_ai_hub.api.routes.access.dto.access_preset_dto import AccessPresetDTO

_PRESET_DEFINITIONS: list[tuple[str, str, str]] = [
    ("aihub.user.>", "user_everything", "everything"),
    ("aihub.admin.>", "admin_everything", "everything"),
    ("aihub.user.agent.>", "use_all_agents", "agents"),
    ("aihub.admin.agent.>", "manage_all_agents", "agents"),
    ("aihub.user.process.>", "use_all_processes", "processes"),
    ("aihub.admin.process.>", "manage_all_processes", "processes"),
    ("aihub.admin.knowledge.>", "manage_knowledge", "knowledge"),
]


class AccessPresetService:
    """Curated, described access rules covering the common authoring cases.

    Mirrors the patterns seeded as default roles in ``initialize_db._DEFAULT_ROLE_DEFINITIONS``.
    """

    @staticmethod
    @trace_fn
    def get_presets(t: LocaleHandler) -> list[AccessPresetDTO]:
        return [
            AccessPresetDTO.from_definition(rule=rule, i18n_key=i18n_key, category=category, t=t)
            for rule, i18n_key, category in _PRESET_DEFINITIONS
        ]
