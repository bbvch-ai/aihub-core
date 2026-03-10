import asyncio
from os.path import abspath, dirname, join

from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.core.routes.health.HealthController import HealthController

from swiss_ai_hub.api.routes.agent.AgentController import AgentController
from swiss_ai_hub.api.routes.event.EventController import EventController
from swiss_ai_hub.api.routes.i18n.I18nController import I18nController
from swiss_ai_hub.api.routes.my_account.MyAccountController import MyAccountController
from swiss_ai_hub.api.routes.openai.OpenaiController import OpenaiController
from swiss_ai_hub.api.routes.thread.ThreadController import ThreadController
from swiss_ai_hub.api.routes.translation.TranslationController import TranslationController
from swiss_ai_hub.api.runners.simulation.agent.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner

enable_logging()


async def main():
    runner = SimulatedAgentApiTestRunner(
        agent_class="my_agent_class",
        agent_id="my_agent_id",
    ).with_simple_chunk_events()

    runner.mount_frontend(join(dirname(abspath(__file__)), "frontend"))

    auth = DangerousDevelopmentOnlyAuthHandler()

    runner.mount(
        HealthController(auth=auth).get_health(),
        MyAccountController(auth=auth).get_my_account().get_my_dashboard().update_my_dashboard(),
        I18nController(auth=auth).get_my_locale(),
        EventController(auth=auth).ws().get_agent_events_in_thread(),
        ThreadController(auth=auth)
        .get_user_threads()
        .create_thread()
        .get_thread()
        .add_agent_to_thread()
        .remove_agent_from_thread()
        .add_user_to_thread()
        .remove_user_from_thread()
        .get_open_chat_hitl(),
        AgentController(auth=auth)
        .get_agent_classes()
        .get_agent_class()
        .get_agent_class_instances()
        .create_agent_instance()
        .get_agent_instance()
        .update_agent_instance()
        .delete_agent_instance()
        .get_agent_instance_threads()
        .get_all_agent_instances(),
        OpenaiController(auth=auth)
        .get_models()
        .get_model()
        .get_embeddings()
        .chat_completion()
        .generate_image()
        .stt()
        .tts(),
        TranslationController(auth=auth).translate(),
    )

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
