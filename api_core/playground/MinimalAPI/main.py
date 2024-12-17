import asyncio

from api_core.routes.i18n.I18nController import I18nController
from api_core.routes.user.UserController import UserController
from api_core.runners.ApiTestRunner import ApiTestRunner




async def main():
    runner = ApiTestRunner()

    runner.mount(
        UserController()
            .get_user(),

        I18nController()
            .get_my_locale()
    )

    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())