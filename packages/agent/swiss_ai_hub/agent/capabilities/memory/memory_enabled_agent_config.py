from typing import Annotated, Any, override

from pydantic import Field
from swiss_ai_hub.core.generative_ai import OrgMemoryReadConfig

from swiss_ai_hub.agent.capabilities.conversation.conversational_agent_config import ConversationalAgentConfig
from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig


class MemoryEnabledAgentConfig(ConversationalAgentConfig):
    """
    A conversational config that also scopes user and organization memory.

    `MemoryCapability` annotates its steps with this class. It sits on the conversational base because
    memory presupposes a conversation: retrieval searches with the turn's query and storage persists the
    turn's answer.
    """

    user_memory: Annotated[
        UserMemoryConfig,
        Field(description="Configuration for user-scoped memory.", title="User Memory"),
    ] = UserMemoryConfig()
    org_memory: Annotated[
        OrgMemoryReadConfig | None,
        Field(
            description="Scoping for the organization memory the agent may read. Disable to skip organization memory.",
            title="Organization Memory",
        ),
    ] = OrgMemoryReadConfig()

    @property
    @override
    def memory_llm_model_name(self) -> str | None:
        """Point the platform's memory hook at the profile's own picker (issue #1590).

        Guarded rather than returned raw: in form mode the value is a `ModelSelect`, and a picker submitted
        blank arrives as an empty string — neither is a model name, and both mean "use the platform default".
        """
        memory_llm = self.user_memory.memory_llm
        return memory_llm if isinstance(memory_llm, str) and memory_llm else None

    @classmethod
    def memory_form_elements(cls) -> dict[str, Any]:
        """The form elements for this class's own fields, for a subclass's `as_form()` to spread."""
        return {
            "user_memory": UserMemoryConfig.as_form(),
            "org_memory": OrgMemoryReadConfig.as_form(),
        }
