import asyncio
from os.path import abspath, dirname, join

from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.core.routes.health.HealthController import HealthController

from swiss_ai_hub.bot.routes.agent.AgentChatController import AgentChatController
from swiss_ai_hub.bot.routes.openai.OpenaiChatController import OpenaiChatController
from swiss_ai_hub.bot.runners.SimulatedAgentBotTestRunner import SimulatedAgentBotTestRunner

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
