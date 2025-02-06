import asyncio
from os.path import abspath, join, dirname

from aihub_bot.routes.chat.ChatController import ChatController
from aihub_bot.routes.echo.EchoController import EchoController
from aihub_bot.runners.SimulatedAgentBotTestRunner import SimulatedAgentBotTestRunner
from aihub_lib.routes.health.HealthController import HealthController


async def main():
    runner = SimulatedAgentBotTestRunner(agent_class="my_agent_class", agent_id="my_agent_id")
    runner.with_simple_chunk_events()

    runner.mount(
        HealthController().get_health(),
        ChatController()
        .completions_json()
        .completions_stream(),
        EchoController().post_messages(),
    )

    runner.mount_frontend(join(dirname(abspath(__file__)), "frontend"))

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
