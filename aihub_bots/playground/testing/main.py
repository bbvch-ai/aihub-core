import asyncio
from os.path import abspath, join, dirname

from aihub_bots.routes.health.HealthController import HealthController
from aihub_bots.routes.messages.MessagesController import MessagesController
from aihub_bots.runners.BotsTestRunner import BotsTestRunner


async def main():
    runner = BotsTestRunner()

    runner.mount(
        HealthController().get_health(),
        MessagesController().post_messages(),
    )

    runner.mount_frontend(join(dirname(abspath(__file__)), "frontend"))

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
