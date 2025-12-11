# ruff: noqa: E402
from aihub_api.routes.docling.DoclingController import DoclingController

from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

import nest_asyncio
from aihub_lib.auth.dependencies.TokenAndOauth2Handler.TokenAndOauth2Handler import TokenAndOauth2Handler
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import create_milvus_vector_store
from aihub_lib.routes.health.HealthController import HealthController

from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.routes.evaluation.EvaluationController import EvaluationController
from aihub_api.routes.event.EventController import EventController
from aihub_api.routes.file.FileController import FileController
from aihub_api.routes.i18n.I18nController import I18nController
from aihub_api.routes.knowledge.KnowledgeController import KnowledgeController
from aihub_api.routes.model.ModelController import ModelController
from aihub_api.routes.notification.NotificationController import NotificationController
from aihub_api.routes.openai.OpenaiController import OpenaiController
from aihub_api.routes.process.ProcessController import ProcessController
from aihub_api.routes.role.RoleController import RoleController
from aihub_api.routes.suite.SuiteController import SuiteController
from aihub_api.routes.thread.ThreadController import ThreadController
from aihub_api.routes.token.TokenController import TokenController
from aihub_api.routes.user.UserController import UserController
from aihub_api.runners.ApiTestRunner import ApiTestRunner

enable_logging()
nest_asyncio.apply()


async def main():
    runner = ApiTestRunner()

    auth = TokenAndOauth2Handler.from_auth_settings()
    # auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())

    runner.mount(
        HealthController(auth=auth).get_health(),
        SuiteController(auth=auth).get_suite(),
        UserController(auth=auth).get_my_user().get_user().get_users().get_my_dashboard().update_my_dashboard(),
        I18nController(auth=auth).get_my_locale(),
        EventController(auth=auth).ws().get_agent_events_in_thread().get_agent_event_timeseries(),
        ThreadController(auth=auth)
        .get_user_threads()
        .create_thread()
        .get_thread()
        .add_agent_to_thread()
        .remove_agent_from_thread()
        .add_user_to_thread()
        .remove_user_from_thread(),
        ModelController(auth=auth).get_models().get_model(),
        AgentController(auth=auth).get_agent().get_agent_threads().get_agent_configuration().update_agent_configuration().get_agents().discover_agents(),
        ProcessController(auth=auth)
        .get_process()
        .get_processes()
        .discover_processes()
        .get_process_walkthroughs()
        .get_process_start_forms()
        .send_process_start_form()
        .send_process_open_form()
        .get_process_open_forms(),
        TokenController(auth=auth).create_token().list_tokens().revoke_token(),
        RoleController(auth=auth).get_role().get_roles().create_role().update_role().delete_role(),
        OpenaiController(auth=auth)
        .get_models()
        .get_model_with_assistants()
        .get_embeddings()
        .chat_completion_with_assistants()
        .generate_image()
        .stt()
        .tts(),
        EvaluationController(
            auth=auth,
            judge=LLMConfig(model_name="text-generation/large"),
        )
        .create_dataset()
        .get_datasets()
        .get_dataset()
        .update_dataset()
        .get_experiment()
        .get_experiments()
        .run_experiment(),
        KnowledgeController(
            auth=auth,
            vector_store_factory=lambda collection: create_milvus_vector_store(
                MilvusSettings().URL, collection, MilvusSettings().DIMENSION
            ),
            translation_llm_config=LLMConfig(model_name="text-generation/mini"),
        )
        .create_namespace()
        .update_namespace()
        .get_databases()
        .get_documents_for_namespace()
        .get_document_by_id()
        .get_nodes_for_document()
        .get_summary_nodes_for_document()
        .initiate_document_upload()
        .validate_document_upload()
        .get_supported_file_types(),
        FileController(auth=auth)
        .get_file_url()
        .get_file_redirect()
        .get_anonymous_file_url()
        .get_anonymous_file_redirect(),
        NotificationController(auth=auth).get_notifications().update_notifications().update_notification(),
        DoclingController(auth=auth).parse_document(),
    )

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
