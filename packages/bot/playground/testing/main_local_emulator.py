"""Local-dev entry point for driving the bot from the Bot Framework Emulator WITHOUT Azure.

The ``microsoft-agents`` ``CloudAdapter`` always performs MSAL authentication. Even to *receive* an
activity it builds a user-token client (needs a real ``TENANT_ID``), and to *reply* it builds a
connector client that signs the request with a bearer token. With empty PathEntity credentials the
plain ``main.py`` (meant to be driven by the pytest harness) fails with ``TENANT_ID is not set`` on
inbound, and a fake token gets rejected with ``401`` by the emulator on outbound.

The SDK already has a built-in unauthenticated mode: ``RestChannelServiceClientFactory`` accepts a
``use_anonymous`` flag on both ``create_user_token_client`` (early-returns an empty-token client) and
``create_connector_client`` (uses the anonymous token provider, so no ``Authorization`` header is
sent). We force that flag on for both — exactly "this is a local unauthenticated bot" — which fixes
inbound and outbound at once. THIS IS FOR LOCAL EMULATOR USE ONLY — never an entry point for a
deployed bot.
"""

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402
import inspect  # noqa: E402


def _force_anonymous_auth() -> None:
    from microsoft_agents.hosting.core.rest_channel_service_client_factory import (
        RestChannelServiceClientFactory,
    )

    def _wrap(func):  # noqa: ANN001, ANN202
        signature = inspect.signature(func)
        if "use_anonymous" not in signature.parameters:
            # Fail loudly instead of silently mis-patching if a future microsoft-agents release
            # renames or removes the kwarg this shim depends on.
            raise RuntimeError(
                f"{func.__qualname__} no longer accepts 'use_anonymous'; the local emulator's "
                "anonymous-auth shim needs updating for this microsoft-agents version."
            )

        async def wrapper(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
            # Callers pass ``use_anonymous`` positionally, so bind everything and override it by
            # name regardless of how it arrived; then re-invoke with keyword args to avoid clashes.
            bound = signature.bind(self, *args, **kwargs)
            bound.apply_defaults()
            bound.arguments["use_anonymous"] = True
            arguments = dict(bound.arguments)
            instance = arguments.pop("self")
            return await func(instance, **arguments)

        return wrapper

    RestChannelServiceClientFactory.create_connector_client = _wrap(
        RestChannelServiceClientFactory.create_connector_client
    )
    RestChannelServiceClientFactory.create_user_token_client = _wrap(
        RestChannelServiceClientFactory.create_user_token_client
    )


_force_anonymous_auth()


def _stub_user_email_for_emulator() -> None:
    """Resolve the user's email from BOT_DEV_FAKE_EMAIL instead of the Teams connector.

    The real ``resolve_user_email`` calls ``get_conversation_member`` (a Teams-only API) which the
    Bot Framework Emulator does not implement (404). This monkeypatch — applied ONLY in this local
    runner, never in production code — short-circuits to an env-provided email so the downstream
    Keycloak/provisioning logic can be exercised from the emulator. Set BOT_DEV_FAKE_EMAIL to a
    provisioned address (happy path) or an unknown one (UserNotProvisionedError). No-op if unset.
    """
    import os

    fake_email = os.environ.get("BOT_DEV_FAKE_EMAIL")
    if not fake_email:
        return

    from swiss_ai_hub.bot.bots.chat.completion_handler import CompletionHandler

    async def _resolve(turn_context):  # noqa: ANN001
        return fake_email

    CompletionHandler.resolve_user_email = staticmethod(_resolve)


_stub_user_email_for_emulator()

from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402
from swiss_ai_hub.core.routes import HealthController  # noqa: E402
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler  # noqa: E402

from swiss_ai_hub.bot.routes.agent.agent_chat_controller import AgentChatController  # noqa: E402
from swiss_ai_hub.bot.routes.openai.openai_chat_controller import OpenaiChatController  # noqa: E402
from swiss_ai_hub.bot.runners.simulated_agent_bot_test_runner import SimulatedAgentBotTestRunner  # noqa: E402

enable_logging()


async def main():
    runner = SimulatedAgentBotTestRunner(agent_class="my_agent_class", agent_id="my_agent_id")
    runner.with_simple_chunk_events()
    auth = TestAuthHandler()

    runner.mount(
        HealthController(auth=auth).get_health(),
        AgentChatController(auth=auth).completions_json().completions_stream(),
        OpenaiChatController(auth=auth).json_chat_completion().stream_chat_completion(),
    )

    # Start the simulated agent's NATS subscribers. runner.run() normally does this before serving;
    # since we serve uvicorn directly (to bind 0.0.0.0), we must call it explicitly or the simulated
    # agent never subscribes and every chat times out waiting for a reply.
    await runner.start_simulation()

    # Bind 0.0.0.0 (not the runner's hardcoded localhost) so a Windows-hosted Bot Framework
    # Emulator can reach the server across the WSL2 boundary.
    from uvicorn import Config, Server

    server = Server(Config(app=runner.create_app(), host="0.0.0.0", port=8001, log_level="debug"))
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
