import asyncio

from aihub_bots.routes.health.HealthController import HealthController
from aihub_bots.runners.BotsTestRunner import BotsTestRunner
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


async def main():
    runner = BotsTestRunner()

    runner.mount(
        HealthController().get_health(),
    )

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
