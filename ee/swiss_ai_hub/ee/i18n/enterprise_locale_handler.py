import os

from swiss_ai_hub.agent import AgentLocaleHandler


class EnterpriseLocaleHandler(AgentLocaleHandler):
    """Adds the enterprise package's own ``translations`` directory on top of the agent SDK's, so enterprise agents keep
    resolving the shared ``agent.*`` strings next to their own."""

    def get_locale_paths(self) -> list[str]:
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        relative_path = os.path.join(current_file_directory, "translations")

        return [*super().get_locale_paths(), relative_path]
