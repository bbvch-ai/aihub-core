import asyncio

from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.core.routes.health.HealthController import HealthController

from swiss_ai_hub.bot.routes.agent.AgentChatController import AgentChatController
from swiss_ai_hub.bot.routes.bot_in_the_loop.BotInTheLoopController import BotInTheLoopController
from swiss_ai_hub.bot.routes.openai.OpenaiChatController import OpenaiChatController
from swiss_ai_hub.bot.runners.BotTestRunner import BotTestRunner

enable_logging()


async def main():
    runner = BotTestRunner(conversation_ttl_days=60)
    auth = DangerousDevelopmentOnlyAuthHandler()

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
