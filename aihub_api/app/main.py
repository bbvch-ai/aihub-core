# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

from aihub_lib.auth.dependencies.TokenAndOauth2Handler.TokenAndOauth2Handler import TokenAndOauth2Handler
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.routes.evaluation.DatasetController import DatasetController
from aihub_api.routes.event.EventController import EventController
from aihub_api.routes.file.FileController import FileController
from aihub_api.routes.health.ApiHealthController import ApiHealthController
from aihub_api.routes.i18n.I18nController import I18nController
from aihub_api.routes.knowledge.KnowledgeController import KnowledgeController
from aihub_api.routes.memory import OrganizationMemoryController, UserMemoryController
from aihub_api.routes.model.ModelController import ModelController
from aihub_api.routes.my_account.MyAccountController import MyAccountController
from aihub_api.routes.notification.NotificationController import NotificationController
from aihub_api.routes.openai.OpenaiController import OpenaiController
from aihub_api.routes.parsing.ParsingController import ParsingController
from aihub_api.routes.process.ProcessController import ProcessController
from aihub_api.routes.role.RoleController import RoleController
from aihub_api.routes.suite.SuiteController import SuiteController
from aihub_api.routes.thread.ThreadController import ThreadController
from aihub_api.routes.token.TokenController import TokenController
from aihub_api.routes.translation.TranslationController import TranslationController
from aihub_api.routes.user.UserController import UserController
from aihub_api.runners.ApiRunner import ApiRunner

enable_logging()


runner = ApiRunner()
auth = TokenAndOauth2Handler.from_auth_settings()


runner.mount(
    ApiHealthController(auth=auth).get_health().get_ready(),
    SuiteController(auth=auth).get_suite(),
    MyAccountController(auth=auth).get_my_account().get_my_dashboard().update_my_dashboard(),
    UserController(auth=auth).get_user().get_users(),
    I18nController(auth=auth).get_my_locale(),
    EventController(auth=auth).ws().get_agent_events_in_thread().get_agent_event_timeseries(),
    ModelController(auth=auth).get_litellm_models().get_litellm_models_by_mode().get_litellm_model(),
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
    ProcessController(auth=auth)
    .get_process_classes()
    .get_process_class()
    .get_process_class_instances()
    .create_process_instance()
    .get_process_instance()
    .update_process_instance()
    .delete_process_instance()
    .get_all_process_instances()
    .get_process_walkthroughs()
    .get_process_start_forms()
    .get_process_open_forms()
    .send_process_start_form()
    .send_process_open_form(),
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
    DatasetController(auth=auth).create_dataset().get_datasets().get_dataset().update_dataset(),
    KnowledgeController(
        auth=auth,
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
    .get_supported_file_types()
    .get_document_url(),
    FileController(auth=auth).get_file_url().get_anonymous_file_url().get_anonymous_file_redirect(),
    NotificationController(auth=auth).get_notifications().update_notifications().update_notification(),
    UserMemoryController(auth=auth)
    .get_user_memories()
    .search_user_memories()
    .delete_user_memory()
    .delete_all_user_memories()
    .update_user_memory(),
    OrganizationMemoryController(auth=auth)
    .get_organization_memories()
    .search_organization_memories()
    .delete_organization_memory()
    .delete_all_organization_memories()
    .update_organization_memory(),
    ParsingController(auth=auth).parse_document(),
    TranslationController(auth=auth).translate(),
)


app = runner.create_app()
