from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import VectorStoreInput
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class KnowledgeToolSource(Form):
    """One knowledge database the knowledge tool may search, whole or narrowed to some of its collections."""

    vector_store: Annotated[
        MilvusVectorStoreConfig | VectorStoreInput,
        Field(description="The database and the collections in it the tool may search."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            vector_store=VectorStoreInput(
                label=AgentLocaleString.from_i18n_path("agent.knowledge.config.source.label"),
                help=AgentLocaleString.from_i18n_path("agent.knowledge.config.source.help"),
            )
        )
