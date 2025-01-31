import asyncio

from aihub_bot.routes.health.HealthController import HealthController
from aihub_bot.runners.BotTestRunner import BotTestRunner
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


async def main():
    runner = BotTestRunner()

    runner.mount(
        HealthController().get_health(),
    )

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
