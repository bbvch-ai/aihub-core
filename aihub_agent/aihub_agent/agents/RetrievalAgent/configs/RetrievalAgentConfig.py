from typing import Annotated, Self

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.LocaleInput import LocaleInput
from pydantic import Field


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
            agent_class=base.agent_class,
            retriever=KnowledgeRetrieverConfig.as_form(),
            context_prompt=LocaleString.as_form(
                label=LocaleString(
                    en="Context Prompt",
                    de="Kontextprompt",
                    fr="Prompt de contexte",
                    it="Prompt di contesto",
                ),
                input_type="textarea",
            ),
        )
