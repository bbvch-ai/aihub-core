from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field


class RetrievalAgentConfig(AgentConfig):
    retriever: Annotated[KnowledgeRetrieverConfig, Field(description="The configuration for knowledge retrieval.")]
    context_prompt: Annotated[
        LocaleString | None, Field(description="The context prompt for the combined and ordered nodes.")
    ] = None
