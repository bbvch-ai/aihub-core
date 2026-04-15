from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler import KeycloakAuthHandler
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.routes import HealthController

from swiss_ai_hub.bot.routes import AgentChatController, BotInTheLoopController, OpenaiChatController
from swiss_ai_hub.bot.runners import BotRunner

enable_logging()

runner = BotRunner()

# Bot endpoints are not directly reachable by end users — they process Bot Framework activities
# whose authenticity is verified by `RoutesService.get_adapter()` against per-endpoint credentials
# stored in MongoDB. The `auth` handler on each controller is therefore only a safety net for any
# accidental external exposure; `KeycloakAuthHandler` is the right fail-closed choice there (it
# rejects any request without a valid platform JWT).
auth = KeycloakAuthHandler()

runner.mount(
    HealthController(auth=auth).get_health(),
    OpenaiChatController(auth=auth).json_chat_completion().stream_chat_completion(),
    AgentChatController(auth=auth).completions_json().completions_stream(),
    BotInTheLoopController(auth=auth).bot_in_the_loop_response(),
)

app = runner.create_app()
