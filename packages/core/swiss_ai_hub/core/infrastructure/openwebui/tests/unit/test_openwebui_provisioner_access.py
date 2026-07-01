from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from scim2_models import Group

from swiss_ai_hub.core.infrastructure.openwebui.access_grant import AccessGrant
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import (
    AIHUB_AGENT_PREFIX,
    OpenWebuiProvisioner,
)


def _group(display_name: str, group_id: str) -> Group:
    g = Group(display_name=display_name)
    g.id = group_id
    return g


class TestComputeAccessForModel:
    def test_group_with_matching_rules_gets_access(self) -> None:
        groups = [_group("aihub:T1:R1", "grp-1")]
        tenant_rules = {"T1": ["aihub.user.agent.rag.*"]}
        role_rules = {("T1", "R1"): ["aihub.user.agent.rag.*"]}

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert result == [AccessGrant(principal_type="group", principal_id="grp-1", permission="read")]

    def test_group_without_matching_rules_denied(self) -> None:
        groups = [_group("aihub:T1:R1", "grp-1")]
        tenant_rules = {"T1": ["aihub.user.agent.rag.*"]}
        role_rules = {("T1", "R1"): ["aihub.user.agent.other.*"]}

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert result == []

    def test_tenant_ceiling_blocks_role_access(self) -> None:
        groups = [_group("aihub:T1:R1", "grp-1")]
        tenant_rules = {"T1": ["aihub.user.agent.other.*"]}
        role_rules = {("T1", "R1"): ["aihub.user.agent.rag.*"]}

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert result == []

    def test_wildcard_rules_grant_broad_access(self) -> None:
        groups = [_group("aihub:T1:R1", "grp-1")]
        tenant_rules = {"T1": ["aihub.user.agent.>"]}
        role_rules = {("T1", "R1"): ["aihub.user.agent.>"]}

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert result == [AccessGrant(principal_type="group", principal_id="grp-1", permission="read")]

    def test_empty_tenant_rules_deny_all(self) -> None:
        groups = [_group("aihub:T1:R1", "grp-1")]
        tenant_rules = {"T1": []}
        role_rules = {("T1", "R1"): ["aihub.user.agent.rag.*"]}

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert result == []

    def test_multiple_groups_different_visibility(self) -> None:
        groups = [
            _group("aihub:T1:R1", "grp-1"),
            _group("aihub:T1:R2", "grp-2"),
        ]
        tenant_rules = {"T1": ["aihub.user.agent.>"]}
        role_rules = {
            ("T1", "R1"): ["aihub.user.agent.rag.*"],
            ("T1", "R2"): ["aihub.user.agent.llm.*"],
        }

        result_rag = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)
        result_llm = OpenWebuiProvisioner._compute_access_for_model("llm", "default", groups, tenant_rules, role_rules)

        assert result_rag == [AccessGrant(principal_type="group", principal_id="grp-1", permission="read")]
        assert result_llm == [AccessGrant(principal_type="group", principal_id="grp-2", permission="read")]

    def test_non_aihub_and_malformed_groups_are_skipped(self) -> None:
        groups = [
            _group("custom-group", "grp-custom"),
            _group("aihub:only-one-part", "grp-bad"),
            _group("aihub:T1:R1", "grp-good"),
        ]
        tenant_rules = {"T1": ["aihub.user.agent.>"]}
        role_rules = {("T1", "R1"): ["aihub.user.agent.>"]}

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert len(result) == 1
        assert result[0].principal_id == "grp-good"


class TestParseAgentFromModel:
    def test_parses_from_base_model_id(self) -> None:
        model = {"id": f"{AIHUB_AGENT_PREFIX}cls-id", "base_model_id": "aihub-pipeline.cls.id"}
        result = OpenWebuiProvisioner._parse_agent_from_model(model)
        assert result == ("cls", "id")

    def test_returns_none_without_base_model_id(self) -> None:
        model = {"id": f"{AIHUB_AGENT_PREFIX}cls-id", "base_model_id": ""}
        result = OpenWebuiProvisioner._parse_agent_from_model(model)
        assert result is None

    def test_returns_none_for_malformed_base_model_id(self) -> None:
        model = {"id": f"{AIHUB_AGENT_PREFIX}cls-id", "base_model_id": "aihub-pipeline.nodot"}
        result = OpenWebuiProvisioner._parse_agent_from_model(model)
        assert result is None


