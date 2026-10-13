from typing import Annotated, Any

from pydantic import Field
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig


class KnowledgeToolFields(Form):
    """The knowledge-tool settings a blueprint's config gains by listing this mixin as a base.

    Only blueprints that put `Knowledge` in a tool set need it, so the referenced-knowledge settings of every other
    chat blueprint stay free of a tool they cannot offer.
    """

    knowledge_tool: Annotated[
        KnowledgeToolConfig,
        Field(description="Which collections the model may search when it chooses to.", title="Knowledge Tool"),
    ] = KnowledgeToolConfig()

    @classmethod
    def knowledge_tool_form_elements(cls) -> dict[str, Any]:
        """The form elements for this class's own fields, for a subclass's `as_form()` to spread."""
        return {"knowledge_tool": KnowledgeToolConfig.as_form()}
