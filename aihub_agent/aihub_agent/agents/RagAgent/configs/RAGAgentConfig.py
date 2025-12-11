from typing import Annotated

from pydantic import Field

from aihub_agent.agents.RagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig
from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString


class RAGAgentConfig(AgentConfig):
    """
    Configuration for a RAGAgent, specifying the LLM, retrieval parameters, and prompts used to generate responses.
    """

    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for the agent."),
    ]
    retrieve_step_config: Annotated[RetrieveStepConfig, Field(description="The configuration for the retrieval step.")]
    number_of_input_tokens: Annotated[
        int, Field(description="Maximum tokens allowed in input to manage context size or cost.")
    ]
    condense_question_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt template for transforming a user query into a standalone question."),
    ] = None
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
        de=("Informiere den Benutzer, dass du die Frage nicht beantworten kannst,"),
        fr=("Informez l'utilisateur que vous ne pouvez pas répondre à la question"),
        it=("Informa l'utente che non puoi rispondere alla domanda per il seguente motivo:"),
    )
    reranking_config: Annotated[
        RerankingConfig,
        Field(description="Configuration for reranking retrieved documents to improve relevance."),
    ] = RerankingConfig()
    expert_escalation: Annotated[
        ExpertEscalationConfig | None,
        Field(
            description="Expert escalation config. Enables escalation when context is insufficient.",
        ),
    ] = None
