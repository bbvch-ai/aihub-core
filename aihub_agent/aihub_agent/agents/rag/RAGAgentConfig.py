from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
)

from aihub_agent.agents.rag.CondenseStandaloneQuestionStepConfig import (
    CondenseStandaloneQuestionStepConfig,
)
from aihub_agent.agents.rag.LimitChatHistoryStepConfig import LimitChatHistoryStepConfig
from aihub_agent.agents.rag.LimitChatHistoryWithContextStepConfig import (
    LimitChatHistoryWithContextStepConfig,
)
from aihub_agent.agents.rag.RetrieveStepConfig import RetrieveStepConfig


class RAGAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig
    retrieve_step_config: RetrieveStepConfig
    limit_chat_history_step_config: LimitChatHistoryStepConfig
    condense_standalone_question_step_config: CondenseStandaloneQuestionStepConfig
    limit_chat_history_with_context_step_config: LimitChatHistoryWithContextStepConfig
