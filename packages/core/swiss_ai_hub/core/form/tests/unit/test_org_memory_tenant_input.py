from unittest.mock import Mock

import pytest

from swiss_ai_hub.core.form.elements.org_memory_tenant_input import OrgMemoryTenantInput
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler


@pytest.fixture
def t() -> LocaleHandler:
    return LocaleHandler(locale="en")


def _checker(has_access: bool) -> Mock:
    checker = Mock()
    checker.has_access = Mock(return_value=has_access)
    return checker


class TestOrgMemoryTenantInputValidation:
    def test_none_value_skipped(self, t: LocaleHandler):
        element = OrgMemoryTenantInput(label="Tenant", name="tenant_id")
        violations = element.validate_authorization("tenant_id", None, _checker(False), t)
        assert violations == []

    def test_access_granted(self, t: LocaleHandler):
        element = OrgMemoryTenantInput(label="Tenant", name="tenant_id")
        violations = element.validate_authorization("tenant_id", "AIHub", _checker(True), t)
        assert violations == []

    def test_access_denied(self, t: LocaleHandler):
        element = OrgMemoryTenantInput(label="Tenant", name="tenant_id")
        checker = _checker(False)

        violations = element.validate_authorization("org_memory.tenant_id", "AIHub", checker, t)

        assert len(violations) == 1
        v = violations[0]
        assert v.field == "org_memory.tenant_id"
        assert v.resource_type == "organization_memory"
        assert v.resource == "organization_memory"
        assert "organization memory" in v.message.lower()
        checker.has_access.assert_called_once_with("aihub.user.memory.organization.?>")

    def test_access_denied_message_localized(self):
        element = OrgMemoryTenantInput(label="Tenant", name="tenant_id")
        violations = element.validate_authorization(
            "tenant_id", "AIHub", _checker(False), LocaleHandler(locale="de")
        )
        assert "Organisationsspeicher" in violations[0].message
