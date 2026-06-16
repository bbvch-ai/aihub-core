from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.routing import APIRoute
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.routes.tenant_scoped_controller import TenantScopedController

from swiss_ai_hub.api.decorators.access_catalog import ACCESS_CATALOG_ENTRY_ATTRIBUTE, AccessCatalogEntryMeta
from swiss_ai_hub.api.routes.access.access_capability_service import AccessCapabilityService
from swiss_ai_hub.api.routes.access.access_preset_service import AccessPresetService

_AGENT = "swiss_ai_hub.api.routes.agent.agent_service.AgentService"
_PROCESS = "swiss_ai_hub.api.routes.process.process_service.ProcessService"
_KNOWLEDGE = "swiss_ai_hub.api.routes.knowledge.knowledge_service.KnowledgeService"


class _FakeRoute(APIRoute):
    def __init__(self, template: str, cap_key: str | None = None):
        def _dependency():
            return template

        self.dependant = SimpleNamespace(call=_dependency, dependencies=[])
        if cap_key:
            setattr(self, ACCESS_CATALOG_ENTRY_ATTRIBUTE, AccessCatalogEntryMeta.from_i18n_path(cap_key))


def _controller(name: str, cls_name: str, routes: list[tuple[str, str | None]]) -> TenantScopedController:
    controller = type(cls_name, (TenantScopedController,), {"name": name})
    instance = controller.__new__(controller)
    instance.router = SimpleNamespace(routes=[_FakeRoute(tmpl, cap_key) for tmpl, cap_key in routes])
    return instance


class _AgentService:
    @staticmethod
    async def get_agent_classes(t):
        return [SimpleNamespace(agent_class="WeatherAgent", name=LocaleString(en="Weather Agent"))]

    @staticmethod
    async def get_all_agent_instances(t):
        return [SimpleNamespace(agent_class="WeatherAgent", agent_id="inst1", name="Prod Weather")]


class _ProcessService:
    @staticmethod
    async def get_process_classes(t):
        return []

    @staticmethod
    async def get_all_process_instances(t):
        return []


class _KnowledgeService:
    @staticmethod
    def get_databases(t):
        return []


_OPS = "api.access.capabilities.ops"
_AGENT_ROUTES = [
    ("aihub.user.?>", None),
    ("aihub.user.agent.?>", f"{_OPS}.agent.see"),
    ("aihub.user.agent.{agent_class}.?>", f"{_OPS}.agent.see_class"),
    ("aihub.admin.agent.{agent_class}", f"{_OPS}.agent.create"),
    ("aihub.user.agent.{agent_class}.{agent_id}", f"{_OPS}.agent.use"),
    ("aihub.admin.agent.{agent_class}.{agent_id}", f"{_OPS}.agent.manage"),
]
_ROLE_ROUTES = [("aihub.admin.service.role", None)]
_OPENAI_ROUTES = [("aihub.user.?>", None)]


async def _capabilities(
    rules: list[str], controllers, tenant_rules=None, is_sys_admin=False
) -> dict[str, SimpleNamespace]:
    runner = SimpleNamespace(controllers=controllers)
    subject = AccessChecker(user_access_rules=rules, tenant_access_rules=rules, is_sys_admin=is_sys_admin)
    ceiling = AccessChecker(tenant_rules, tenant_rules) if tenant_rules is not None else None
    with (
        patch(_AGENT, _AgentService),
        patch(_PROCESS, _ProcessService),
        patch(_KNOWLEDGE, _KnowledgeService),
    ):
        response = await AccessCapabilityService.build_capabilities(subject, runner, LocaleHandler("en"), ceiling)

    flat: dict[str, SimpleNamespace] = {}

    def collect(group):
        for cap in group.capabilities:
            flat[cap.key] = cap
        for sub in group.groups:
            collect(sub)

    for group in response.groups:
        collect(group)
    return flat


def _by_rule(caps: dict[str, SimpleNamespace], rule: str) -> SimpleNamespace:
    return next(cap for cap in caps.values() if cap.rule == rule)


@pytest.mark.asyncio
async def test_groups_are_controllers_with_service_gate():
    caps = await _capabilities([], [_controller("AI Assistants", "AgentController", _AGENT_ROUTES)])

    use = _by_rule(caps, "aihub.user.service.agent")
    assert use.toggleable and not use.granted  # the service gate "Use" capability


@pytest.mark.asyncio
async def test_exact_instance_rule_is_granted_and_unlocked():
    caps = await _capabilities(
        ["aihub.user.agent.WeatherAgent.inst1"], [_controller("AI Assistants", "AgentController", _AGENT_ROUTES)]
    )

    use = _by_rule(caps, "aihub.user.agent.WeatherAgent.inst1")
    assert use.granted and not use.locked and use.toggleable


@pytest.mark.asyncio
async def test_broad_rule_locks_covered_capabilities():
    caps = await _capabilities(["aihub.user.agent.>"], [_controller("AI Assistants", "AgentController", _AGENT_ROUTES)])

    use = _by_rule(caps, "aihub.user.agent.WeatherAgent.inst1")
    assert use.granted and use.locked  # granted via broader rule → locked


