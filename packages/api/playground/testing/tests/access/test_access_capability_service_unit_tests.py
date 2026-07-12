from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

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
# Guards mirror the real Process/Knowledge controllers: process "Create" is a class-level read-only guard
# (`{process_class}.?>`), while knowledge has only namespace-level (two-parameter) guards — no class-level row.
_PROCESS_ROUTES = [
    ("aihub.user.process.?>", f"{_OPS}.process.see"),
    ("aihub.admin.process.{process_class}.?>", f"{_OPS}.process.create"),
    ("aihub.user.process.{process_class}.{process_id}", f"{_OPS}.process.use"),
    ("aihub.admin.process.{process_class}.{process_id}", f"{_OPS}.process.manage"),
]
_KNOWLEDGE_ROUTES = [
    ("aihub.user.knowledge.?>", f"{_OPS}.knowledge.see"),
    ("aihub.user.knowledge.{database}.{namespace}", f"{_OPS}.knowledge.use"),
    ("aihub.admin.knowledge.{database}.{namespace}", f"{_OPS}.knowledge.manage"),
]


class _PopulatedProcessService:
    @staticmethod
    async def get_process_classes(t):
        return [SimpleNamespace(process_class="Onboarding", name=LocaleString(en="Onboarding"))]

    @staticmethod
    async def get_all_process_instances(t):
        return [
            SimpleNamespace(
                process_class="Onboarding", process_id="run1", process_config=SimpleNamespace(name="Q3 Onboarding")
            )
        ]


class _PopulatedKnowledgeService:
    @staticmethod
    def get_databases(t):
        return [
            SimpleNamespace(
                name="corp",
                display_name="Corporate Wiki",
                namespaces=[SimpleNamespace(name="hr", display_name="HR Policies")],
            )
        ]


async def _catalog(
    rules: list[str],
    controllers,
    tenant_rules=None,
    is_sys_admin=False,
    agent_service=_AgentService,
    process_service=_ProcessService,
    knowledge_service=_KnowledgeService,
):
    """Builds the catalog, returning the raw response so tests can assert the group hierarchy. The three
    resource services are patched so the agent/process/knowledge resolvers enumerate fakes, not real data."""
    runner = SimpleNamespace(controllers=controllers)
    subject = AccessChecker(user_access_rules=rules, tenant_access_rules=rules, is_sys_admin=is_sys_admin)
    ceiling = AccessChecker(tenant_rules, tenant_rules) if tenant_rules is not None else None
    with (
        patch(_AGENT, agent_service),
        patch(_PROCESS, process_service),
        patch(_KNOWLEDGE, knowledge_service),
    ):
        return await AccessCapabilityService.build_capabilities(subject, runner, LocaleHandler("en"), ceiling)


async def _capabilities(
    rules: list[str], controllers, tenant_rules=None, is_sys_admin=False
) -> dict[str, SimpleNamespace]:
    response = await _catalog(rules, controllers, tenant_rules=tenant_rules, is_sys_admin=is_sys_admin)

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


def _group_by_key(groups, key: str) -> SimpleNamespace:
    return next(group for group in groups if group.key == key)


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


def test_presets_include_use_all_models():
    presets = AccessPresetService.get_presets(LocaleHandler("en"))

    all_models = next(preset for preset in presets if preset.rule == "aihub.user.model.>")
    assert all_models.name and all_models.description and all_models.category == "models"


_MODEL_ROUTES = [("aihub.user.?>", None)]
_ACCESS_SVC = "swiss_ai_hub.api.routes.access.access_capability_service"


async def _model_catalog(rules, tenant_rules=None, models=None):
    """Builds the catalog with a ModelController, patching the LiteLLM enumeration so the synthesized
    model subtree is fed fakes instead of a live proxy call."""
    models = models if models is not None else {"text-generation": ["Kimi-K2.6", "Apertus-70B"]}
    controllers = [_controller("Models", "ModelController", _MODEL_ROUTES)]
    with patch(
        f"{_ACCESS_SVC}.AccessCapabilityService.available_models_by_capability",
        AsyncMock(return_value=models),
    ):
        return await _catalog(rules, controllers, tenant_rules=tenant_rules)


def _model_tier(response):
    service = _group_by_key(response.groups, "service:model")
    return _group_by_key(service.groups, "model:text-generation")


@pytest.mark.asyncio
async def test_model_group_synthesizes_tier_and_model_rows():
    tier = _model_tier(await _model_catalog([]))

    assert tier.label == "Text generation"
    assert {cap.rule for cap in tier.capabilities} == {
        "aihub.user.model.text-generation.Kimi-K2_6",
        "aihub.user.model.text-generation.Apertus-70B",
    }
    assert all(cap.toggleable for cap in tier.capabilities)


