import asyncio

from api_core.auth.dependencies.no_auth.use_no_auth_user import use_no_auth_user
from api_core.routes.i18n.controller import i18n_controller_factory
from api_core.routes.user.controller import user_controller_factory
from api_core.runners.ApiTestRunner import ApiTestRuner




async def main():
    runner = ApiTestRuner()

    runner.app.include_router(
        i18n_controller_factory(use_no_auth_user),
        prefix="/i18n"
    )

    runner.app.include_router(
        user_controller_factory(use_no_auth_user),
        prefix="/user"
    )

    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())