from typing import Annotated, Any

from pydantic import Field
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai import OrgMemoryReadConfig

from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig


class MemoryFields(Form):
    """
    The user and organization memory scoping a blueprint's config gains by listing this mixin as a base.

    `MemoryCapability` annotates its steps with this class. List it before `AgentConfig` so its
    `memory_llm_model_name` wins over the platform default the base config reports.
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
