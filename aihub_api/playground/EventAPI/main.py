import asyncio

from aihub_api.routes.event.EventController import EventController
from aihub_api.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()

async def main():
    runner = SimulatedAgentApiTestRunner(
        agent_class="my_agent_class",
        agent_id="my_agent_id",
    ).with_simple_chunk_events()

    runner.mount(
        EventController()
            .ws()
            .get_events()
    )

    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())