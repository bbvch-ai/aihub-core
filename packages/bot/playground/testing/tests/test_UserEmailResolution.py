"""Tests for shared user-email / identity resolution in ``CompletionHandler``.

Regression coverage for issue #1314: the agent Teams bot used the Teams *display
name* (e.g. ``John Doe``) as the Keycloak lookup key, so every user whose display
name was not literally their email failed with
``User with email '...' not found in Keycloak``.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from microsoft_agents.activity import Activity, ChannelAccount, ConversationAccount
from microsoft_agents.activity.teams import TeamsChannelAccount
from microsoft_agents.hosting.core import TeamsConnectorClient, TurnContext
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.routes import ChatService
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_tenant_identity
from swiss_ai_hub.core.testing.auth_utils.user_mocks import register_fake_keycloak_user

from swiss_ai_hub.bot.bots.chat.agent.agent_completion_handler import AgentCompletionHandler
from swiss_ai_hub.bot.bots.chat.completion_handler import CompletionHandler

DISPLAY_NAME = "John Doe"
RESOLVED_EMAIL = "john.doe@example.com"
USER_AAD_ID = "29:aad-object-id"
CONVERSATION_ID = "conversation-1"


def _make_turn_context(
    *,
    from_name: str,
    from_id: str = USER_AAD_ID,
    connector_client: object | None = None,
) -> TurnContext:
    """Builds a minimal ``TurnContext`` for a single inbound message activity."""
    activity = Activity(
        type="message",
        from_property=ChannelAccount(id=from_id, name=from_name),
        conversation=ConversationAccount(id=CONVERSATION_ID),
        recipient=ChannelAccount(id="bot-1", name="Assistant"),
    )
    turn_context = TurnContext(MagicMock(), activity)
    if connector_client is not None:
        turn_context.turn_state["ConnectorClient"] = connector_client
    return turn_context


def _teams_connector(email: str | None) -> MagicMock:
    """A fake ``TeamsConnectorClient`` whose ``get_conversation_member`` yields the given email."""
    # ``TeamsChannelAccount.email`` rejects an explicit ``None``; omit it to model a member
    # whose email is unknown.
    account_fields = {"id": USER_AAD_ID, "name": DISPLAY_NAME}
    if email is not None:
        account_fields["email"] = email
    connector = MagicMock(spec=TeamsConnectorClient)
    connector.get_conversation_member = AsyncMock(return_value=TeamsChannelAccount(**account_fields))
    return connector


@pytest.mark.asyncio
async def test_resolve_email_uses_teams_connector_for_display_name():
    """Display name in ``from_property.name`` → email comes from the Teams connector."""
    connector = _teams_connector(RESOLVED_EMAIL)
    turn_context = _make_turn_context(from_name=DISPLAY_NAME, connector_client=connector)

    email = await CompletionHandler.resolve_user_email(turn_context)

    assert email == RESOLVED_EMAIL
    connector.get_conversation_member.assert_awaited_once_with(CONVERSATION_ID, USER_AAD_ID)


@pytest.mark.asyncio
async def test_resolve_email_raises_for_display_name_without_connector():
    """Issue #1314 symptom: a display name with no connector cannot be resolved."""
    turn_context = _make_turn_context(from_name=DISPLAY_NAME)

    with pytest.raises(ValueError, match="Could not determine email"):
        await CompletionHandler.resolve_user_email(turn_context)


@pytest.mark.asyncio
async def test_resolve_email_falls_back_to_name_when_name_is_email():
    """Emulator / dev channels put an email straight into ``from_property.name``."""
    turn_context = _make_turn_context(from_name=RESOLVED_EMAIL)

    email = await CompletionHandler.resolve_user_email(turn_context)

    assert email == RESOLVED_EMAIL


@pytest.mark.asyncio
async def test_resolve_email_raises_when_connector_has_no_email():
    """A Teams account without an email must not mask the display-name failure."""
    turn_context = _make_turn_context(from_name=DISPLAY_NAME, connector_client=_teams_connector(email=None))

    with pytest.raises(ValueError, match="Could not determine email"):
        await CompletionHandler.resolve_user_email(turn_context)


@pytest.mark.asyncio
async def test_resolve_email_ignores_non_teams_connector():
    """A non-Teams connector client is not queried; resolution uses the fallback."""
    turn_context = _make_turn_context(from_name=RESOLVED_EMAIL, connector_client=MagicMock())

    email = await CompletionHandler.resolve_user_email(turn_context)

    assert email == RESOLVED_EMAIL


@pytest.mark.asyncio
async def test_agent_completion_handler_resolves_display_name_via_connector(monkeypatch):
    """The agent bot path resolves a Teams display-name activity end-to-end.

    Drives ``AgentCompletionHandler.chat_completion`` with an activity whose
    ``from_property.name`` is a display name and asserts the identity handed to
    ``ChatService`` carries the connector-resolved email — the exact scenario that
    failed before issue #1314 was fixed.
    """
    register_fake_keycloak_user(user_id="agent-user-oid", name=DISPLAY_NAME, email=RESOLVED_EMAIL)

    monkeypatch.setattr(CompletionHandler, "get_messages_by_conversation_id", lambda *a, **k: [])
    monkeypatch.setattr(CompletionHandler, "get_system_message", lambda *a, **k: None)
    monkeypatch.setattr(AuthHandler, "get_active_tenant_for_user", AsyncMock(return_value=fake_tenant_identity()))
    monkeypatch.setattr(UserTenantRoleEntity, "get_roles_for_user_in_tenant", MagicMock(return_value=["admin"]))

    captured: dict = {}

    async def _capture_chat_interaction(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    monkeypatch.setattr(ChatService, "start_json_chat_interaction", _capture_chat_interaction)

    turn_context = _make_turn_context(from_name=DISPLAY_NAME, connector_client=_teams_connector(RESOLVED_EMAIL))

    await AgentCompletionHandler.chat_completion(
        turn_context=turn_context,
        path="/api/v1/agent/chat/completions/Agent/agent-1/json",
        agent_class="Agent",
        agent_id="agent-1",
        nc=MagicMock(),
        external_agent_event_distributor=MagicMock(),
        stream=False,
    )

    assert captured["user"].email == RESOLVED_EMAIL
    assert captured["user"].id == "agent-user-oid"
