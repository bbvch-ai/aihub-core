from types import SimpleNamespace
from unittest.mock import patch

import pytest
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes.tenant_scoped_controller import TenantScopedController

from swiss_ai_hub.api.routes.suite.suite_service import SuiteService

_TENANT_ADMIN_CEILING = ["aihub.admin.>"]
_AGENT_VISIBILITY = f"{AccessChecker.ADMIN_PREFIX}agent.?>"


def _controller(cls_name: str, route: str, suite_visibility_permission: str | None = None) -> TenantScopedController:
    controller = type(cls_name, (TenantScopedController,), {"suite_visibility_permission": suite_visibility_permission})
    instance = controller.__new__(controller)
    instance.base_route = route
    instance.additionally_required_permission = None
    return instance


def _agent_controller() -> TenantScopedController:
    return _controller("AgentController", "/agents", _AGENT_VISIBILITY)


def _openai_controller() -> TenantScopedController:
    return _controller("OpenaiController", "/openai")


def _suite_paths(
    user_access_rules: list[str],
    tenant_access_rules: list[str] = _TENANT_ADMIN_CEILING,
    is_sys_admin: bool = False,
) -> list[str]:
    checker = AccessChecker(
        user_access_rules=user_access_rules,
        tenant_access_rules=tenant_access_rules,
        is_sys_admin=is_sys_admin,
    )
    runner = SimpleNamespace(controllers=[_agent_controller(), _openai_controller()])
    with patch.object(AccessChecker, "from_user", return_value=checker):
        suite = SuiteService.get_suite(SimpleNamespace(), runner, LocaleHandler("en"))
    return [service.path for service in suite.services]


class TestAgentAppVisibility:
    def test_chat_only_user_is_not_offered_the_agent_app(self):
        """The reported bug: `aihub.user.>` satisfies the service gate every agent user must hold to chat."""
        paths = _suite_paths(["aihub.user.>"])

        assert "/service/agents" not in paths

    def test_chat_only_user_keeps_the_services_they_can_use(self):
        paths = _suite_paths(["aihub.user.>"])

        assert "/service/openai" in paths

    def test_platform_admin_is_offered_the_agent_app(self):
        paths = _suite_paths(["aihub.admin.>"])

        assert "/service/agents" in paths

    def test_class_level_admin_is_offered_the_agent_app(self):
        """A grant to create instances of one class needs no existing instance to count."""
        paths = _suite_paths(["aihub.user.>", "aihub.admin.agent.WeatherAgent"])

        assert "/service/agents" in paths

    def test_instance_level_admin_is_offered_the_agent_app(self):
        paths = _suite_paths(["aihub.user.>", "aihub.admin.agent.WeatherAgent.inst1"])

        assert "/service/agents" in paths

    def test_sys_admin_short_circuit_is_intact(self):
        paths = _suite_paths([], tenant_access_rules=[], is_sys_admin=True)

        assert "/service/agents" in paths

    def test_tenant_ceiling_caps_a_user_level_tenant(self):
        paths = _suite_paths(["aihub.admin.agent.>"], tenant_access_rules=["aihub.user.>"])

        assert "/service/agents" not in paths


class TestControllersWithoutVisibilityPermission:
    @pytest.mark.parametrize("rules", [["aihub.user.>"], ["aihub.admin.>"]])
    def test_are_listed_exactly_as_before(self, rules: list[str]):
        paths = _suite_paths(rules)

        assert "/service/openai" in paths
