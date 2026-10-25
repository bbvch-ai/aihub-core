from contextlib import ExitStack
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.form import ConfigSpecs
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.process.process_config_entity_document import ProcessConfigEntityDocument

from swiss_ai_hub.api.routes.process.dto.create_process_instance_request import CreateProcessInstanceRequest
from swiss_ai_hub.api.routes.process.process_instance_access_grant import ProcessInstanceAccessGrant
from swiss_ai_hub.api.routes.process.process_service import ProcessService
from swiss_ai_hub.api.runners.lifetime.process_root_rule_migration import ProcessRootRuleMigration

_MODULE = "swiss_ai_hub.api.routes.process.process_service"
_ADMIN_RULE = "aihub.admin.process.Onboarding.q3-onboarding"
_USER_RULE = "aihub.user.process.Onboarding.q3-onboarding"
_ROLE_NAME = "ProcessAdmin.Onboarding.q3-onboarding"


@pytest.fixture
def creator_user() -> Mock:
    """A tenant admin whose ceiling holds only the process root, as a newly derived tenant does."""
    user = Mock(spec=UserIdentity)
    user.id = "user_123"
    user.acting_within_tenant = Mock()
    user.acting_within_tenant.id = "tenant_1"
    user.acting_within_tenant.access_rules = ["aihub.admin.process"]
    return user


class TestRoleName:
    def test_names_class_and_id_verbatim(self):
        assert ProcessInstanceAccessGrant.role_name("Onboarding", "q3-onboarding") == _ROLE_NAME

    @pytest.mark.parametrize(
        ("first", "second"),
        [
            (("Onboarding", "q3-onboarding"), ("Offboarding", "q3-onboarding")),
            (("Onboarding", "cv-review"), ("Onboarding", "cv_review")),
            (("Onboarding", "cvreview"), ("Onboarding", "cv-review")),
        ],
    )
    def test_different_instances_never_share_a_role(self, first: tuple[str, str], second: tuple[str, str]):
        assert ProcessInstanceAccessGrant.role_name(*first) != ProcessInstanceAccessGrant.role_name(*second)


class TestNamesAreLiteralRuleSegments:
    @pytest.mark.parametrize("process_id", ["a.b", ">", "*", "x.>", "a?", "{id}", "Upper", ""])
    def test_the_request_rejects_an_id_that_is_not_a_plain_slug(self, process_id: str):
        with pytest.raises(ValidationError):
            CreateProcessInstanceRequest(process_id=process_id, configuration={})

    @pytest.mark.parametrize(
        ("process_class", "process_id"),
        [("Onboarding", "x.>"), ("Onboarding", ">"), ("Onboarding", "a*"), ("On.boarding", "id"), ("*", "id")],
    )
    def test_the_grant_refuses_a_name_that_would_widen_the_rule(
        self, creator_user: Mock, process_class: str, process_id: str
    ):
        rollback = Mock()
        with (
            patch.object(TenantMetadataEntity, "grant_access_rule") as grant_rule,
            patch.object(RoleEntity, "create_tenant_role") as create_role,
            patch.object(UserTenantRoleEntity, "add_roles") as add_roles,
            pytest.raises(HTTPException) as raised,
        ):
            ProcessInstanceAccessGrant.grant(process_class, process_id, creator_user, rollback)

        assert raised.value.status_code == 500
        grant_rule.assert_not_called()
        create_role.assert_not_called()
        add_roles.assert_not_called()
        rollback.assert_called_once()


class TestExistingRole:
    @staticmethod
    def _existing_role(*rules: str) -> Mock:
        role = Mock()
        role.access_rules = list(rules)
        query = Mock()
        query.first.return_value = role
        return query

    def test_a_role_granting_exactly_the_instance_is_reused(self):
        with (
            patch.object(RoleEntity, "objects", return_value=self._existing_role(_ADMIN_RULE)),
            patch.object(RoleEntity, "create_tenant_role") as create_role,
        ):
            created = ProcessInstanceAccessGrant._ensure_admin_role(
                _ROLE_NAME, _ADMIN_RULE, "tenant_1", "Onboarding", "q3-onboarding"
            )

        assert not created
        create_role.assert_not_called()

    @pytest.mark.parametrize("rules", [("aihub.admin.process.>",), (_ADMIN_RULE, "aihub.admin.agent.>"), ()])
    def test_a_role_with_any_other_scope_fails_the_grant(self, creator_user: Mock, rules: tuple[str, ...]):
        rollback = Mock()
        with (
            patch.object(TenantMetadataEntity, "grant_access_rule"),
            patch.object(TenantMetadataEntity, "revoke_access_rule_from_all_tenants"),
            patch.object(RoleEntity, "objects", return_value=self._existing_role(*rules)),
            patch.object(RoleEntity, "delete_role_from_all_tenants") as delete_role,
            patch.object(UserTenantRoleEntity, "add_roles") as add_roles,
            pytest.raises(HTTPException) as raised,
        ):
            ProcessInstanceAccessGrant.grant("Onboarding", "q3-onboarding", creator_user, rollback)

        assert raised.value.status_code == 500
        add_roles.assert_not_called()
        delete_role.assert_not_called()
        rollback.assert_called_once()


