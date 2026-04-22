from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402
from swiss_ai_hub.core.routes import HealthController  # noqa: E402
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler  # noqa: E402

from swiss_ai_hub.bot.routes.agent.agent_chat_controller import AgentChatController  # noqa: E402
from swiss_ai_hub.bot.routes.bot_in_the_loop.bot_in_the_loop_controller import BotInTheLoopController  # noqa: E402
from swiss_ai_hub.bot.routes.openai.openai_chat_controller import OpenaiChatController  # noqa: E402
from swiss_ai_hub.bot.runners.bot_test_runner import BotTestRunner  # noqa: E402

enable_logging()


async def main():
    runner = BotTestRunner(conversation_ttl_days=60)
    auth = TestAuthHandler()

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
