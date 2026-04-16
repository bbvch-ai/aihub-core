from unittest.mock import AsyncMock, patch

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import pytest  # noqa: E402
from swiss_ai_hub.core.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: E402, F401
from swiss_ai_hub.core.testing.auth_utils.tenant_mocks import mock_tenant_entity_autouse  # noqa: E402, F401
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: E402, F401

# Must be imported before anything that constructs ``AIHubSettings`` — the module
# sets ``AIHUB_MONGO_MAIN_DB_NAME=aihub_test`` at import time so the test DB is used.
from swiss_ai_hub.core.testing.db_isolation import _isolate_test_db  # noqa: E402, F401

OPENWEBUI_PROVISIONER = "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.OpenWebuiProvisioner"
LANGFUSE_PROVISIONER = "swiss_ai_hub.core.infrastructure.langfuse.langfuse_provisioner.LangfuseProvisioner"
ACCESS_CHANGE_HOOK = "swiss_ai_hub.core.persistence.access.access_change_hook.AccessChangeHook"


@pytest.fixture(autouse=True, scope="session")
def _skip_external_provisioning():
    """Skip OpenWebUI and Langfuse provisioning during tests (not available in CI)."""
    with (
        patch(f"{OPENWEBUI_PROVISIONER}.provision", new_callable=AsyncMock),
        patch(f"{OPENWEBUI_PROVISIONER}.sync_access", new_callable=AsyncMock),
        patch(f"{OPENWEBUI_PROVISIONER}.sync_agents", new_callable=AsyncMock),
        patch(f"{LANGFUSE_PROVISIONER}.provision", new_callable=AsyncMock),
        patch(f"{ACCESS_CHANGE_HOOK}.connect"),
    ):
        yield
