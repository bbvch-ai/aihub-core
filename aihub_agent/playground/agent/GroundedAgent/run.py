import asyncio

from aihub_agent.agents.GroundedAgent.GroundedAgent import GroundedAgent
from aihub_agent.agents.GroundedAgent.GroundedAgentConfig import GroundedAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=GroundedAgent,
        agent_config=GroundedAgentConfig(
            agent_id="grounded_agent",
            name=LocaleString(en="Grounded Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            system_prompt=LocaleString(en="You are an agent"),
            expert_asking_agent_class="ExpertAskingAgent",
            expert_asking_agent_id="expert_agent",
            llm=AzureOpenAILLMConfig(
                name="gpt-4o",
                base_url="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2024-12-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0),
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
