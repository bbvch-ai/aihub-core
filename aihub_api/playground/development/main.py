import asyncio
import os
from os.path import join, dirname, abspath, isdir

import nest_asyncio
from dotenv import load_dotenv

from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.routes.evaluation.EvaluationController import EvaluationController
from aihub_api.routes.event.EventController import EventController
from aihub_api.routes.file.FileController import FileController
from aihub_api.routes.i18n.I18nController import I18nController
from aihub_api.routes.knowledge.KnowledgeController import KnowledgeController
from aihub_api.routes.openai.OpenaiController import OpenaiController
from aihub_api.routes.suite.SuiteController import SuiteController
from aihub_api.routes.thread.ThreadController import ThreadController
from aihub_api.routes.token.TokenController import TokenController
from aihub_api.routes.user.UserController import UserController
from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.dependencies.OpenWebuiAuthHandler.OpenWebuiAuthHandler import OpenWebuiAuthHandler
from aihub_lib.auth.dependencies.TokenAndOauth2Handler.TokenAndOauth2Handler import TokenAndOauth2Handler
from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
from aihub_lib.auth.identity.AzureIdentityProvider.AzureIdentityProvider import AzureIdentityProvider
from aihub_lib.auth.identity.TokenIdentityProvider.TokenIdentityProvider import TokenIdentityProvider
from aihub_lib.generative_ai.resources.models.image.azure.AzureImageModelConfig import AzureOpenaiImageModelConfig
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.generative_ai.resources.models.llm.chat.openai_like.OpenaiLikeLLMConfig import OpenaiLikeLLMConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.self_hosted.SelfHostedEmbeddingConfig import (
    SelfHostedEmbeddingConfig,
)
from aihub_lib.generative_ai.resources.models.stt.azure.AzureSTTConfig import AzureOpenaiSTTConfig
from aihub_lib.generative_ai.resources.models.tts.azure.AzureTTSConfig import AzureOpenaiTTSConfig
from aihub_lib.nats.events import UserMessageEvent, LLMStopEvent
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import create_milvus_vector_store
from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.testing.logging.logger import enable_logging
from playground.development.DevelopmentOpenaiResourceSettings import DevelopmentOpenaiResourceSettings

load_dotenv()

enable_logging()
nest_asyncio.apply()


async def main():
    runner = ApiTestRunner()

    frontend_dir = join(
        dirname(abspath(__file__)), "..", "..", "..", "aihub_web", "aihub_web", ".playground", ".output", "public"
    )
    if isdir(join(frontend_dir, "_nuxt")):
        runner.mount_frontend(frontend_dir)

    auth = TokenAndOauth2Handler(
        bearer_handlers=[
            OpenWebuiAuthHandler(identity_provider=AzureIdentityProvider()),
            TokenAuthHandler(identity_provider=TokenIdentityProvider()),
        ],
        oauth2_handlers=[
            OAuth2AuthHandler(identity_provider=AzureIdentityProvider()),
        ],
    )
    # auth = DangerousDevelopmentOnlyAuthHandler(
    #     identity_provider=DangerousDevelopmentOnlyIdentityProvider()
    # )

    azure_openai_settings = DevelopmentOpenaiResourceSettings()

    runner.mount(
        HealthController(auth=auth).get_health(),
        SuiteController(auth=auth).get_suite(),
        UserController(auth=auth).get_my_user().get_my_dashboard().update_my_dashboard(),
        I18nController(auth=auth).get_my_locale(),
        EventController(auth=auth).ws().get_events().get_event_timeseries(),
        ThreadController(auth=auth)
        .get_user_threads()
        .create_thread()
        .get_thread()
        .add_agent_to_thread()
        .remove_agent_from_thread()
        .add_user_to_thread()
        .remove_user_from_thread(),
        AgentController(auth=auth)
        .get_agent()
        .get_agent_threads()
        .get_agents()
        .discover_agents()
        .send_event_to(
            "LLMWrappingAgent",
            "dev_agent",
            start_event_class=UserMessageEvent,
            stop_event_class=LLMStopEvent,
        ),
        TokenController(auth=auth).create_token().list_tokens().revoke_token(),
        OpenaiController(
            auth=auth,
            embedding_models=[
                SelfHostedEmbeddingConfig(
                    name="Alibaba-NLP/gte-base-en-v1.5",
                    base_url="http://localhost:8183",
                ),
                AzureOpenAIEmbeddingConfig(
                    name="text-embedding-3-large",
                    base_url="https://bbvaihub-openai-sui.openai.azure.com",
                    api_version="2024-12-01-preview",
                    embedding_tokens_costs_per_thousand=0.0,
                    api_key=azure_openai_settings.OPENAI_API_KEY,
                ),
            ],
            chat_models=[
                OpenaiLikeLLMConfig(
                    name="unsloth/Llama-3.2-1B-Instruct",
                    base_url="http://localhost:8182/v1",
                    is_function_calling_model=False,
                    context_size=512,
                ),
                AzureOpenAILLMConfig(
                    name="gpt-4o",
                    base_url="https://bbvaihub-openai-sui.openai.azure.com",
                    api_version="2025-01-01-preview",
                    prompt_tokens_costs_per_thousand=0.0045,
                    completion_tokens_costs_per_thousand=0.0133,
                    api_key=azure_openai_settings.OPENAI_API_KEY,
                ),
                AzureOpenAILLMConfig(
                    name="gpt-4o-mini",
                    base_url="https://bbvaihub-openai-sui.openai.azure.com",
                    api_version="2025-01-01-preview",
                    prompt_tokens_costs_per_thousand=0.0045,
                    completion_tokens_costs_per_thousand=0.0133,
                    api_key=azure_openai_settings.OPENAI_API_KEY,
                ),
            ],
            image_models=[
                AzureOpenaiImageModelConfig(
                    name="dall-e-3",
                    base_url="https://aihub-dev-openai-swe-whisper.openai.azure.com",
                    api_version="2024-02-01",
                    api_key=azure_openai_settings.AZURE_OPENAI_API_KEY_SWEDEN_WHISPER,
                )
            ],
            stt_models=[
                AzureOpenaiSTTConfig(
                    name="whisper-1",
                    base_url="https://aihub-dev-openai-swe-whisper.openai.azure.com",
                    api_version="2024-06-01",
                    api_key=azure_openai_settings.AZURE_OPENAI_API_KEY_SWEDEN_WHISPER,
                )
            ],
            tts_models=[
                AzureOpenaiTTSConfig(
                    name="tts-1-hd",
                    base_url="https://aihub-dev-openai-swe-whisper.openai.azure.com",
                    api_version="2024-05-01-preview",
                    api_key=azure_openai_settings.AZURE_OPENAI_API_KEY_SWEDEN_WHISPER,
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
                base_url="https://bbvaihub-openai-sui.openai.azure.com",
                api_version="2025-01-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                api_key=azure_openai_settings.OPENAI_API_KEY,
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

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
