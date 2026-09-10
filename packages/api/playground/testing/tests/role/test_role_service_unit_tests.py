from unittest.mock import MagicMock, patch

from swiss_ai_hub.api.routes.role.dto.create_role_request import CreateRoleRequest
from swiss_ai_hub.api.routes.role.dto.update_role_request import UpdateRoleRequest
from swiss_ai_hub.api.routes.role.role_service import RoleService

_ROLE_SERVICE = "swiss_ai_hub.api.routes.role.role_service"


class TestUpdateRolePersistsViaSave:
    """Regression: update_role must persist via ``save()`` (not the atomic ``modify()``), otherwise the
    MongoEngine post_save signal never fires and AccessChangeHook never re-syncs OpenWebUI access grants."""

    def test_update_role_calls_save_not_modify(self):
        role = MagicMock()
        role.tenant_id = "tenant-1"

        with (
            patch(f"{_ROLE_SERVICE}.RoleEntity") as mock_entity,
            patch(f"{_ROLE_SERVICE}.RoleResponse"),
        ):
            mock_entity.objects.get.return_value = role
            RoleService.update_role(
                role_id="role-1",
                data=UpdateRoleRequest(access_rules=["aihub.user.model.text-generation.>"]),
                tenant_id="tenant-1",
            )

        role.save.assert_called_once()
        role.modify.assert_not_called()
        assert role.access_rules == ["aihub.user.model.text-generation.>"]


class TestNormalizesModelAccessRulesOnWrite:
    """Model names carry version dots (``Kimi-K2.6``) that the checker collapses to ``_``; a rule
    written with the raw dot can never match, so the write path normalizes the model segment."""

    def test_update_role_normalizes_dotted_model_name(self):
        role = MagicMock()
        role.tenant_id = "tenant-1"

        with (
            patch(f"{_ROLE_SERVICE}.RoleEntity") as mock_entity,
            patch(f"{_ROLE_SERVICE}.RoleResponse"),
        ):
            mock_entity.objects.get.return_value = role
            RoleService.update_role(
                role_id="role-1",
                data=UpdateRoleRequest(access_rules=["aihub.user.model.text-generation.Kimi-K2.6"]),
                tenant_id="tenant-1",
            )

        assert role.access_rules == ["aihub.user.model.text-generation.Kimi-K2_6"]

    def test_create_role_normalizes_dotted_model_name(self):
        with (
            patch(f"{_ROLE_SERVICE}.RoleEntity") as mock_entity,
            patch(f"{_ROLE_SERVICE}.RoleResponse"),
        ):
            RoleService.create_role(
                data=CreateRoleRequest(
                    name="R1",
                    description="d",
                    access_rules=["aihub.user.model.text-generation.Kimi-K2.6"],
                ),
                tenant_id="tenant-1",
            )

        passed_rules = mock_entity.create_tenant_role.call_args.kwargs["access_rules"]
        assert passed_rules == ["aihub.user.model.text-generation.Kimi-K2_6"]
