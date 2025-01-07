from aihub_agent.agents.AgentConfig import AgentConfig
from aihub_agent.steps.prompting.few_shot_step.FewShotStepConfig import (
    FewShotStepConfig,
)
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
)


class FewShotAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig
    few_shot: FewShotStepConfig
