from typing import Annotated, Any

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.generative_ai.retrievers.RetrieverConfig import RetrieverConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field, field_validator

from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig


def _empty_locale_string_to_none(v: Any) -> Any:
    """
    Convert empty LocaleString data to None.

    FormKit may send:
    - Empty dict: {} -> None
    - Dict with empty strings: {"en": "", "de": ""} -> None
    - LocaleString with all None/empty values -> None
    """
    if v is None:
        return None
    if isinstance(v, dict):
        # Empty dict
        if not v:
            return None
        # Dict with all empty/None values
        if all(not val for val in v.values()):
            return None
    if isinstance(v, LocaleString):
        # LocaleString with all None/empty values
        if not any([v.de, v.en, v.fr, v.it]):
            return None
    return v


class RAGAgentConfig(AgentConfig):
    """
    Configuration for a RAGAgent with multiple retrieval sources.

    Supports:
    - Multiple retrievers (knowledge base + insights)

    Note: For expert escalation functionality, use ExpertRAGAgentConfig instead.
    """

    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for the agent."),
    ]

    retrievers: Annotated[
        list[RetrieverConfig],
        Field(description="List of retriever configurations (knowledge, insight)."),
    ]

    number_of_input_tokens: Annotated[
        int, Field(description="Maximum tokens allowed in input to manage context size or cost.")
    ]
    context_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt template for providing context (e.g., retrieved documents) to the LLM."),
    ] = None
    few_shot_guard_examples: Annotated[
        list[FewShotGuardExample],
        Field(description="Examples for the few-shot guard to define which user requests are accepted."),
    ] = []
    check_context_sufficiency: Annotated[
        bool | None,
        Field(
            description="Whether or not to check if the retrieved context is sufficient for generating a response.",
        ),
    ] = False
    max_hops: Annotated[
        int,
        Field(
            description="Maximum number of retrieval hops to perform if context is insufficient.",
            ge=1,
        ),
    ] = 1
    system_prompt: Annotated[
        LocaleString | None,
        Field(description="System prompt to guide the agent's behavior and responses."),
    ] = None
    context_insufficient_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt used when the retrieved context is insufficient to answer the user's question."),
    ] = LocaleString(
        en=("Inform the user that you can not answer the question due to the following reason:"),
        de=("Informiere den Benutzer, dass du die Frage nicht beantworten kannst, aufgrund des folgenden Grundes:"),
        fr=("Informez l'utilisateur que vous ne pouvez pas répondre à la question pour la raison suivante :"),
        it=("Informa l'utente che non puoi rispondere alla domanda per il seguente motivo:"),
    )
    reranking_config: Annotated[
        RerankingConfig,
        Field(description="Configuration for reranking retrieved documents to improve relevance."),
    ] = RerankingConfig()

    @field_validator("context_prompt", "system_prompt", "context_insufficient_prompt", mode="before")
    @classmethod
    def empty_locale_string_to_none(cls, v: Any) -> Any:
        """Convert empty LocaleString data from FormKit to None."""
        return _empty_locale_string_to_none(v)
