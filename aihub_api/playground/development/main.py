import asyncio

from aihub_api.routes.agent_dynamic.DynamicAgentController import DynamicAgentController
from aihub_api.routes.event.EventController import EventController
from aihub_api.routes.i18n.I18nController import I18nController
from aihub_api.routes.openai.OpenaiController import OpenaiController
from aihub_api.routes.thread.ThreadController import ThreadController
from aihub_api.routes.token.TokenController import TokenController
from aihub_api.routes.user.UserController import UserController
from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_lib.auth.dependencies.TokenAndOauth2Handler.TokenAndOauth2Handler import TokenAndOauth2Handler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.dependencies.OpenWebuiAuthHandler.OpenWebuiAuthHandler import OpenWebuiAuthHandler
from aihub_lib.generative_ai.resources.models.image.azure.AzureImageModelConfig import AzureOpenaiImageModelConfig
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.generative_ai.resources.models.llm.chat.self_hosted.SelfHostedLLMConfig import SelfHostedLLMConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.self_hosted.SelfHostedEmbeddingConfig import (
    SelfHostedEmbeddingConfig,
)
from aihub_lib.generative_ai.resources.models.stt.azure.AzureSTTConfig import AzureOpenaiSTTConfig
from aihub_lib.generative_ai.resources.models.tts.azure.AzureTTSConfig import AzureOpenaiTTSConfig
from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


async def main():
    runner = ApiTestRunner()

    auth = TokenAndOauth2Handler(
        OpenWebuiAuthHandler(),
        OAuth2AuthHandler(),
    )

    runner.mount(
        HealthController().get_health(),
        UserController(auth=auth).get_user(),
        I18nController(auth=auth).get_my_locale(),
        EventController(auth=auth).ws().get_events(),
        ThreadController(auth=auth)
        .get_user_threads()
        .create_thread()
        .get_thread()
        .add_agent_to_thread()
        .remove_agent_from_thread()
        .add_user_to_thread()
        .remove_user_from_thread(),
        DynamicAgentController(auth=auth).get_agent().discover_agents(),
        TokenController().create_token().list_tokens().revoke_token(),
        OpenaiController(
            auth=auth,
            embedding_models=[
                SelfHostedEmbeddingConfig(
                    name="Alibaba-NLP/gte-base-en-v1.5",
                    base_url="http://localhost:8183",
                ),
                AzureOpenAIEmbeddingConfig(
                    name="text-embedding-3-large",
                    base_url="https://aihub-dev-openai-swe-whisper.openai.azure.com",
                    api_version="2023-12-01-preview",
                    embedding_tokens_costs_per_thousand=0.0,
                ),
            ],
            chat_models=[
                SelfHostedLLMConfig(
                    name="unsloth/Llama-3.2-1B-Instruct",
                    base_url="http://localhost:8182/v1",
                    is_function_calling_model=False,
                    context_size=512,
                ),
                AzureOpenAILLMConfig(
                    name="gpt-4o",
                    base_url="https://aihub-dev-openai-swe-whisper.openai.azure.com",
                    api_version="2024-08-01-preview",
                    prompt_tokens_costs_per_thousand=0.0045,
                    completion_tokens_costs_per_thousand=0.0133,
                ),
                AzureOpenAILLMConfig(
                    name="o1-mini",
                    base_url="https://aihub-dev-openai-swe-whisper.openai.azure.com",
                    api_version="2024-08-01-preview",
                    prompt_tokens_costs_per_thousand=0.0045,
                    completion_tokens_costs_per_thousand=0.0133,
                ),
            ],
            image_models=[
                AzureOpenaiImageModelConfig(
                    name="dall-e-3",
                    base_url="https://aihub-dev-openai-swe-whisper.openai.azure.com",
                    api_version="2024-02-01",
                )
            ],
            stt_models=[
                AzureOpenaiSTTConfig(
                    name="whisper-1",
                    base_url="https://aihub-dev-openai-swe-whisper.openai.azure.com",
                    api_version="2024-06-01",
                )
            ],
            tts_models=[
                AzureOpenaiTTSConfig(
                    name="tts-1-hd",
                    base_url="https://aihub-dev-openai-swe-whisper.openai.azure.com",
                    api_version="2024-05-01-preview",
                )
            ],
        )
        .get_models_with_assistants()
        .get_model_with_assistants()
        .get_embeddings()
        .chat_completion_with_assistants()
        .generate_image()
        .stt()
        .tts(),
    )

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
