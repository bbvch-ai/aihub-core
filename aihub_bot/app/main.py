from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.routes.health.HealthController import HealthController

from aihub_bot.routes.agent.AgentChatController import AgentChatController
from aihub_bot.routes.bot_in_the_loop.BotInTheLoopController import BotInTheLoopController
from aihub_bot.routes.openai.OpenaiChatController import OpenaiChatController
from aihub_bot.runners.BotRunner import BotRunner

enable_logging()

runner = BotRunner()

# Controllers require an auth handler, but the Bot API performs actual authentication via Bot Framework credentials
# stored in the database (RoutesService.get_adapter).
# DangerousDevelopmentOnlyAuthHandler is used here as a placeholder since bot endpoints are not directly accessible -
# they only process authenticated Bot Framework activities.
auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())

runner.mount(
    HealthController(auth=auth).get_health(),
    OpenaiChatController(auth=auth).json_chat_completion().stream_chat_completion(),
    AgentChatController(auth=auth).completions_json().completions_stream(),
    BotInTheLoopController(auth=auth).bot_in_the_loop_response(),
)

app = runner.create_app()
