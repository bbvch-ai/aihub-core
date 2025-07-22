from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.routes.evaluation.EvaluationController import EvaluationController
from aihub_api.routes.event.EventController import EventController
from aihub_api.routes.file.FileController import FileController
from aihub_api.routes.i18n.I18nController import I18nController
from aihub_api.routes.knowledge.KnowledgeController import KnowledgeController
from aihub_api.routes.openai.OpenaiController import OpenaiController
from aihub_api.routes.process.ProcessController import ProcessController
from aihub_api.routes.role.RoleController import RoleController
from aihub_api.routes.thread.ThreadController import ThreadController
from aihub_api.routes.token.TokenController import TokenController
from aihub_api.routes.user.UserController import UserController
from aihub_api.runners.ApiRunner import ApiRunner
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.dependencies.OpenWebuiAuthHandler.OpenWebuiAuthHandler import OpenWebuiAuthHandler
from aihub_lib.auth.dependencies.TokenAndOauth2Handler.TokenAndOauth2Handler import TokenAndOauth2Handler
from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
from aihub_lib.auth.identity.AzureIdentityProvider.AzureIdentityProvider import AzureIdentityProvider
from aihub_lib.generative_ai.resources.models.image.azure.AzureImageModelConfig import AzureOpenaiImageModelConfig
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
    AzureOpenAIEmbeddingParameter,
)
from aihub_lib.generative_ai.resources.models.stt.azure.AzureSTTConfig import AzureOpenaiSTTConfig
from aihub_lib.generative_ai.resources.models.tts.azure.AzureTTSConfig import AzureOpenaiTTSConfig
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import create_milvus_vector_store
from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.testing.logging.logger import enable_logging
from app.ApiRunnerSettings import ApiRunnerSettings

enable_logging()


runner = ApiRunner()
auth = TokenAndOauth2Handler(
    bearer_handlers=[OpenWebuiAuthHandler(identity_provider=AzureIdentityProvider()), TokenAuthHandler(identity_provider=AzureIdentityProvider())],
    oauth2_handlers=[OAuth2AuthHandler(identity_provider=AzureIdentityProvider())],
)

api_runner_settings = ApiRunnerSettings()

runner.mount(
    HealthController(auth=auth).get_health(),
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
    AgentController(auth=auth).get_agent().get_agent_threads().get_agents().discover_agents(),
    ProcessController(auth=auth)
    .get_process()
    .get_processes()
    .discover_processes()
    .get_process_start_forms()
    .get_process_open_forms()
    .send_process_start_form()
    .send_process_open_form(),
    TokenController(auth=auth).create_token().list_tokens().revoke_token(),
    RoleController(auth=auth).get_role().get_roles().create_role().update_role().delete_role(),
    OpenaiController(
        auth=auth,
        embedding_models=[
            AzureOpenAIEmbeddingConfig(
                name="text-embedding-3-large",
                base_url=api_runner_settings.MODEL_SUI_URL,
                api_key=api_runner_settings.MODEL_SUI_API_KEY,
                api_version="2023-05-15",
                embedding_tokens_costs_per_thousand=0.000118,
                default_parameter=AzureOpenAIEmbeddingParameter(dimensions=1536),
            ),
            AzureOpenAIEmbeddingConfig(
                name="text-embedding-3-small",
                base_url=api_runner_settings.MODEL_SUI_URL,
                api_key=api_runner_settings.MODEL_SUI_API_KEY,
                api_version="2023-05-15",
                embedding_tokens_costs_per_thousand=0.000118,
            ),
        ],
        chat_models=[
            AzureOpenAILLMConfig(
                name="gpt-4o-mini",
                base_url=api_runner_settings.MODEL_SUI_URL,
                api_key=api_runner_settings.MODEL_SUI_API_KEY,
                api_version="2025-01-01-preview",
                prompt_tokens_costs_per_thousand=0.00013599,
                completion_tokens_costs_per_thousand=0.000544,
            ),
            AzureOpenAILLMConfig(
                name="gpt-4o",
                base_url=api_runner_settings.MODEL_SUI_URL,
                api_key=api_runner_settings.MODEL_SUI_API_KEY,
                api_version="2025-01-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
            ),
        ],
        image_models=[
            AzureOpenaiImageModelConfig(
                name="dall-e-3",
                base_url=api_runner_settings.MODEL_EUR_URL,
                api_key=api_runner_settings.MODEL_EUR_API_KEY,
                api_version="2024-02-01",
            )
        ],
        stt_models=[
            AzureOpenaiSTTConfig(
                name="whisper",
                base_url=api_runner_settings.MODEL_SUI_URL,
                api_key=api_runner_settings.MODEL_SUI_API_KEY,
                api_version="2024-06-01",
            )
        ],
        tts_models=[
            AzureOpenaiTTSConfig(
                name="tts",
                base_url=api_runner_settings.MODEL_EUR_URL,
                api_key=api_runner_settings.MODEL_EUR_API_KEY,
                api_version="2024-05-01-preview",
            )
        ],
    )
    .get_models_with_assistants(exclude_webui_agents=True)
    .get_model_with_assistants()
    .get_embeddings()
    .chat_completion_with_assistants()
    .generate_image()
    .stt()
    .tts(),
    EvaluationController(
        auth=auth,
        judge=AzureOpenAILLMConfig(
            name="gpt-4o",
            base_url=api_runner_settings.MODEL_SUI_URL,
            api_version="2025-01-01-preview",
            prompt_tokens_costs_per_thousand=0.0045,
            completion_tokens_costs_per_thousand=0.0133,
            api_key=api_runner_settings.MODEL_SUI_API_KEY,
        ),
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
            "http://localhost:19530", collection, 3072
        ),
    )
    .get_databases()
    .get_documents_for_namespace()
    .get_document_by_id()
    .get_nodes_for_document()
    .get_summary_nodes_for_document(),
    FileController(auth=auth)
        .get_file_url()
        .get_file_redirect()
        .get_anonymous_file_url()
        .get_anonymous_file_redirect(),
)


app = runner.get_app()