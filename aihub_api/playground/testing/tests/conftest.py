from unittest.mock import AsyncMock, patch

import pytest

OPENWEBUI_PROVISIONER = "aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.OpenWebuiProvisioner"
ACCESS_CHANGE_HOOK = "aihub_lib.persistence.access.AccessChangeHook.AccessChangeHook"


@pytest.fixture(autouse=True)
def _skip_openwebui_provisioning():
    """Skip OpenWebUI provisioning and access hooks during tests (no OpenWebUI in CI)."""
    with (
        patch(f"{OPENWEBUI_PROVISIONER}.initialize"),
        patch(f"{OPENWEBUI_PROVISIONER}.provision", new_callable=AsyncMock),
        patch(f"{OPENWEBUI_PROVISIONER}.sync_access", new_callable=AsyncMock),
        patch(f"{ACCESS_CHANGE_HOOK}.connect"),
    ):
        yield
