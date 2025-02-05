import asyncio
from os.path import abspath, join, dirname

from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.routes.chat.ChatController import ChatController
from aihub_api.routes.event.EventController import EventController
from aihub_api.routes.i18n.I18nController import I18nController
from aihub_api.routes.openai.OpenaiController import OpenaiController
from aihub_api.routes.thread.ThreadController import ThreadController
from aihub_api.routes.user.UserController import UserController
from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_lib.routes.health.HealthController import HealthController


async def main():
    runner = ApiTestRunner()

    runner.mount_frontend(join(dirname(abspath(__file__)), "frontend"))

    runner.mount(
        HealthController().get_health(),
        UserController().get_user(),
        I18nController().get_my_locale(),
        EventController().ws().get_events(),
        ThreadController()
            .get_user_threads()
            .create_thread()
            .get_thread()
            .add_agent_to_thread()
            .remove_agent_from_thread()
            .add_user_to_thread()
            .remove_user_from_thread(),
        AgentController().get_agent().discover_agents(),
        ChatController().completions_json().completions_stream(),
        OpenaiController()
            .get_models()
            .get_model()
            .get_embeddings()
            .chat_completion()
            .generate_image()
    )

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
