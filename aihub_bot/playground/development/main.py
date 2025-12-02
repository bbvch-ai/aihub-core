import asyncio

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.infrastructure.logging.logger import enable_logging

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
        OpenaiChatController(auth=auth)
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
