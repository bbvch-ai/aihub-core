from aihub_lib.routes.health.HealthController import HealthController
from aihub_lib.testing.logging.logger import enable_logging

from aihub_bot.routes.openai.OpenaiChatController import OpenaiChatController
from aihub_bot.runners.BotRunner import BotRunner

enable_logging()

runner = BotRunner()

runner.mount(
    HealthController().get_health(),
    OpenaiChatController().json_chat_completion().stream_chat_completion(),
)

app = runner.get_app()