class TestSyncAccessGrants:
    @pytest.mark.asyncio
    async def test_sync_sets_access_grants_on_model(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_models",
                return_value=[
                    {"id": f"{AIHUB_AGENT_PREFIX}rag-default", "base_model_id": "aihub-pipeline.rag.default"}
                ],
            ),
            patch.object(
                provisioner._openwebui,
                "list_groups",
                return_value=[_group("aihub:T1:R1", "grp-1")],
            ),
            patch.object(provisioner._openwebui, "update_model_access") as mock_update,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity"
            ) as mock_tenant,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity") as mock_role,
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "T1"
            tenant.access_rules = ["aihub.user.agent.>"]
            mock_tenant.objects.return_value = [tenant]

            role = MagicMock()
            role.name = "R1"
            role.tenant_id = "T1"
            role.access_rules = ["aihub.user.agent.>"]
            mock_role.objects.return_value = [role]

            await provisioner._sync_access_grants(mock_client)

            mock_update.assert_called_once()
            call_args = mock_update.call_args
            assert call_args[0][1] == f"{AIHUB_AGENT_PREFIX}rag-default"
            grants = call_args[0][2]
            assert AccessGrant(principal_type="group", principal_id="grp-1", permission="read") in grants

    @pytest.mark.asyncio
    async def test_sync_parses_agent_from_base_model_id(self, provisioner: OpenWebuiProvisioner) -> None:
        """base_model_id is the preferred source for agent_class/agent_id parsing."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_models",
                return_value=[
                    {"id": f"{AIHUB_AGENT_PREFIX}my-rag-default", "base_model_id": "aihub-pipeline.my-rag.default"}
                ],
            ),
            patch.object(
                provisioner._openwebui,
                "list_groups",
                return_value=[_group("aihub:T1:R1", "grp-1")],
            ),
            patch.object(provisioner._openwebui, "update_model_access") as mock_update,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity"
            ) as mock_tenant,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity") as mock_role,
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "T1"
            tenant.access_rules = ["aihub.user.agent.my-rag.*"]
            mock_tenant.objects.return_value = [tenant]

            role = MagicMock()
            role.name = "R1"
            role.tenant_id = "T1"
            role.access_rules = ["aihub.user.agent.my-rag.*"]
            mock_role.objects.return_value = [role]

            await provisioner._sync_access_grants(mock_client)

            mock_update.assert_called_once()
            grants = mock_update.call_args[0][2]
            assert len(grants) == 1

    @pytest.mark.asyncio
    async def test_sync_skips_model_without_base_model_id(self, provisioner: OpenWebuiProvisioner) -> None:
        """Models without a valid base_model_id are skipped during access sync."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_models",
                return_value=[{"id": f"{AIHUB_AGENT_PREFIX}rag-default"}],
            ),
            patch.object(
                provisioner._openwebui,
                "list_groups",
                return_value=[_group("aihub:T1:R1", "grp-1")],
            ),
            patch.object(provisioner._openwebui, "update_model_access") as mock_update,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity"
            ) as mock_tenant,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity") as mock_role,
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "T1"
            tenant.access_rules = ["aihub.user.agent.rag.*"]
            mock_tenant.objects.return_value = [tenant]

            role = MagicMock()
            role.name = "R1"
            role.tenant_id = "T1"
            role.access_rules = ["aihub.user.agent.rag.*"]
            mock_role.objects.return_value = [role]

            await provisioner._sync_access_grants(mock_client)

            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_skips_model_with_malformed_base_model_id(self, provisioner: OpenWebuiProvisioner) -> None:
        """A base_model_id without a dot separator after the prefix is unparseable — model is skipped."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_models",
                return_value=[{"id": f"{AIHUB_AGENT_PREFIX}broken", "base_model_id": "aihub-pipeline.nodot"}],
            ),
            patch.object(
                provisioner._openwebui,
                "list_groups",
                return_value=[_group("aihub:T1:R1", "grp-1")],
            ),
            patch.object(provisioner._openwebui, "update_model_access") as mock_update,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity"
            ) as mock_tenant,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity") as mock_role,
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "T1"
            tenant.access_rules = ["aihub.user.agent.>"]
            mock_tenant.objects.return_value = [tenant]

            role = MagicMock()
            role.name = "R1"
            role.tenant_id = "T1"
            role.access_rules = ["aihub.user.agent.>"]
            mock_role.objects.return_value = [role]

            await provisioner._sync_access_grants(mock_client)

            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_model_accessible_by_multiple_groups(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_models",
                return_value=[
                    {"id": f"{AIHUB_AGENT_PREFIX}rag-default", "base_model_id": "aihub-pipeline.rag.default"}
                ],
            ),
            patch.object(
                provisioner._openwebui,
                "list_groups",
                return_value=[
                    _group("aihub:T1:R1", "grp-1"),
                    _group("aihub:T1:R2", "grp-2"),
                ],
            ),
            patch.object(provisioner._openwebui, "update_model_access") as mock_update,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity"
            ) as mock_tenant,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity") as mock_role,
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "T1"
            tenant.access_rules = ["aihub.user.agent.>"]
            mock_tenant.objects.return_value = [tenant]

            role1 = MagicMock()
            role1.name = "R1"
            role1.tenant_id = "T1"
            role1.access_rules = ["aihub.user.agent.>"]
            role2 = MagicMock()
            role2.name = "R2"
            role2.tenant_id = "T1"
            role2.access_rules = ["aihub.user.agent.>"]
            mock_role.objects.return_value = [role1, role2]

            await provisioner._sync_access_grants(mock_client)

            mock_update.assert_called_once()
            grants = mock_update.call_args[0][2]
            granted_ids = {g.principal_id for g in grants}
            assert granted_ids == {"grp-1", "grp-2"}

    @pytest.mark.asyncio
    async def test_skips_when_no_models(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(provisioner._openwebui, "list_models", return_value=[]),
            patch.object(provisioner._openwebui, "list_groups") as mock_list_groups,
        ):
            await provisioner._sync_access_grants(mock_client)

            mock_list_groups.assert_not_called()


class TestBuildRoleRules:
    def test_same_role_name_in_different_tenants_do_not_collide(self) -> None:
        """Roles are unique per (tenant_id, name), so the same name exists in every tenant with its
        own rules. A name-only key collapsed them and let the last tenant's rules mask the rest;
        the (tenant name, role name) key keeps them distinct."""
        with (
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity"
            ) as mock_tenant,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity") as mock_role,
        ):
            tenant_a = MagicMock()
            tenant_a.id = "ta"
            tenant_a.name = "TenantA"
            tenant_b = MagicMock()
            tenant_b.id = "tb"
            tenant_b.name = "TenantB"
            mock_tenant.objects.return_value = [tenant_a, tenant_b]

            role_a = MagicMock()
            role_a.name = "Shared"
            role_a.tenant_id = "ta"
            role_a.access_rules = ["aihub.user.agent.rag.*"]
            role_b = MagicMock()
            role_b.name = "Shared"
            role_b.tenant_id = "tb"
            role_b.access_rules = ["aihub.user.agent.other.*"]
            mock_role.objects.return_value = [role_a, role_b]

            result = OpenWebuiProvisioner._build_role_rules()

        assert result == {
            ("TenantA", "Shared"): ["aihub.user.agent.rag.*"],
            ("TenantB", "Shared"): ["aihub.user.agent.other.*"],
        }

    def test_role_of_unknown_tenant_is_skipped(self) -> None:
        """A role whose tenant has no TenantMetadataEntity has no OpenWebUI group either, so its
        rules are never looked up — dropping it keeps the lookup key well-defined."""
        with (
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity"
            ) as mock_tenant,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity") as mock_role,
        ):
            tenant = MagicMock()
            tenant.id = "ta"
            tenant.name = "TenantA"
            mock_tenant.objects.return_value = [tenant]

            orphan = MagicMock()
            orphan.name = "Ghost"
            orphan.tenant_id = "deleted"
            orphan.access_rules = ["aihub.user.agent.>"]
            mock_role.objects.return_value = [orphan]

            assert OpenWebuiProvisioner._build_role_rules() == {}


class TestCrossTenantIsolation:
    def test_same_role_name_in_two_tenants_stay_isolated(self) -> None:
        """The regression: a role name shared by two tenants must grant each tenant's own rules.
        With the old name-only key both groups resolved to the same (colliding) rule set."""
        groups = [
            _group("aihub:TenantA:Shared", "grp-a"),
            _group("aihub:TenantB:Shared", "grp-b"),
        ]
        tenant_rules = {"TenantA": ["aihub.user.agent.>"], "TenantB": ["aihub.user.agent.>"]}
        role_rules = {
            ("TenantA", "Shared"): ["aihub.user.agent.rag.*"],
            ("TenantB", "Shared"): ["aihub.user.agent.other.*"],
        }

        result = OpenWebuiProvisioner._compute_access_for_model("rag", "default", groups, tenant_rules, role_rules)

        assert [g.principal_id for g in result] == ["grp-a"]