class TestGrant:
    def test_grants_the_tenant_rule_and_a_creator_role(self, creator_user: Mock):
        rollback = Mock()
        with (
            patch.object(TenantMetadataEntity, "grant_access_rule") as grant_rule,
            patch.object(ProcessInstanceAccessGrant, "_ensure_admin_role", return_value=True) as ensure_role,
            patch.object(UserTenantRoleEntity, "add_roles") as add_roles,
        ):
            ProcessInstanceAccessGrant.grant("Onboarding", "q3-onboarding", creator_user, rollback)

        grant_rule.assert_called_once_with("tenant_1", _ADMIN_RULE)
        ensure_role.assert_called_once_with(_ROLE_NAME, _ADMIN_RULE, "tenant_1", "Onboarding", "q3-onboarding")
        add_roles.assert_called_once_with("user_123", "tenant_1", [_ROLE_NAME])
        rollback.assert_not_called()

    def test_skips_the_tenant_rule_when_a_broader_rule_covers_it(self, creator_user: Mock):
        creator_user.acting_within_tenant.access_rules = ["aihub.admin.>"]
        with (
            patch.object(TenantMetadataEntity, "grant_access_rule") as grant_rule,
            patch.object(ProcessInstanceAccessGrant, "_ensure_admin_role", return_value=True),
            patch.object(UserTenantRoleEntity, "add_roles") as add_roles,
        ):
            ProcessInstanceAccessGrant.grant("Onboarding", "q3-onboarding", creator_user, Mock())

        grant_rule.assert_not_called()
        add_roles.assert_called_once()

    def test_the_root_alone_does_not_count_as_covering_the_instance(self):
        assert not AccessChecker.rules_grant_admin(["aihub.admin.process"], _ADMIN_RULE)

    def test_a_failed_grant_undoes_the_grant_and_the_creation(self, creator_user: Mock):
        rollback = Mock()
        with (
            patch.object(TenantMetadataEntity, "grant_access_rule"),
            patch.object(ProcessInstanceAccessGrant, "_ensure_admin_role", return_value=True),
            patch.object(UserTenantRoleEntity, "add_roles", side_effect=RuntimeError("boom")),
            patch.object(TenantMetadataEntity, "revoke_access_rule_from_all_tenants") as revoke,
            patch.object(RoleEntity, "delete_role_from_all_tenants") as delete_role,
            pytest.raises(HTTPException) as raised,
        ):
            ProcessInstanceAccessGrant.grant("Onboarding", "q3-onboarding", creator_user, rollback)

        assert raised.value.status_code == 500
        revoke.assert_called_once_with([_ADMIN_RULE])
        delete_role.assert_called_once_with(_ROLE_NAME)
        rollback.assert_called_once()


class TestCreateGrantsTheInstance:
    @staticmethod
    def _mock_create_dependencies(stack: ExitStack) -> tuple[Mock, Mock]:
        class_entity = Mock()
        class_entity.is_online = True
        class_entity.process_config_specs.to_specs.return_value = ConfigSpecs(config_class="Onboarding")
        config_entity = Mock()
        grant = stack.enter_context(patch.object(ProcessInstanceAccessGrant, "grant"))
        stack.enter_context(patch(f"{_MODULE}.ProcessClassEntity.get_by_process_class", return_value=class_entity))
        stack.enter_context(patch(f"{_MODULE}.ModelCreationService"))
        stack.enter_context(patch(f"{_MODULE}.InstanceConfigHelper"))
        stack.enter_context(
            patch(f"{_MODULE}.ModelLimitValidator.reject_values_beyond_model_limits", AsyncMock(return_value=None))
        )
        config_auth = stack.enter_context(patch(f"{_MODULE}.ConfigAuthorizationService"))
        config_auth.validate_for_user_or_raise = AsyncMock()
        stack.enter_context(patch(f"{_MODULE}.FullProcessInstanceDTO"))
        config_doc = stack.enter_context(patch(f"{_MODULE}.ProcessConfigEntityDocument"))
        config_doc.find_for_class_and_id.return_value = None
        config_doc.return_value = config_entity
        return grant, config_entity

    @pytest.mark.asyncio
    async def test_grants_the_instance_to_the_creating_tenant(self):
        user = Mock()
        user.acting_within_tenant = Mock()
        request = CreateProcessInstanceRequest(process_id="q3-onboarding", configuration={})

        with ExitStack() as stack:
            grant, config_entity = self._mock_create_dependencies(stack)
            await ProcessService.create_process_instance("Onboarding", request, Mock(spec=LocaleHandler), user=user)

        grant.assert_called_once_with("Onboarding", "q3-onboarding", user, config_entity.delete)

    @pytest.mark.asyncio
    async def test_skips_the_grant_for_a_sysadmin_outside_any_tenant(self):
        user = Mock()
        user.acting_within_tenant = None
        request = CreateProcessInstanceRequest(process_id="q3-onboarding", configuration={})

        with ExitStack() as stack:
            grant, _ = self._mock_create_dependencies(stack)
            await ProcessService.create_process_instance("Onboarding", request, Mock(spec=LocaleHandler), user=user)

        grant.assert_not_called()


