from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402
from os.path import abspath, dirname, join  # noqa: E402

from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402
from swiss_ai_hub.core.routes import HealthController  # noqa: E402
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler  # noqa: E402

from swiss_ai_hub.api.routes.agent.agent_controller import AgentController  # noqa: E402
from swiss_ai_hub.api.routes.event.event_controller import EventController  # noqa: E402
from swiss_ai_hub.api.routes.i18n.i18n_controller import I18nController  # noqa: E402
from swiss_ai_hub.api.routes.my_account.my_account_controller import MyAccountController  # noqa: E402
from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController  # noqa: E402
from swiss_ai_hub.api.routes.thread.thread_controller import ThreadController  # noqa: E402
from swiss_ai_hub.api.routes.translation.translation_controller import TranslationController  # noqa: E402
from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import (  # noqa: E402
    SimulatedAgentApiTestRunner,
)

enable_logging()


async def main():
    runner = SimulatedAgentApiTestRunner(
        agent_class="my_agent_class",
        agent_id="my_agent_id",
    ).with_simple_chunk_events()

    runner.mount_frontend(join(dirname(abspath(__file__)), "frontend"))

    auth = TestAuthHandler()

    runner.mount(
        HealthController(auth=auth).get_health(),
        MyAccountController(auth=auth).get_my_account().get_my_dashboard().update_my_dashboard(),
        I18nController(auth=auth).get_my_locale(),
        EventController(auth=auth).ws().get_agent_events_in_thread().resolve_thread_for_display(),
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
