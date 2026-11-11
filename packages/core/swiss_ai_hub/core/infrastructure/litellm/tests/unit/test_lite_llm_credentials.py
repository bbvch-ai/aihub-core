from unittest.mock import AsyncMock, patch

import pytest

from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_credentials import LiteLLMCredentials
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_customer_service import LiteLLMCustomerService
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService

pytestmark = pytest.mark.unit

HEADER = LiteLLMCustomerService.CUSTOMER_HEADER
TENANT = TenantIdentity(id="tenant-a", name="Tenant A", access_rules=[])


@pytest.mark.asyncio
async def test_a_user_gets_their_key_and_their_acting_tenant_together() -> None:
    user = UserIdentity(id="user-1", name="Ada", email="ada@example.com", roles=[], acting_within_tenant=TENANT)

    with (
        patch.object(LiteLLMService, "api_key_for_user", new=AsyncMock(return_value="sk-user")),
        patch.dict(LiteLLMCustomerService._aliases, {TENANT.id: TENANT.name}),
    ):
        credentials = await LiteLLMCredentials.for_user(user)

    assert (credentials.api_key, credentials.headers) == ("sk-user", {HEADER: "tenant-a"})


@pytest.mark.asyncio
async def test_a_call_without_a_user_keeps_the_master_key_and_books_to_no_tenant() -> None:
    credentials = await LiteLLMCredentials.for_user(None)

    assert (credentials.api_key, credentials.headers) == (None, {HEADER: LiteLLMCustomerService.NO_TENANT_CUSTOMER_ID})


def test_the_key_stays_out_of_logs() -> None:
    assert "sk-user" not in repr(LiteLLMCredentials(api_key="sk-user", headers={}))
