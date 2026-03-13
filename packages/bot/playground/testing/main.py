from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402
from os.path import abspath, dirname, join  # noqa: E402

from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_handler import (  # noqa: E402, E501
    DangerousDevelopmentOnlyAuthHandler,
)
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402
from swiss_ai_hub.core.routes import HealthController  # noqa: E402

from swiss_ai_hub.bot.routes.agent.agent_chat_controller import AgentChatController  # noqa: E402
from swiss_ai_hub.bot.routes.openai.openai_chat_controller import OpenaiChatController  # noqa: E402
from swiss_ai_hub.bot.runners.simulated_agent_bot_test_runner import SimulatedAgentBotTestRunner  # noqa: E402

enable_logging()


async def main():
    runner = SimulatedAgentBotTestRunner(agent_class="my_agent_class", agent_id="my_agent_id")
    runner.with_simple_chunk_events()
    auth = DangerousDevelopmentOnlyAuthHandler()

    runner.mount(
        HealthController(auth=auth).get_health(),
        AgentChatController(auth=auth).completions_json().completions_stream(),
        OpenaiChatController(
            auth=auth,
        )
        .json_chat_completion()
        .stream_chat_completion(),
    )

    runner.mount_frontend(join(dirname(abspath(__file__)), "frontend"))

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
