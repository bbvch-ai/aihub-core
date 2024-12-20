import asyncio

from aihub_api.routes.chat.ChatController import ChatController
from aihub_api.routes.thread.ThreadController import ThreadController
from aihub_api.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()

async def main():
    runner = SimulatedAgentApiTestRunner(
        agent_class="my_agent_class",
        agent_id="my_agent_id",
    ).with_simple_chunk_events()

    runner.mount(
        ThreadController()
            .get_user_threads()
            .create_thread()
            .get_thread()
            .add_agent_to_thread()
            .remove_agent_from_thread()
            .add_user_to_thread()
            .remove_user_from_thread()
    )

    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())