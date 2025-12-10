from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.RagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig
from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig


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
