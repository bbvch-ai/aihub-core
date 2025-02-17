import asyncio

from aihub_bot.routes.chat.openai.OpenaiChatController import OpenaiChatController
from aihub_bot.runners.BotTestRunner import BotTestRunner
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


async def main():
    runner = BotTestRunner()

    runner.mount(
        HealthController().get_health(),
        OpenaiChatController(
            chat_models=[
                AzureOpenAILLMConfig(
                    name="gpt-4o-mini",
                    base_url="https://aihub-dev-openai-che.openai.azure.com/",
                    api_version="2023-12-01-preview",
                    prompt_tokens_costs_per_thousand=0.00013027,
                    completion_tokens_costs_per_thousand=0.0005211,
                ),
            ]
        )
        .json_chat_completion()
        .stream_chat_completion(),
    )

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
