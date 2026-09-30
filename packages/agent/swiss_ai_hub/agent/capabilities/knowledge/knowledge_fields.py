from typing import Annotated, Any

from pydantic import Field
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.knowledge.knowledge_config import KnowledgeConfig


class KnowledgeFields(Form):
    """The referenced-knowledge settings a blueprint's config gains by listing this mixin as a base.

    `Knowledge` annotates its step with this class. The defaults are models every deployment ships, so profiles
    stored before the mixin existed keep validating.
    """

    knowledge: Annotated[
        KnowledgeConfig,
        Field(
            description="How the knowledge collections the user references in the chat are searched.",
            title="Referenced Knowledge",
        ),
    ] = KnowledgeConfig()

    @classmethod
    def knowledge_form_elements(cls) -> dict[str, Any]:
        """The form elements for this class's own fields, for a subclass's `as_form()` to spread."""
        return {"knowledge": KnowledgeConfig.as_form()}
