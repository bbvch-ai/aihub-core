from unittest.mock import AsyncMock, patch

import pytest

OPENWEBUI_PROVISIONER = "aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.OpenWebuiProvisioner"
LANGFUSE_PROVISIONER = "aihub_lib.infrastructure.langfuse.LangfuseProvisioner.LangfuseProvisioner"
ACCESS_CHANGE_HOOK = "aihub_lib.persistence.access.AccessChangeHook.AccessChangeHook"


@pytest.fixture(autouse=True, scope="session")
def _skip_external_provisioning():
    """Skip OpenWebUI and Langfuse provisioning during tests (not available in CI)."""
    with (
        patch(f"{OPENWEBUI_PROVISIONER}.initialize"),
        patch(f"{OPENWEBUI_PROVISIONER}.provision", new_callable=AsyncMock),
        patch(f"{OPENWEBUI_PROVISIONER}.sync_access", new_callable=AsyncMock),
        patch(f"{LANGFUSE_PROVISIONER}.provision", new_callable=AsyncMock),
        patch(f"{ACCESS_CHANGE_HOOK}.connect"),
    ):
        yield
