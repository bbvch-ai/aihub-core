from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from scim2_client.errors import SCIMResponseError
from scim2_models import SearchRequest, User

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_client import OpenWebuiClient

EMAIL = "new.user@example.com"
KEYCLOAK_SUB = "92f366d1-17e2-4d65-8ac8-42610479054f"
BY_EXTERNAL_ID = f'externalId eq "{KEYCLOAK_SUB}"'
BY_EMAIL = f'userName eq "{EMAIL}"'
CONFLICT = SCIMResponseError("Expected type User but got undefined object with no schema", source={})


@pytest.fixture
def owui_client() -> OpenWebuiClient:
    return OpenWebuiClient(
        base_url="http://open-webui:8080",
        secret_key="test-secret-key-for-jwt-signing",
        scim_token="test-scim-token",
        service_account_id="00000000-0000-4000-a000-000000000001",
    )


def _scim_user(user_name: str, user_id: str) -> User:
    user = User(user_name=user_name)
    user.id = user_id
    return user


def _conflicting_scim(matches: dict[str, User]) -> AsyncMock:
    """A SCIM client whose create conflicts and whose queries only find the accounts listed per filter."""

    async def _query(_resource: type[User], search_request: SearchRequest) -> SimpleNamespace:
        match = matches.get(search_request.filter)
        return SimpleNamespace(resources=[match] if match else [])

    scim = AsyncMock()
    scim.create.side_effect = CONFLICT
    scim.query.side_effect = _query
    return scim


async def _create(owui_client: OpenWebuiClient, scim: AsyncMock) -> User:
    return await owui_client.create_user(email=EMAIL, display_name="New User", external_id=KEYCLOAK_SUB, scim=scim)


class TestCreateUser:
    @pytest.mark.asyncio
    async def test_should_create_account_keyed_by_keycloak_sub(self, owui_client: OpenWebuiClient) -> None:
        scim = AsyncMock()
        scim.create.return_value = _scim_user(EMAIL, "owui-new")

        await _create(owui_client, scim)

        sent: User = scim.create.await_args.args[0]
        assert (sent.user_name, sent.external_id, [e.value for e in sent.emails]) == (EMAIL, KEYCLOAK_SUB, [EMAIL])

    @pytest.mark.asyncio
    async def test_should_return_created_account(self, owui_client: OpenWebuiClient) -> None:
        created = _scim_user(EMAIL, "owui-new")
        scim = AsyncMock()
        scim.create.return_value = created

        result = await _create(owui_client, scim)

        assert result is created

    @pytest.mark.asyncio
    async def test_should_reuse_account_when_chat_login_created_it_first(self, owui_client: OpenWebuiClient) -> None:
        existing = _scim_user(EMAIL, "owui-existing")
        scim = _conflicting_scim({BY_EXTERNAL_ID: existing, BY_EMAIL: existing})

        result = await _create(owui_client, scim)

        assert result is existing

    @pytest.mark.asyncio
    async def test_should_reuse_account_whose_email_changed_in_keycloak(self, owui_client: OpenWebuiClient) -> None:
        """OpenWebUI keeps the old email, so only the Keycloak sub still identifies the account."""
        existing = _scim_user("old.address@example.com", "owui-existing")
        scim = _conflicting_scim({BY_EXTERNAL_ID: existing})

        result = await _create(owui_client, scim)

        assert result is existing

    @pytest.mark.asyncio
    async def test_should_fall_back_to_email_when_no_account_has_the_sub(self, owui_client: OpenWebuiClient) -> None:
        existing = _scim_user(EMAIL, "owui-existing")
        scim = _conflicting_scim({BY_EMAIL: existing})

        result = await _create(owui_client, scim)

        assert result is existing

    @pytest.mark.asyncio
    async def test_should_raise_when_create_fails_and_no_account_exists(self, owui_client: OpenWebuiClient) -> None:
        scim = _conflicting_scim({})

        with pytest.raises(SCIMResponseError):
            await _create(owui_client, scim)
