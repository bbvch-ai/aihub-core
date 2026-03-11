from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import LocaleInput
from swiss_ai_hub.core.generative_ai import KnowledgeRetrieverConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class RetrievalAgentConfig(AgentConfig):
    retriever: Annotated[KnowledgeRetrieverConfig, Field(description="The configuration for knowledge retrieval.")]
    context_prompt: Annotated[
        LocaleString | LocaleInput | None, Field(description="The context prompt for the combined and ordered nodes.")
    ] = None

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode RetrievalAgentConfig."""
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            retriever=KnowledgeRetrieverConfig.as_form(),
            context_prompt=LocaleString.as_form(
                label=AgentLocaleString.from_i18n_path("agent.retrieval_agent.config.context_prompt.label"),
                input_type="textarea",
            ),
        )
