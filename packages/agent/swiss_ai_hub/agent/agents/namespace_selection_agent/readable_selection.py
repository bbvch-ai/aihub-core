from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import StopEvent
from swiss_ai_hub.core.generative_ai import UserScopedRetrievers
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.namespace_selection_agent.configs.namespace_selection_agent_config import (
    NamespaceSelectionAgentConfig,
)


class ReadableSelection:
    """Keeps a proposed or stored namespace selection to what the asking user may read right now.

    A selection outlives the turn it was approved in, and the delegated RAG profile may not restrict access itself,
    so access revoked since then must be enforced before every hand-over, not only when the options are offered.
    """

    @staticmethod
    def narrow(
        selection: dict[str, str], agent_config: NamespaceSelectionAgentConfig, access: AccessChecker | None
    ) -> dict[str, str]:
        if not agent_config.restrict_to_user_access or access is None:
            return selection
        readable = UserScopedRetrievers.readable_namespaces(
            access, {bucket: [namespace] for bucket, namespace in selection.items()}
        )
        return {bucket: namespaces[0] for bucket, namespaces in readable.items()}

    @staticmethod
    async def refuse(model_name: str, displayer: EventDisplayer, t: LocaleHandler) -> StopEvent:
        """Say why nothing is searched, since an empty hand-over would read as "the documents do not cover this"."""
        await displayer.display_chunk(
            t("agent.namespace_selection_agent.messages.no_accessible_knowledge"), model_name=model_name
        )
        return StopEvent()
