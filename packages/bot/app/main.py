from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler import KeycloakAuthHandler
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.routes import HealthController

from swiss_ai_hub.bot.routes import AgentChatController, BotInTheLoopController, OpenaiChatController
from swiss_ai_hub.bot.runners import BotRunner

enable_logging()

runner = BotRunner()

# Activity routes verify the Azure Bot Service token themselves (`RoutesService.process_activity`); no route depends
# on `auth`, which only satisfies the `Controller` constructor.
auth = KeycloakAuthHandler()

runner.mount(
    HealthController(auth=auth).get_health(),
    OpenaiChatController(auth=auth).json_chat_completion().stream_chat_completion(),
    AgentChatController(auth=auth).completions_json().completions_stream(),
    BotInTheLoopController(auth=auth).bot_in_the_loop_response(),
)

app = runner.create_app()
