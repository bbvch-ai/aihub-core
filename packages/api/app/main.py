# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor

AihubInstrumentor().instrument()

from swiss_ai_hub.core.auth import TokenAndOauth2Handler
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.infrastructure import enable_logging

from swiss_ai_hub.api.routes import (
    AgentController,
    ApiHealthController,
    AuthProviderController,
    DatasetController,
    EventController,
    FileController,
    I18nController,
    KnowledgeController,
    ModelController,
    MyAccountController,
    NotificationController,
    OpenaiController,
    OrganizationMemoryController,
    ParsingController,
    ProcessController,
    RoleController,
    SuiteController,
    ThreadController,
    TokenController,
    TranslationController,
    UserController,
    UserMemoryController,
)
from swiss_ai_hub.api.runners import ApiRunner

enable_logging()


runner = ApiRunner()
auth = TokenAndOauth2Handler.from_auth_settings()


runner.mount(
    ApiHealthController(auth=auth).get_health().get_ready(),
    AuthProviderController(auth=auth).get_auth_providers(),
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
    .get_all_agent_instances()
    .initiate_file_upload()
    .validate_file_upload(),
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
        translation_llm_config=LLMConfig(model_name="text-generation/gpt-oss-120b"),
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
    .get_document_url()
    .delete_document(),
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
