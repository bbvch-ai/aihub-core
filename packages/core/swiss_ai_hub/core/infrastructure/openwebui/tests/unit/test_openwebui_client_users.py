from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from scim2_client.errors import SCIMResponseError
from scim2_models import User

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_client import OpenWebuiClient

EMAIL = "new.user@example.com"
KEYCLOAK_SUB = "92f366d1-17e2-4d65-8ac8-42610479054f"
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
        scim = AsyncMock()
        scim.create.side_effect = CONFLICT
        scim.query.return_value = SimpleNamespace(resources=[existing])

        result = await _create(owui_client, scim)

        assert result is existing

    @pytest.mark.asyncio
    async def test_should_look_up_existing_account_by_email(self, owui_client: OpenWebuiClient) -> None:
        scim = AsyncMock()
        scim.create.side_effect = CONFLICT
        scim.query.return_value = SimpleNamespace(resources=[_scim_user(EMAIL, "owui-existing")])

        await _create(owui_client, scim)

        assert scim.query.await_args.kwargs["search_request"].filter == f'userName eq "{EMAIL}"'

    @pytest.mark.asyncio
    async def test_should_raise_when_create_fails_and_no_account_exists(self, owui_client: OpenWebuiClient) -> None:
        scim = AsyncMock()
        scim.create.side_effect = CONFLICT
        scim.query.return_value = SimpleNamespace(resources=[])

        with pytest.raises(SCIMResponseError):
            await _create(owui_client, scim)
