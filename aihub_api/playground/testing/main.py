import asyncio
from os.path import abspath, join, dirname

from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_lib.routes.health.HealthController import HealthController


async def main():
    runner = ApiTestRunner()

    runner.mount(
        HealthController().get_health(),
    )

    runner.mount_frontend(join(dirname(abspath(__file__)), "frontend"))

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
