from aihub_bot.routes.openai.OpenaiChatController import OpenaiChatController
from aihub_bot.runners.BotRunner import BotRunner
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.testing.logging.logger import enable_logging
from app.BotRunnerSettings import BotRunnerSettings

enable_logging()

runner = BotRunner()
bot_runner_settings=BotRunnerSettings()

runner.mount(
    HealthController().get_health(),
    OpenaiChatController(
        chat_models=[
            AzureOpenAILLMConfig(
                name="gpt-4o-mini",
                base_url=bot_runner_settings.MODEL_URL,
                api_version="2023-12-01-preview",
                prompt_tokens_costs_per_thousand=0.00013027,
                completion_tokens_costs_per_thousand=0.0005211,
                api_key=bot_runner_settings.MODEL_API_KEY
            ),
        ]
    )
    .json_chat_completion()
    .stream_chat_completion(),
)

app = runner.get_app()