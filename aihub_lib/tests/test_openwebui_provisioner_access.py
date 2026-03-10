"""Tests for OpenWebuiProvisioner — access grant computation."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import (
    AIHUB_MODEL_PREFIX,
    OpenWebuiProvisioner,
)


@pytest.fixture
def mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.BASE_URL = "http://open-webui:8080"
    settings.SECRET_KEY = MagicMock()
    settings.SECRET_KEY.get_secret_value.return_value = "sk-test"
    settings.SCIM_TOKEN = MagicMock()
    settings.SCIM_TOKEN.get_secret_value.return_value = "scim-test"
    return settings


@pytest.fixture
def provisioner(mock_settings: MagicMock) -> OpenWebuiProvisioner:
    return OpenWebuiProvisioner(settings=mock_settings)


class TestComputeAccessForModel:
    def test_group_with_matching_rules_gets_access(self) -> None:
        groups = [{"displayName": "aihub:T1:R1", "id": "grp-1"}]
        tenant_rules = {"T1": ["aihub.user.agent.rag.*"]}
        role_rules = {"R1": ["aihub.user.agent.rag.*"]}

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert result == [{"principal_type": "group", "principal_id": "grp-1", "permission": "read"}]

    def test_group_without_matching_rules_denied(self) -> None:
        groups = [{"displayName": "aihub:T1:R1", "id": "grp-1"}]
        tenant_rules = {"T1": ["aihub.user.agent.rag.*"]}
        role_rules = {"R1": ["aihub.user.agent.other.*"]}

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert result == []

    def test_tenant_ceiling_blocks_role_access(self) -> None:
        groups = [{"displayName": "aihub:T1:R1", "id": "grp-1"}]
        tenant_rules = {"T1": ["aihub.user.agent.other.*"]}
        role_rules = {"R1": ["aihub.user.agent.rag.*"]}

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert result == []

    def test_wildcard_rules_grant_broad_access(self) -> None:
        groups = [{"displayName": "aihub:T1:R1", "id": "grp-1"}]
        tenant_rules = {"T1": ["aihub.user.agent.>"]}
        role_rules = {"R1": ["aihub.user.agent.>"]}

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert result == [{"principal_type": "group", "principal_id": "grp-1", "permission": "read"}]

    def test_empty_tenant_rules_deny_all(self) -> None:
        groups = [{"displayName": "aihub:T1:R1", "id": "grp-1"}]
        tenant_rules = {"T1": []}
        role_rules = {"R1": ["aihub.user.agent.rag.*"]}

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert result == []

    def test_multiple_groups_different_visibility(self) -> None:
        groups = [
            {"displayName": "aihub:T1:R1", "id": "grp-1"},
            {"displayName": "aihub:T1:R2", "id": "grp-2"},
        ]
        tenant_rules = {"T1": ["aihub.user.agent.>"]}
        role_rules = {
            "R1": ["aihub.user.agent.rag.*"],
            "R2": ["aihub.user.agent.llm.*"],
        }

        result_rag = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)
        result_llm = OpenWebuiProvisioner._compute_access_for_model("llm", "default", groups, tenant_rules, role_rules)

        assert result_rag == [{"principal_type": "group", "principal_id": "grp-1", "permission": "read"}]
        assert result_llm == [{"principal_type": "group", "principal_id": "grp-2", "permission": "read"}]


class TestSyncAccessGrants:
    @pytest.mark.asyncio
    async def test_sync_sets_access_grants_on_model(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._client,
                "list_models",
                return_value=[
                    {"id": f"{AIHUB_MODEL_PREFIX}rag-default", "base_model_id": "aihub-pipeline.rag.default"}
                ],
            ),
            patch.object(
                provisioner._client,
                "list_groups",
                return_value=[{"displayName": "aihub:T1:R1", "id": "grp-1"}],
            ),
            patch.object(provisioner._client, "update_model_access") as mock_update,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.access_rules = ["aihub.user.agent.>"]
            mock_tenant.objects.return_value = [tenant]

            role = MagicMock()
            role.name = "R1"
            role.access_rules = ["aihub.user.agent.>"]
            mock_role.objects.return_value = [role]

            await provisioner._sync_access_grants(mock_client)

            mock_update.assert_called_once()
            call_args = mock_update.call_args
            assert call_args[0][1] == f"{AIHUB_MODEL_PREFIX}rag-default"
            grants = call_args[0][2]
            assert {"principal_type": "group", "principal_id": "grp-1", "permission": "read"} in grants

    @pytest.mark.asyncio
    async def test_model_with_no_groups_gets_empty_grants(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._client,
                "list_models",
                return_value=[
                    {"id": f"{AIHUB_MODEL_PREFIX}rag-default", "base_model_id": "aihub-pipeline.rag.default"}
                ],
            ),
            patch.object(provisioner._client, "list_groups", return_value=[]),
            patch.object(provisioner._client, "update_model_access") as mock_update,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
        ):
            mock_tenant.objects.return_value = []
            mock_role.objects.return_value = []

            await provisioner._sync_access_grants(mock_client)

            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_model_accessible_by_multiple_groups(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._client,
                "list_models",
                return_value=[
                    {"id": f"{AIHUB_MODEL_PREFIX}rag-default", "base_model_id": "aihub-pipeline.rag.default"}
                ],
            ),
            patch.object(
                provisioner._client,
                "list_groups",
                return_value=[
                    {"displayName": "aihub:T1:R1", "id": "grp-1"},
                    {"displayName": "aihub:T1:R2", "id": "grp-2"},
                ],
            ),
            patch.object(provisioner._client, "update_model_access") as mock_update,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.access_rules = ["aihub.user.agent.>"]
            mock_tenant.objects.return_value = [tenant]

            role1 = MagicMock()
            role1.name = "R1"
            role1.access_rules = ["aihub.user.agent.>"]
            role2 = MagicMock()
            role2.name = "R2"
            role2.access_rules = ["aihub.user.agent.>"]
            mock_role.objects.return_value = [role1, role2]

            await provisioner._sync_access_grants(mock_client)

            mock_update.assert_called_once()
            grants = mock_update.call_args[0][2]
            granted_ids = {g["principal_id"] for g in grants}
            assert granted_ids == {"grp-1", "grp-2"}
