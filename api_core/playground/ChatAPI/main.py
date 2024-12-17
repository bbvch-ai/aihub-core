import asyncio

from api_core.routes.chat.ChatController import ChatController
from api_core.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from lib_core.testing.logging.logger import enable_logging

enable_logging()

async def main():
    runner = SimulatedAgentApiTestRunner(
        agent_class="my_agent_class",
        agent_id="my_agent_id",
    ).with_simple_chunk_events()

    runner.mount(
        ChatController()
            .completions_json()
            .completions_stream()
    )

    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())