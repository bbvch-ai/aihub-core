import asyncio

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.testing.logging.logger import enable_logging

from aihub_bot.routes.agent.AgentChatController import AgentChatController
from aihub_bot.routes.bot_in_the_loop.BotInTheLoopController import BotInTheLoopController
from aihub_bot.routes.openai.OpenaiChatController import OpenaiChatController
from aihub_bot.runners.BotTestRunner import BotTestRunner

enable_logging()


async def main():
    runner = BotTestRunner(conversation_ttl_days=60)
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())

    runner.mount(
        HealthController(auth=auth).get_health(),
        OpenaiChatController(
            auth=auth,
            chat_models=[
                AzureOpenAILLMConfig(
                    name="gpt-4o-mini",
                    base_url="https://aihub-dev-openai-che.openai.azure.com/",
                    api_version="2024-12-01-preview",
                    prompt_tokens_costs_per_thousand=0.00013027,
                    completion_tokens_costs_per_thousand=0.0005211,
                ),
            ],
        )
        .json_chat_completion(typing_timeout_seconds=60)
        .stream_chat_completion(typing_timeout_seconds=60),
        AgentChatController(auth=auth)
        .completions_json(typing_timeout_seconds=60)
        .completions_stream(typing_timeout_seconds=60),
        BotInTheLoopController(auth=auth).bot_in_the_loop_response(),
    )

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
