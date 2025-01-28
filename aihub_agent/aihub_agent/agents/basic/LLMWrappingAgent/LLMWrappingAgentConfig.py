from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig


from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig


class LLMWrappingAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig
