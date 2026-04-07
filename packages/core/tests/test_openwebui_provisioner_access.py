from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from scim2_models import Group

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner


def _make_group(group_id: str, name: str) -> Group:
    return Group(id=group_id, display_name=name)


class TestComputeAccessForModel:
    def test_grants_access_when_rules_match(self):
        groups = [_make_group("g1", "aihub:Tenant1:Admin")]
        tenant_rules = {"Tenant1": ["aihub.user.agent.>"]}
        role_rules = {"Admin": ["aihub.user.agent.>"]}

        grants = OpenWebuiProvisioner._compute_access_for_model("myagent", "inst1", groups, tenant_rules, role_rules)

        assert len(grants) == 1
        assert grants[0].principal_id == "g1"
        assert grants[0].permission == "read"

    def test_no_access_when_tenant_blocks(self):
        groups = [_make_group("g1", "aihub:Tenant1:Admin")]
        tenant_rules = {"Tenant1": []}
        role_rules = {"Admin": ["aihub.user.agent.>"]}

        grants = OpenWebuiProvisioner._compute_access_for_model("myagent", "inst1", groups, tenant_rules, role_rules)
        assert len(grants) == 0

    def test_ignores_non_aihub_groups(self):
        groups = [_make_group("g1", "other-group")]
        grants = OpenWebuiProvisioner._compute_access_for_model("myagent", "inst1", groups, {}, {})
        assert len(grants) == 0

    def test_ignores_malformed_group_names(self):
        groups = [_make_group("g1", "aihub:malformed")]
        grants = OpenWebuiProvisioner._compute_access_for_model("myagent", "inst1", groups, {}, {})
        assert len(grants) == 0

    def test_multiple_groups_different_visibility(self):
        groups = [
            _make_group("g1", "aihub:T1:Admin"),
            _make_group("g2", "aihub:T1:User"),
        ]
        tenant_rules = {"T1": ["aihub.user.agent.>"]}
        role_rules = {
            "Admin": ["aihub.user.agent.>"],
            "User": ["aihub.user.agent.other.>"],
        }

        grants = OpenWebuiProvisioner._compute_access_for_model("myagent", "inst1", groups, tenant_rules, role_rules)
        assert len(grants) == 1
        assert grants[0].principal_id == "g1"


class TestParseAgentFromModel:
    def test_parses_from_base_model_id(self):
        model = {"id": "aihub-agent-cls-id", "base_model_id": "aihub-pipeline.cls.id"}
        result = OpenWebuiProvisioner._parse_agent_from_model(model)
        assert result == ("cls", "id")

    def test_fallback_to_model_id(self):
        model = {"id": "aihub-agent-cls-id", "base_model_id": ""}
        result = OpenWebuiProvisioner._parse_agent_from_model(model)
        assert result == ("cls", "id")

    def test_returns_none_for_malformed(self):
        model = {"id": "aihub-agent-nohyphen", "base_model_id": ""}
        result = OpenWebuiProvisioner._parse_agent_from_model(model)
        assert result is None


class TestSyncAccessGrants:
    @pytest.mark.asyncio
    async def test_updates_access_for_models(self, provisioner: OpenWebuiProvisioner):
        with (
            patch.object(provisioner, "_openwebui") as mock_client,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantEntity") as mock_tenant_cls,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity") as mock_role_cls,
        ):
            mock_client.list_models = AsyncMock(
                return_value=[{"id": "aihub-agent-cls-id1", "base_model_id": "aihub-pipeline.cls.id1"}]
            )

            group = _make_group("g1", "aihub:T1:Admin")
            mock_client.list_groups = AsyncMock(return_value=[group])
            mock_client.update_model_access = AsyncMock()

            tenant = MagicMock()
            tenant.name = "T1"
            tenant.access_rules = ["aihub.user.agent.>"]
            mock_tenant_cls.objects.return_value = [tenant]

            role = MagicMock()
            role.name = "Admin"
            role.access_rules = ["aihub.user.agent.>"]
            mock_role_cls.objects.return_value = [role]

            import httpx

            async with httpx.AsyncClient() as http:
                await provisioner._sync_access_grants(http)

            mock_client.update_model_access.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_when_no_models(self, provisioner: OpenWebuiProvisioner):
        with patch.object(provisioner, "_openwebui") as mock_client:
            mock_client.list_models = AsyncMock(return_value=[])

            import httpx

            async with httpx.AsyncClient() as http:
                await provisioner._sync_access_grants(http)

            mock_client.list_groups.assert_not_called()
