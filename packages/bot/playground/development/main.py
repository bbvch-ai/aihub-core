import asyncio

from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_handler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.routes import HealthController

from swiss_ai_hub.bot.routes.agent.agent_chat_controller import AgentChatController
from swiss_ai_hub.bot.routes.bot_in_the_loop.bot_in_the_loop_controller import BotInTheLoopController
from swiss_ai_hub.bot.routes.openai.openai_chat_controller import OpenaiChatController
from swiss_ai_hub.bot.runners.bot_test_runner import BotTestRunner

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
