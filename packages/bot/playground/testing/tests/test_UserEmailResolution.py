"""Tests for user-email / identity resolution and agent access in ``CompletionHandler``.

The identity must come from the channel (Teams member roster, Slack user profile), never from the
sender-controlled ``from.name``; channels without such a lookup are rejected.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from microsoft_agents.activity import Activity, ChannelAccount, Channels, ConversationAccount
from microsoft_agents.activity.teams import TeamsChannelAccount
from microsoft_agents.hosting.core import TeamsConnectorClient, TurnContext
from swiss_ai_hub.core.auth import AccessChecker, UserNotProvisionedError
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.routes import ChatService
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_tenant_identity
from swiss_ai_hub.core.testing.auth_utils.user_mocks import register_fake_keycloak_user

from swiss_ai_hub.bot.bots.chat.agent.agent_completion_handler import AgentCompletionHandler
from swiss_ai_hub.bot.bots.chat.bot_access_denied_error import BotAccessDeniedError
from swiss_ai_hub.bot.bots.chat.completion_handler import CompletionHandler
from swiss_ai_hub.bot.bots.chat.openai.openai_completion_handler import OpenaiCompletionHandler
from swiss_ai_hub.bot.bots.chat.unverified_bot_user_error import UnverifiedBotUserError
from swiss_ai_hub.bot.persistence.entities.path_entity import PathEntity
from swiss_ai_hub.bot.routes.bot_in_the_loop.slack_utils import SlackUtils

DISPLAY_NAME = "John Doe"
RESOLVED_EMAIL = "john.doe@example.com"
VICTIM_EMAIL = "victim@example.com"
USER_AAD_ID = "29:aad-object-id"
SLACK_USER_ID = "U012AB3CD"
SLACK_SENDER_ID = f"{SLACK_USER_ID}:T0123ABC"
CONVERSATION_ID = "conversation-1"
PATH = "/api/v1/agent/chat/completions/Agent/agent-1/json"


def _make_turn_context(
    *,
    channel_id: str = Channels.ms_teams,
    from_name: str = DISPLAY_NAME,
    from_id: str | None = USER_AAD_ID,
    connector_client: object | None = None,
) -> TurnContext:
    """Builds a minimal ``TurnContext`` for a single inbound message activity."""
    from_fields: dict = {"name": from_name}
    if from_id is not None:
        from_fields["id"] = from_id
    activity = Activity(
        type="message",
        channel_id=channel_id,
        from_property=ChannelAccount(**from_fields),
        conversation=ConversationAccount(id=CONVERSATION_ID),
        recipient=ChannelAccount(id="bot-1", name="Assistant"),
    )
    turn_context = TurnContext(MagicMock(), activity)
    if connector_client is not None:
        turn_context.turn_state["ConnectorClient"] = connector_client
    return turn_context


def _teams_connector(email: str | None) -> MagicMock:
    """A fake ``TeamsConnectorClient`` whose ``get_conversation_member`` yields the given email."""
    account_fields = {"id": USER_AAD_ID, "name": DISPLAY_NAME}
    if email is not None:
        account_fields["email"] = email
    connector = MagicMock(spec=TeamsConnectorClient)
    connector.get_conversation_member = AsyncMock(return_value=TeamsChannelAccount(**account_fields))
    return connector


@pytest.fixture
def slack_lookup(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    monkeypatch.setattr(PathEntity, "get_slack_token_by_path", MagicMock(return_value="xoxb-token"))
    lookup = AsyncMock(return_value=RESOLVED_EMAIL)
    monkeypatch.setattr(SlackUtils, "get_user_email", lookup)
    return lookup


@pytest.fixture
def provisioned_user(monkeypatch: pytest.MonkeyPatch) -> None:
    register_fake_keycloak_user(user_id="agent-user-oid", name=DISPLAY_NAME, email=RESOLVED_EMAIL)
    monkeypatch.setattr(AuthHandler, "get_active_tenant_for_user", AsyncMock(return_value=fake_tenant_identity()))
    monkeypatch.setattr(UserTenantRoleEntity, "get_roles_for_user_in_tenant", MagicMock(return_value=["member"]))


@pytest.fixture
def no_conversation_history(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CompletionHandler, "get_messages_by_conversation_id", lambda *a, **k: [])
    monkeypatch.setattr(CompletionHandler, "get_system_message", lambda *a, **k: None)


def _grant_rules(monkeypatch: pytest.MonkeyPatch, rules: list[str]) -> None:
    monkeypatch.setattr(RoleEntity, "get_access_rules_for_roles", MagicMock(return_value=rules))


@pytest.mark.asyncio
async def test_teams_email_comes_from_the_member_roster():
    connector = _teams_connector(RESOLVED_EMAIL)
    turn_context = _make_turn_context(from_name=VICTIM_EMAIL, connector_client=connector)

    email = await CompletionHandler.resolve_user_email(turn_context, PATH)

    assert email == RESOLVED_EMAIL
    connector.get_conversation_member.assert_awaited_once_with(CONVERSATION_ID, USER_AAD_ID)


@pytest.mark.asyncio
async def test_teams_without_connector_is_rejected_even_when_name_is_an_email():
    turn_context = _make_turn_context(from_name=VICTIM_EMAIL)

    with pytest.raises(UnverifiedBotUserError):
        await CompletionHandler.resolve_user_email(turn_context, PATH)


@pytest.mark.asyncio
async def test_teams_non_teams_connector_is_rejected():
    turn_context = _make_turn_context(from_name=VICTIM_EMAIL, connector_client=MagicMock())

    with pytest.raises(UnverifiedBotUserError):
        await CompletionHandler.resolve_user_email(turn_context, PATH)


@pytest.mark.asyncio
async def test_teams_member_without_email_is_rejected():
    turn_context = _make_turn_context(connector_client=_teams_connector(email=None))

    with pytest.raises(UnverifiedBotUserError):
        await CompletionHandler.resolve_user_email(turn_context, PATH)


@pytest.mark.asyncio
async def test_teams_missing_sender_id_skips_lookup_and_is_rejected():
    connector = _teams_connector(RESOLVED_EMAIL)
    turn_context = _make_turn_context(from_name=VICTIM_EMAIL, from_id=None, connector_client=connector)

    with pytest.raises(UnverifiedBotUserError):
        await CompletionHandler.resolve_user_email(turn_context, PATH)
    connector.get_conversation_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_slack_email_comes_from_slack_user_profile(slack_lookup: AsyncMock):
    turn_context = _make_turn_context(channel_id=Channels.slack, from_name=VICTIM_EMAIL, from_id=SLACK_SENDER_ID)

    email = await CompletionHandler.resolve_user_email(turn_context, PATH)

    assert email == RESOLVED_EMAIL
    slack_lookup.assert_awaited_once_with("xoxb-token", SLACK_USER_ID)


@pytest.mark.asyncio
async def test_slack_malformed_sender_id_is_rejected(slack_lookup: AsyncMock):
    turn_context = _make_turn_context(channel_id=Channels.slack, from_id="not-a-slack-id")

    with pytest.raises(UnverifiedBotUserError):
        await CompletionHandler.resolve_user_email(turn_context, PATH)
    slack_lookup.assert_not_awaited()


@pytest.mark.asyncio
async def test_slack_without_token_is_rejected(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(PathEntity, "get_slack_token_by_path", MagicMock(return_value=None))
    turn_context = _make_turn_context(channel_id=Channels.slack, from_id=SLACK_SENDER_ID)

    with pytest.raises(UnverifiedBotUserError):
        await CompletionHandler.resolve_user_email(turn_context, PATH)


@pytest.mark.asyncio
async def test_slack_user_without_email_is_rejected(slack_lookup: AsyncMock):
    slack_lookup.return_value = None
    turn_context = _make_turn_context(channel_id=Channels.slack, from_id=SLACK_SENDER_ID)

    with pytest.raises(UnverifiedBotUserError):
        await CompletionHandler.resolve_user_email(turn_context, PATH)


@pytest.mark.parametrize("channel_id", [Channels.webchat, Channels.emulator, Channels.direct_line, "custom-channel"])
@pytest.mark.asyncio
async def test_channels_without_verified_lookup_are_rejected(channel_id: str):
    turn_context = _make_turn_context(channel_id=channel_id, from_name=VICTIM_EMAIL)

    with pytest.raises(UnverifiedBotUserError):
        await CompletionHandler.resolve_user_email(turn_context, PATH)


@pytest.mark.asyncio
async def test_resolve_user_identity_builds_identity_from_keycloak(provisioned_user: None):
    turn_context = _make_turn_context(connector_client=_teams_connector(RESOLVED_EMAIL))

    identity = await CompletionHandler.resolve_user_identity(turn_context, PATH)

    assert identity.id == "agent-user-oid"
    assert identity.email == RESOLVED_EMAIL
    assert identity.roles == ["member"]
    assert identity.is_sys_admin is False


@pytest.mark.asyncio
async def test_resolve_user_identity_raises_when_user_not_in_keycloak():
    turn_context = _make_turn_context(connector_client=_teams_connector("ghost@example.com"))

    with pytest.raises(UserNotProvisionedError, match="not provisioned in Keycloak") as excinfo:
        await CompletionHandler.resolve_user_identity(turn_context, PATH)
    assert excinfo.value.email == "ghost@example.com"


@pytest.mark.asyncio
async def test_agent_completion_runs_as_the_roster_user_with_access(
    monkeypatch: pytest.MonkeyPatch, provisioned_user: None, no_conversation_history: None
):
    _grant_rules(monkeypatch, [AccessChecker.agent_instance_user_rule("Agent", "agent-1")])
    start_interaction = AsyncMock(return_value=MagicMock())
    monkeypatch.setattr(ChatService, "start_json_chat_interaction", start_interaction)
    turn_context = _make_turn_context(from_name=VICTIM_EMAIL, connector_client=_teams_connector(RESOLVED_EMAIL))

    await AgentCompletionHandler.chat_completion(
        turn_context=turn_context,
        path=PATH,
        agent_class="Agent",
        agent_id="agent-1",
        nc=MagicMock(),
        external_agent_event_distributor=MagicMock(),
        stream=False,
    )

    user = start_interaction.await_args.kwargs["user"]
    assert user.email == RESOLVED_EMAIL
    assert user.id == "agent-user-oid"


@pytest.mark.asyncio
async def test_agent_completion_is_refused_without_agent_access(
    monkeypatch: pytest.MonkeyPatch, provisioned_user: None, no_conversation_history: None
):
    _grant_rules(monkeypatch, [AccessChecker.agent_instance_user_rule("Agent", "other-agent")])
    start_interaction = AsyncMock()
    monkeypatch.setattr(ChatService, "start_json_chat_interaction", start_interaction)
    turn_context = _make_turn_context(connector_client=_teams_connector(RESOLVED_EMAIL))

    with pytest.raises(BotAccessDeniedError):
        await AgentCompletionHandler.chat_completion(
            turn_context=turn_context,
            path=PATH,
            agent_class="Agent",
            agent_id="agent-1",
            nc=MagicMock(),
            external_agent_event_distributor=MagicMock(),
            stream=False,
        )
    start_interaction.assert_not_awaited()


@pytest.mark.parametrize("model_name", ["text-generation/other-model", "model-without-capability"])
@pytest.mark.asyncio
async def test_openai_completion_is_refused_without_model_access(
    monkeypatch: pytest.MonkeyPatch, provisioned_user: None, no_conversation_history: None, model_name: str
):
    _grant_rules(monkeypatch, [AccessChecker.model_user_rule("text-generation", "allowed-model")])
    turn_context = _make_turn_context(connector_client=_teams_connector(RESOLVED_EMAIL))

    with pytest.raises(BotAccessDeniedError):
        await OpenaiCompletionHandler.chat_completion(
            turn_context=turn_context, path=PATH, model_name=model_name, stream=False
        )


@pytest.mark.parametrize(
    ("exception", "message_key"),
    [
        (UnverifiedBotUserError(Channels.webchat, "no lookup"), "bot.error.unverified_user"),
        (BotAccessDeniedError("agent-user-oid", "agent Agent/agent-1"), "bot.error.access_denied"),
    ],
)
@pytest.mark.asyncio
async def test_rejected_users_get_an_actionable_reply(exception: Exception, message_key: str):
    turn_context = _make_turn_context()
    turn_context.send_activity = AsyncMock()
    t = LocaleHandler().in_locale("en")

    response = await CompletionHandler.handle_exception(
        turn_context=turn_context,
        exception=exception,
        typing_task=AsyncMock()(),
        typing_stop_signal=MagicMock(),
        t=t,
    )

    assert response == t(message_key)
    assert response != t("bot.error.generic_error")
    turn_context.send_activity.assert_awaited_once()
