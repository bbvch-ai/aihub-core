import asyncio

from api_core.auth.dependencies.oauth2.use_oauth2_user import use_oauth2_user
from api_core.routes.agent.AgentController import AgentController
from api_core.routes.chat.ChatController import ChatController
from api_core.routes.event.EventController import EventController
from api_core.routes.health.HealthController import HealthController
from api_core.routes.i18n.I18nController import I18nController
from api_core.routes.thread.ThreadController import ThreadController
from api_core.routes.user.UserController import UserController
from api_core.runners.ApiTestRunner import ApiTestRunner
from api_core.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from lib_core.testing.logging.logger import enable_logging

enable_logging()

async def main():
    runner = ApiTestRunner()

    runner.mount(

        HealthController()
        .get_health(),

        UserController(auth=use_oauth2_user)
        .get_user(),

        I18nController(auth=use_oauth2_user)
        .get_my_locale(),

        EventController(auth=use_oauth2_user)
        .ws()
        .get_events(),

        ThreadController(auth=use_oauth2_user)
            .get_user_threads()
            .create_thread()
            .get_thread()
            .add_agent_to_thread()
            .remove_agent_from_thread()
            .add_user_to_thread()
            .remove_user_from_thread(),

        AgentController(auth=use_oauth2_user)
            .get_agent()
            .discover_agents(),

        ChatController(auth=use_oauth2_user)
            .completions_json()
            .completions_stream(),
    )

    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())