@pytest.mark.asyncio
async def test_model_capability_normalizes_dotted_name_but_labels_the_real_name():
    tier = _model_tier(await _model_catalog([]))

    kimi = next(cap for cap in tier.capabilities if cap.rule == "aihub.user.model.text-generation.Kimi-K2_6")
    assert kimi.label == "Kimi-K2.6"  # display keeps the real dotted name; only the rule is collapsed


@pytest.mark.asyncio
async def test_model_capability_reflects_granted_state():
    tier = _model_tier(await _model_catalog(["aihub.user.model.text-generation.Kimi-K2_6"]))

    kimi = next(cap for cap in tier.capabilities if cap.rule == "aihub.user.model.text-generation.Kimi-K2_6")
    assert kimi.granted and not kimi.locked


@pytest.mark.asyncio
async def test_model_ceiling_hides_models_it_cannot_grant():
    tier = _model_tier(await _model_catalog([], tenant_rules=["aihub.user.model.text-generation.Kimi-K2_6"]))

    assert {cap.rule for cap in tier.capabilities} == {"aihub.user.model.text-generation.Kimi-K2_6"}


@pytest.mark.asyncio
async def test_capabilities_nest_under_their_service_class_and_instance():
    # The other tests flatten the tree away; this one asserts the actual nesting, so a capability landing
    # at the wrong level (hoisted onto the service, or a class rule duplicated onto its instances) fails.
    response = await _catalog(
        ["aihub.user.agent.WeatherAgent.inst1"], [_controller("AI Assistants", "AgentController", _AGENT_ROUTES)]
    )

    service = _group_by_key(response.groups, "service:agent")
    assert service.label == "AI Assistants"

    weather = _group_by_key(service.groups, "agent:WeatherAgent")
    assert weather.label == "Weather Agent"
    # "Create" is a class-level guard: it belongs on the class group, never on the service or the instance.
    assert "aihub.admin.agent.WeatherAgent" in {cap.rule for cap in weather.capabilities}
    assert "aihub.admin.agent.WeatherAgent" not in {cap.rule for cap in service.capabilities}

    instance = _group_by_key(weather.groups, "agent:WeatherAgent:inst1")
    assert instance.label == "Prod Weather"
    instance_rules = {cap.rule for cap in instance.capabilities}
    assert {"aihub.user.agent.WeatherAgent.inst1", "aihub.admin.agent.WeatherAgent.inst1"} <= instance_rules
    # The instance-level rule must live only under the instance, not be hoisted onto its class group.
    assert "aihub.user.agent.WeatherAgent.inst1" not in {cap.rule for cap in weather.capabilities}


@pytest.mark.asyncio
async def test_process_resolver_builds_class_and_instance_groups():
    # Exercises the `process` resolver branch with real data (the default fakes return empty lists, so the
    # process subtree was never built before). Mirrors the agent assertions for a second service.
    response = await _catalog(
        ["aihub.user.process.>"],
        [_controller("Workflows", "ProcessController", _PROCESS_ROUTES)],
        process_service=_PopulatedProcessService,
    )

    service = _group_by_key(response.groups, "service:process")
    onboarding = _group_by_key(service.groups, "process:Onboarding")
    assert onboarding.label == "Onboarding"
    # "Create" (`aihub.admin.process.{process_class}.?>`) is class-level AND an existence query → read-only.
    create = next(cap for cap in onboarding.capabilities if cap.label and not cap.toggleable)
    assert create.rule is None

    run = _group_by_key(onboarding.groups, "process:Onboarding:run1")
    assert run.label == "Q3 Onboarding"
    use = _by_rule({cap.key: cap for cap in run.capabilities}, "aihub.user.process.Onboarding.run1")
    assert use.granted and use.toggleable  # granted via the broad `aihub.user.process.>` rule


@pytest.mark.asyncio
async def test_knowledge_resolver_nests_namespaces_under_databases():
    # Exercises the `knowledge` resolver branch: databases are the class level, namespaces the instances,
    # and knowledge has no class-level guard, so the database group carries no rows of its own.
    response = await _catalog(
        ["aihub.admin.knowledge.>"],
        [_controller("Knowledge", "KnowledgeController", _KNOWLEDGE_ROUTES)],
        knowledge_service=_PopulatedKnowledgeService,
    )

    service = _group_by_key(response.groups, "service:knowledge")
    database = _group_by_key(service.groups, "knowledge:corp")
    assert database.label == "Corporate Wiki"
    assert database.capabilities == []  # knowledge has no class-level guard → the database group carries no rows

    namespace = _group_by_key(database.groups, "knowledge:corp:hr")
    assert namespace.label == "HR Policies"
    namespace_rules = {cap.rule for cap in namespace.capabilities}
    assert {"aihub.user.knowledge.corp.hr", "aihub.admin.knowledge.corp.hr"} <= namespace_rules
