from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import Checkbox
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_source import KnowledgeToolSource
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class KnowledgeToolConfig(Form):
    """Which collections the model may search when it chooses to, in a tool loop.

    Whatever is offered is narrowed to what the asking user may read, and the collections the user referenced on the
    message are offered on top.
    """

    every_readable_collection: Annotated[
        bool | Checkbox,
        Field(description="Offer every collection the asking user can read, instead of the ones listed."),
    ] = False
    sources: Annotated[
        list[KnowledgeToolSource],
        Field(description="The databases and collections the tool may search.", title="Collections"),
    ] = []

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            every_readable_collection=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.knowledge.config.every_readable_collection.label"),
                help=AgentLocaleString.from_i18n_path("agent.knowledge.config.every_readable_collection.help"),
            ),
            sources=[KnowledgeToolSource.as_form()],
        )
