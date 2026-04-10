from unittest.mock import AsyncMock, patch

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import pytest  # noqa: E402
from swiss_ai_hub.core.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: E402, F401
from swiss_ai_hub.core.testing.auth_utils.tenant_mocks import mock_tenant_entity_autouse  # noqa: E402, F401
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: E402, F401

OPENWEBUI_PROVISIONER = "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.OpenWebuiProvisioner"
LANGFUSE_PROVISIONER = "swiss_ai_hub.core.infrastructure.langfuse.langfuse_provisioner.LangfuseProvisioner"


@pytest.fixture(autouse=True, scope="session")
def _skip_external_provisioning():
    with (
        patch(f"{OPENWEBUI_PROVISIONER}.sync_agents", new_callable=AsyncMock),
        patch(f"{LANGFUSE_PROVISIONER}.provision", new_callable=AsyncMock),
    ):
        yield