@pytest.mark.asyncio
async def test_wildcard_guards_are_read_only():
    caps = await _capabilities(["aihub.user.agent.>"], [_controller("AI Assistants", "AgentController", _AGENT_ROUTES)])

    # "See all assistants" (aihub.user.agent.?>) has no addable rule → read-only, but reflects access.
    see_all = next(cap for cap in caps.values() if not cap.toggleable and cap.granted)
    assert see_all.rule is None and not see_all.toggleable


@pytest.mark.asyncio
async def test_sysadmin_subject_grants_every_capability():
    # A sysadmin holds admin everywhere via the short-circuit, not via rules — the catalog must reflect that.
    caps = await _capabilities([], [_controller("AI Assistants", "AgentController", _AGENT_ROUTES)], is_sys_admin=True)

    toggleable = [cap for cap in caps.values() if cap.toggleable]
    assert toggleable and all(cap.granted and cap.locked for cap in toggleable)


@pytest.mark.asyncio
async def test_administer_capability_is_auto_detected():
    caps = await _capabilities([], [_controller("User Roles", "RoleController", _ROLE_ROUTES)])

    assert _by_rule(caps, "aihub.user.service.role").toggleable  # Use always present
    assert _by_rule(caps, "aihub.admin.service.role").toggleable  # Administer detected from the admin endpoint


@pytest.mark.asyncio
async def test_controller_without_admin_endpoint_has_no_administer():
    caps = await _capabilities([], [_controller("Chat", "OpenaiController", _OPENAI_ROUTES)])

    assert _by_rule(caps, "aihub.user.service.openai").toggleable
    assert not any(cap.rule == "aihub.admin.service.openai" for cap in caps.values())


@pytest.mark.asyncio
async def test_tenant_ceiling_hides_capabilities_it_cannot_grant():
    # Tenant allows only USER access to WeatherAgent instances.
    controllers = [
        _controller("AI Assistants", "AgentController", _AGENT_ROUTES),
        _controller("User Roles", "RoleController", _ROLE_ROUTES),
    ]
    caps = await _capabilities([], controllers, tenant_rules=["aihub.user.agent.WeatherAgent.>"])

    rules = {cap.rule for cap in caps.values() if cap.rule}
    assert "aihub.user.agent.WeatherAgent.inst1" in rules  # "Use" — tenant grants it
    assert "aihub.admin.agent.WeatherAgent.inst1" not in rules  # admin "Configure & delete" hidden
    assert "aihub.admin.agent.WeatherAgent" not in rules  # admin "Create" hidden
    assert not any(cap.rule and "service.role" in cap.rule for cap in caps.values())  # whole service hidden


@pytest.mark.asyncio
async def test_no_restriction_shows_full_catalog():
    controllers = [_controller("User Roles", "RoleController", _ROLE_ROUTES)]
    caps = await _capabilities([], controllers, tenant_rules=None)

    assert _by_rule(caps, "aihub.user.service.role")  # visible when editing the tenant ceiling itself
    assert _by_rule(caps, "aihub.admin.service.role")


def test_real_route_guard_is_discoverable():
    # The unit tests above use a fake route; this asserts the closure-walk works against a REAL
    # user_with_permission guard, so a refactor of how the template is captured fails loudly here.
    from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

    from swiss_ai_hub.api.routes.role.role_controller import RoleController

    controller = RoleController(auth=TestAuthHandler()).get_roles()
    route = next(r for r in controller.router.routes if isinstance(r, APIRoute))

    assert AccessCapabilityService._route_template(route) == f"aihub.admin.service.{controller.service_name}"


def test_annotated_controllers_expose_capabilities():
    # Beyond the fakes above: the closure-walk + @capability introspection must hold against real
    # production controllers — including their path-parameter guards — so a refactor of
    # user_with_permission cannot silently empty the catalog for any of them.
    from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

    from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
    from swiss_ai_hub.api.routes.process.process_controller import ProcessController

    controllers = [
        AgentController(auth=TestAuthHandler()).get_agent_classes().create_agent_instance().get_agent_instance(),
        ProcessController(auth=TestAuthHandler())
        .get_process_classes()
        .create_process_instance()
        .get_process_instance(),
    ]
    for controller in controllers:
        name = type(controller).__name__
        all_templates, annotated = AccessCapabilityService._introspect(controller)
        assert annotated, f"{name}: no @capability guard discovered — closure-walk or annotation plumbing broke"
        assert any("{" in template for template in annotated), f"{name}: expected a path-parameter guard"
        assert all(template.startswith(("aihub.user.", "aihub.admin.")) for template in all_templates)


def test_presets_cover_curated_rules_with_localized_names():
    presets = AccessPresetService.get_presets(LocaleHandler("en"))

    rules = {preset.rule for preset in presets}
    assert {"aihub.user.>", "aihub.admin.>", "aihub.user.agent.>"} <= rules
    assert all(preset.name and preset.description for preset in presets)
