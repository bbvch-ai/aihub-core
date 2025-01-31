import asyncio

from aihub_api.auth.dependencies.oauth2.use_oauth2_user import use_oauth2_user
from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.routes.chat.ChatController import ChatController
from aihub_api.routes.event.EventController import EventController
from aihub_api.routes.health.HealthController import HealthController
from aihub_api.routes.i18n.I18nController import I18nController
from aihub_api.routes.thread.ThreadController import ThreadController
from aihub_api.routes.user.UserController import UserController
from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_api.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


async def main():
    runner = ApiTestRunner()

    runner.mount(
        HealthController().get_health(),
        UserController(auth=use_oauth2_user).get_user(),
        I18nController(auth=use_oauth2_user).get_my_locale(),
        EventController(auth=use_oauth2_user).ws().get_events(),
        ThreadController(auth=use_oauth2_user)
        .get_user_threads()
        .create_thread()
        .get_thread()
        .add_agent_to_thread()
        .remove_agent_from_thread()
        .add_user_to_thread()
        .remove_user_from_thread(),
        AgentController(auth=use_oauth2_user).get_agent().discover_agents(),
        ChatController(auth=use_oauth2_user).completions_json().completions_stream(),
    )

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
