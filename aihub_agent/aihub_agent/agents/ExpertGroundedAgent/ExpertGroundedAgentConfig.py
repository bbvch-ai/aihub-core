from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.generative_ai.resources.models.llm.chat.gemini.GeminiLLMConfig import GeminiLLMConfig
from aihub_lib.generative_ai.resources.models.llm.chat.openai_like.OpenaiLikeLLMConfig import OpenaiLikeLLMConfig


class ExpertGroundedAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig | GeminiLLMConfig | OpenaiLikeLLMConfig
    expert_asking_agent_class: str
    expert_asking_agent_id: str