class TestDeleteRevokesTheInstance:
    @pytest.mark.asyncio
    async def test_revokes_both_rules_and_deletes_the_role(self):
        with (
            patch.object(ProcessConfigEntityDocument, "find_for_class_and_id", return_value=Mock()),
            patch.object(ProcessConfigEntityDocument, "delete_if_exists_for_class_and_id") as delete_config,
            patch.object(TenantMetadataEntity, "revoke_access_rule_from_all_tenants") as revoke,
            patch.object(RoleEntity, "delete_role_from_all_tenants") as delete_role,
        ):
            await ProcessService.delete_process_instance("Onboarding", "q3-onboarding")

        delete_config.assert_called_once_with("Onboarding", "q3-onboarding")
        revoke.assert_called_once_with([_USER_RULE, _ADMIN_RULE])
        delete_role.assert_called_once_with(_ROLE_NAME)

    @pytest.mark.asyncio
    async def test_a_missing_instance_revokes_nothing(self):
        with (
            patch.object(ProcessConfigEntityDocument, "find_for_class_and_id", return_value=None),
            patch.object(TenantMetadataEntity, "revoke_access_rule_from_all_tenants") as revoke,
            pytest.raises(HTTPException) as raised,
        ):
            await ProcessService.delete_process_instance("Onboarding", "missing")

        assert raised.value.status_code == 404
        revoke.assert_not_called()


class TestTheCreateGuard:
    """The trap the migration exists for: a ``>`` needs one more token, so the wildcard misses the root."""

    def test_the_wildcard_alone_does_not_satisfy_the_root(self):
        checker = AccessChecker(user_access_rules=["aihub.admin.process.>"], tenant_access_rules=["aihub.admin.>"])

        assert not checker.has_access(AccessChecker.process_root_admin_rule())

    def test_the_root_lists_processes_without_reaching_any_instance(self):
        checker = AccessChecker(user_access_rules=["aihub.admin.>"], tenant_access_rules=["aihub.admin.process"])

        assert checker.has_access("aihub.user.process.?>")
        assert not checker.has_access_to_process("Onboarding", "q3-onboarding")


class TestProcessRootRuleMigration:
    @staticmethod
    def _holder(*rules: str) -> Mock:
        holder = Mock()
        holder.access_rules = list(rules)
        return holder

    def test_adds_the_root_next_to_the_wildcard(self):
        tenant = self._holder("aihub.admin.process.>")
        role = self._holder("aihub.admin.process.>", "aihub.user.>")
        with (
            patch.object(TenantMetadataEntity, "objects", return_value=[tenant]) as tenants,
            patch.object(RoleEntity, "objects", return_value=[role]) as roles,
        ):
            migrated = ProcessRootRuleMigration.run()

        tenants.assert_called_once_with(access_rules="aihub.admin.process.>")
        roles.assert_called_once_with(access_rules="aihub.admin.process.>")
        assert tenant.access_rules == ["aihub.admin.process.>", "aihub.admin.process"]
        assert role.access_rules == ["aihub.admin.process.>", "aihub.user.>", "aihub.admin.process"]
        tenant.save.assert_called_once()
        role.save.assert_called_once()
        assert len(migrated) == 2

    def test_leaves_a_holder_that_already_has_the_root_alone(self):
        tenant = self._holder("aihub.admin.process.>", "aihub.admin.process")
        with (
            patch.object(TenantMetadataEntity, "objects", return_value=[tenant]),
            patch.object(RoleEntity, "objects", return_value=[]),
        ):
            migrated = ProcessRootRuleMigration.run()

        tenant.save.assert_not_called()
        assert migrated == []
