import asyncio
from os.path import abspath, join, dirname

from aihub_bot.routes.agent.AgentChatController import AgentChatController
from aihub_bot.routes.openai.OpenaiChatController import OpenaiChatController
from aihub_bot.runners.SimulatedAgentBotTestRunner import SimulatedAgentBotTestRunner
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
)
from aihub_lib.generative_ai.resources.models.llm.chat.self_hosted.SelfHostedLLMConfig import SelfHostedLLMConfig
from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


async def main():
    runner = SimulatedAgentBotTestRunner(agent_class="my_agent_class", agent_id="my_agent_id")
    runner.with_simple_chunk_events()

    runner.mount(
        HealthController().get_health(),
        AgentChatController().completions_json().completions_stream(),
        OpenaiChatController(
            chat_models=[
                AzureOpenAILLMConfig(
                    name="gpt-4o-mini",
                    base_url="https://aihub-dev-openai-che.openai.azure.com/",
                    api_version="2023-12-01-preview",
                    prompt_tokens_costs_per_thousand=0.00013027,
                    completion_tokens_costs_per_thousand=0.0005211,
                ),
                SelfHostedLLMConfig(
                    name="unsloth/Llama-3.2-1B-Instruct",
                    base_url="http://localhost:8182/v1",
                    is_function_calling_model=False,
                    context_size=512,
                ),
            ]
        )
        .json_chat_completion()
        .stream_chat_completion(),
    )

    runner.mount_frontend(join(dirname(abspath(__file__)), "frontend"))

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
