from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_handler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.routes import HealthController

from swiss_ai_hub.bot.routes.agent.agent_chat_controller import AgentChatController
from swiss_ai_hub.bot.routes.bot_in_the_loop.bot_in_the_loop_controller import BotInTheLoopController
from swiss_ai_hub.bot.routes.openai.openai_chat_controller import OpenaiChatController
from swiss_ai_hub.bot.runners.bot_runner import BotRunner

enable_logging()

runner = BotRunner()

# Controllers require an auth handler, but the Bot API performs actual authentication via Bot Framework credentials
# stored in the database (RoutesService.get_adapter).
# DangerousDevelopmentOnlyAuthHandler is used here as a placeholder since bot endpoints are not directly accessible -
# they only process authenticated Bot Framework activities.
auth = DangerousDevelopmentOnlyAuthHandler()

runner.mount(
    HealthController(auth=auth).get_health(),
    OpenaiChatController(auth=auth).json_chat_completion().stream_chat_completion(),
    AgentChatController(auth=auth).completions_json().completions_stream(),
    BotInTheLoopController(auth=auth).bot_in_the_loop_response(),
)

app = runner.create_app()
