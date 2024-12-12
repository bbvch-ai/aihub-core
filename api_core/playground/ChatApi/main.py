import asyncio

from api_core.auth.dependencies.no_auth.use_no_auth_user import use_no_auth_user
from api_core.routes.chat.controller import chat_controller_factory
from api_core.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from lib_core.testing.logging.logger import enable_logging

enable_logging()

async def main():
    runner = SimulatedAgentApiTestRunner(
        agent_class="my_agent_class",
        agent_id="my_agent_id",
    )

    runner.app.include_router(
        chat_controller_factory(use_no_auth_user),
        prefix="/chat"
    )

    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())