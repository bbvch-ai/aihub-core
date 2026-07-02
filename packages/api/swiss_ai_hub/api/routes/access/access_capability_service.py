import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Annotated, NamedTuple

from fastapi.routing import APIRoute
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.infrastructure import LiteLLMProxySettings, trace_fn
from swiss_ai_hub.core.routes.tenant_scoped_controller import TenantScopedController

from swiss_ai_hub.api.decorators.access_catalog import ACCESS_CATALOG_ENTRY_ATTRIBUTE, AccessCatalogEntryMeta
from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.access.dto.access_capabilities_dto import (
    AccessCapabilitiesResponse,
    Capability,
    CapabilityGroup,
)

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners import Runner

logger = logging.getLogger(__name__)

# The implicit per-service gate is not backed by a ``user_with_permission`` route, so it carries no
# ``@access_catalog_entry`` annotation — its labels live here instead of being read off a route.
_SERVICE_USE_LABEL = ApiLocaleString.from_i18n_path("api.access.capabilities.ops.service.use.label")
_SERVICE_USE_DESCRIPTION = ApiLocaleString.from_i18n_path("api.access.capabilities.ops.service.use.description")
_SERVICE_ADMIN_LABEL = ApiLocaleString.from_i18n_path("api.access.capabilities.ops.service.administer.label")
_SERVICE_ADMIN_DESCRIPTION = ApiLocaleString.from_i18n_path(
    "api.access.capabilities.ops.service.administer.description"
)

# Models are gated in the service layer (``has_access_to_model``), not by a per-model route guard, so their
# capability rows are synthesized rather than read off a route — the same way the service gates above are.
_MODEL_SERVICE_NAME = "model"
_MODEL_USE_DESCRIPTION = ApiLocaleString.from_i18n_path("api.access.capabilities.ops.model.use.description")


class _Guard(NamedTuple):
    """A concrete, fully-substituted permission rule (e.g. ``aihub.user.agent.WeatherAgent.inst1``) — what
    the subject's ``AccessChecker`` is actually queried with."""

    rule: str

    @property
    def is_existence_query(self) -> bool:
        """A ``?>``/``?*`` query asks "is there *any* access" — it has no single satisfying rule, so its
        capability row is read-only rather than a grantable checkbox."""
        return "?" in self.rule

    def __str__(self) -> str:
        return self.rule


class _GuardTemplate(NamedTuple):
    """A route's raw ``user_with_permission`` template before its ``{path_params}`` are filled in. Its
    *arity* — the number of placeholders — classifies it: resource-wide guards (``aihub.admin.agent.>``)
    render straight onto the service, class-level guards expand over each class, instance-level over each
    instance."""

    raw: str

    @property
    def arity(self) -> int:
        return self.raw.count("{")

    @property
    def is_resource_wide(self) -> bool:
        return self.arity == 0

    @property
    def is_class_level(self) -> bool:
        return self.arity == 1

    @property
    def is_instance_level(self) -> bool:
        return self.arity == 2

    def substitute(self, **path_param_values: str) -> _Guard:
        """Fills the template's ``{path_params}`` with concrete resource values (none for resource-wide
        guards) to produce the queryable :class:`_Guard`."""
        return _Guard(self.raw.format(**path_param_values))


class _ResourceNode(NamedTuple):
    """One concrete resource a templated guard is expanded over — an agent or process class, a class
    instance, a knowledge database or a namespace. ``value`` is substituted for the guard's path
    parameter; ``label`` and ``icon`` drive the rendered group header."""

    value: str
    label: str
    icon: str | None = None


class _ResourceTree(NamedTuple):
    """The enumerable resources of one service, in the two-level shape the capability tree mirrors:
    top-level ``classes`` (agent/process classes, knowledge databases), their ``instances_by_class``
    (instances, namespaces), and the guard's ``(class, instance)`` path-parameter names."""

    classes: list[_ResourceNode]
    instances_by_class: dict[str, list[_ResourceNode]]
    param_names: tuple[str, str]


class AccessCapabilityService:
    """Builds the human-readable capability catalog by introspecting each controller's routes at runtime.

    Groups are services (controllers). Each route annotated with ``@access_catalog_entry(...)`` becomes a capability
    whose access rule **is** the route's own ``user_with_permission`` guard — the single source of truth,
    never restated. ``granted`` is evaluated through the subject's ``AccessChecker`` with the exact
    ``has_access`` call the endpoint enforces with, so the table cannot drift from enforcement: the sysadmin
    short-circuit and the tenant ceiling are honoured for free. A guard containing a ``?`` query has no
    single satisfying rule, so its row is read-only; templated guards are enumerated over the concrete
    resources of the service.

    The per-request assembly — which is stateful in ``subject``/``ceiling``/``t`` — lives on
    :class:`_CapabilityCatalogBuilder`; this class is the stateless facade plus the pure route-introspection
    helpers (``_introspect``/``_route_template``) that need no request state.
    """

    @staticmethod
    @trace_fn
    async def build_capabilities(
        subject: Annotated[
            AccessChecker,
            "Whose access the catalog is evaluated against: a draft rule set in the role / tenant-ceiling "
            "editor, or the viewed user's real checker (sysadmin- and ceiling-aware) on the user page.",
        ],
        runner: "Runner",
        t: LocaleHandler,
        ceiling: Annotated[
            AccessChecker | None,
            "When set, capabilities this ceiling cannot grant are hidden entirely — the role editor must "
            "never reveal access the tenant itself lacks. ``None`` when editing the ceiling (full catalog).",
        ] = None,
    ) -> AccessCapabilitiesResponse:
        return await _CapabilityCatalogBuilder(subject=subject, ceiling=ceiling, t=t).build(runner)

    @staticmethod
    def _introspect(controller: TenantScopedController) -> tuple[set[str], dict[str, AccessCatalogEntryMeta]]:
        """Reads every route's ``user_with_permission`` guard. Returns all guard templates (used to detect
        whether an "Administer" gate exists) and the subset annotated with ``@access_catalog_entry`` (the
        catalog rows)."""
        all_templates: set[str] = set()
        annotated_guards: dict[str, AccessCatalogEntryMeta] = {}
        for route in controller.router.routes:
            if not isinstance(route, APIRoute):
                continue
            template = AccessCapabilityService._route_template(route)
            if template is None:
                continue
            all_templates.add(template)
            meta = getattr(route, ACCESS_CATALOG_ENTRY_ATTRIBUTE, None)
            if isinstance(meta, AccessCatalogEntryMeta):
                if template in annotated_guards and annotated_guards[template] != meta:
                    logger.warning(
                        "Two @capability annotations resolve to the same guard %r on %s; keeping the first "
                        "and dropping the other. Give the routes distinct guards or merge their labels.",
                        template,
                        type(controller).__name__,
                    )
                annotated_guards.setdefault(template, meta)
        return all_templates, annotated_guards

    @staticmethod
    def _route_template(route: APIRoute) -> str | None:
        """The ``user_with_permission`` template guarding ``route``, read out of its dependency closure — the
        guard the endpoint actually enforces, so the catalog's rule can never drift from what is enforced."""
        stack = [route.dependant]
        while stack:
            dependant = stack.pop()
            guard = AccessCapabilityService._guard_in_closure(getattr(dependant, "call", None))
            if guard is not None:
                return guard
            stack.extend(dependant.dependencies)
        return None

    @staticmethod
    def _guard_in_closure(call: object) -> str | None:
        """Finds the ``aihub.…`` permission template captured as a free variable by ``user_with_permission``.

        This couples the catalog to *how* ``Controller.user_with_permission`` captures its template (as a
        string closure cell); if that helper ever stops closing over the raw template, routes silently drop
        out of the catalog. The contract is exercised end-to-end by ``test_real_route_guard_is_discoverable``.
        """
        for cell in getattr(call, "__closure__", None) or ():
            try:
                value = cell.cell_contents
            except ValueError:
                continue
            # Require the permission-template prefixes, not just ``aihub.``, so an unrelated captured string
            # (a NATS subject, a log prefix) can't be mistaken for the guard and silently shadow the real one.
            if isinstance(value, str) and value.startswith((AccessChecker.USER_PREFIX, AccessChecker.ADMIN_PREFIX)):
                return value
        return None

    @staticmethod
    async def available_models_by_capability() -> dict[str, list[str]]:
        """Enumerates every LiteLLM model as ``{capability: [model_name, ...]}`` for the model capability
        rows. Uses the master client so the whole catalog is built; per-subject and per-ceiling filtering
        happens downstream in ``_capability_for_guard``. Models without a capability prefix are skipped —
        they cannot form a ``aihub.user.model.<capability>.<name>`` rule."""
        async with LiteLLMProxySettings().httpx_aclient as client:
            response = await client.get("/v1/model/info")
            response.raise_for_status()
            data = response.json()["data"]
        models_by_capability: dict[str, list[str]] = {}
        for entry in data:
            capability, _, name = entry["model_name"].partition("/")
            if name:
                models_by_capability.setdefault(capability, []).append(name)
        return models_by_capability


class _CapabilityCatalogBuilder:
    """Assembles one capability catalog for a single ``(subject, ceiling, locale)``. Holding these as state
    keeps them off every method signature — each capability row only needs the guard and its labels — and
    makes the recursion (service → class → instance) read as the tree it builds."""

    def __init__(self, *, subject: AccessChecker, ceiling: AccessChecker | None, t: LocaleHandler):
        self._subject = subject
        self._ceiling = ceiling
        self._t = t
        self._granted_rules = subject.access_rules

    async def build(self, runner: "Runner") -> AccessCapabilitiesResponse:
        groups: list[CapabilityGroup] = []
        for controller in runner.controllers:
            if not isinstance(controller, TenantScopedController):
                continue
            group = await self._service_group(controller)
            if self._prune(group):
                groups.append(group)
        groups.sort(key=lambda group: group.label.lower())
        return AccessCapabilitiesResponse(groups=groups)

    async def _service_group(self, controller: TenantScopedController) -> CapabilityGroup:
        """Builds one top-level group for a service: its service-level gate, any resource-wide capabilities
        (zero-parameter guards), and the nested class/instance tree for enumerable resources."""
        service_name = controller.service_name
        all_templates, annotated_guards = AccessCapabilityService._introspect(controller)
        # The service-level gates are rendered separately by `_service_gate_capabilities`, so exclude them
        # from the per-resource guards below. `USER_PREFIX`/`ADMIN_PREFIX` already end in a dot
        # (`"aihub.user."`), so `f"{USER_PREFIX}?>"` is `"aihub.user.?>"` — the catch-all "any access" gate.
        gate_templates = {
            f"{AccessChecker.USER_PREFIX}?>",
            f"{AccessChecker.ADMIN_PREFIX}?>",
            AccessChecker.service_user_rule(service_name),
            AccessChecker.service_admin_rule(service_name),
        }
        resource_guards = {
            _GuardTemplate(template): meta
            for template, meta in annotated_guards.items()
            if template not in gate_templates
        }

        capabilities = self._service_gate_capabilities(service_name, all_templates)
        # Resource-wide guards have no `{path_param}` to substitute (e.g. "list everything"), so they render
        # straight onto the service group. Parameterised guards are expanded by `_resource_groups` over the
        # service's concrete agents/processes/namespaces.
        resource_wide = sorted(
            (template, meta) for template, meta in resource_guards.items() if template.is_resource_wide
        )
        capabilities += self._capabilities_for(resource_wide)
        subgroups = await self._resource_groups(service_name, resource_guards)
        if service_name == _MODEL_SERVICE_NAME:
            subgroups = subgroups + await self._model_tier_groups()
        return CapabilityGroup(
            key=f"service:{service_name}",
            label=self._t.extract(controller.name),
            icon=getattr(controller, "icon", None),
            capabilities=capabilities,
            groups=subgroups,
        )

    def _service_gate_capabilities(self, service_name: str, all_templates: set[str]) -> list[Capability]:
        """The implicit per-service gate: every service has a "Use" capability; "Administer" is surfaced
        only when the controller actually exposes an ``aihub.admin.service.<name>`` endpoint."""
        gate_specs = [(_SERVICE_USE_LABEL, _SERVICE_USE_DESCRIPTION, AccessChecker.service_user_rule(service_name))]
        if AccessChecker.service_admin_rule(service_name) in all_templates:
            gate_specs.append(
                (_SERVICE_ADMIN_LABEL, _SERVICE_ADMIN_DESCRIPTION, AccessChecker.service_admin_rule(service_name))
            )
        capabilities: list[Capability] = []
        for label, description, rule in gate_specs:
            capability = self._capability_for_guard(label, description, _Guard(rule))
            if capability is not None:
                capabilities.append(capability)
        return capabilities

    def _capabilities_for(
        self, guards: list[tuple[_GuardTemplate, AccessCatalogEntryMeta]], **path_param_values: str
    ) -> list[Capability]:
        """Substitutes ``path_param_values`` into each guard template and builds its capability row, dropping
        any the ceiling hides (``_capability_for_guard`` returns ``None``)."""
        capabilities: list[Capability] = []
        for template, meta in guards:
            capability = self._capability_for_guard(
                meta.label, meta.description, template.substitute(**path_param_values)
            )
            if capability is not None:
                capabilities.append(capability)
        return capabilities

    def _capability_for_guard(
        self, label_locale: LocaleString, description_locale: LocaleString, guard: _Guard
    ) -> Capability | None:
        """Builds one capability row. ``granted`` comes from ``subject.has_access`` — the same call the
        endpoint's guard makes — so the row matches enforcement (sysadmin short-circuit and ceiling included).

        An existence-query guard (``?>``/``?*``) has no single satisfying rule, so the row is read-only; a
        concrete guard *is* the grantable rule and is toggleable, and is ``locked`` when access comes from a
        broader rule than the one this checkbox would add. Returns ``None`` when a ``ceiling`` is given that
        cannot grant the capability — it is then hidden, never merely disabled (no information leak).
        """
        rule = str(guard)
        if self._ceiling is not None and not self._ceiling.has_access(rule):
            return None

        label = self._t.extract(label_locale)
        description = self._t.extract(description_locale)
        granted = self._subject.has_access(rule)

        if guard.is_existence_query:
            return Capability(
                key=f"ro:{rule}",
                label=label,
                description=description,
                rule=None,
                granted=granted,
                locked=False,
                toggleable=False,
            )
        return Capability(
            key=rule,
            label=label,
            description=description,
            rule=rule,
            granted=granted,
            locked=granted and rule not in self._granted_rules,
            toggleable=True,
        )

    async def _model_tier_groups(self) -> list[CapabilityGroup]:
        """Synthesizes the model capability subtree: one group per capability tier (text-generation,
        embedding, ...), each holding a grantable row per concrete model. The rule is built with
        ``AccessChecker.model_user_rule`` — the same normalized template enforcement checks with — so a
        checkbox can never grant a rule that would fail to match, and dotted names are collapsed for free.
        ``_capability_for_guard`` applies the ceiling and ``granted`` state exactly as for route-derived
        rows, so a model the ceiling cannot grant is hidden rather than shown disabled."""
        models_by_capability = await AccessCapabilityService.available_models_by_capability()
        groups: list[CapabilityGroup] = []
        for capability in sorted(models_by_capability):
            capabilities: list[Capability] = []
            for name in sorted(models_by_capability[capability]):
                label = LocaleString(de=name, en=name, fr=name, it=name)
                guard = _Guard(AccessChecker.model_user_rule(capability, name))
                capability_row = self._capability_for_guard(label, _MODEL_USE_DESCRIPTION, guard)
                if capability_row is not None:
                    capabilities.append(capability_row)
            if capabilities:
                groups.append(
                    CapabilityGroup(
                        key=f"model:{capability}",
                        label=self._prettify_capability(capability),
                        capabilities=capabilities,
                    )
                )
        return groups

    @staticmethod
    def _prettify_capability(capability: str) -> str:
        """Turns a LiteLLM capability segment (``text-generation``) into a group heading (``Text generation``)."""
        return capability.replace("-", " ").replace("_", " ").capitalize()

    @staticmethod
    def _prune(group: CapabilityGroup) -> bool:
        """Drops nested groups emptied by ceiling-filtering; returns whether ``group`` still shows anything."""
        group.groups = [sub for sub in group.groups if _CapabilityCatalogBuilder._prune(sub)]
        return bool(group.capabilities or group.groups)

    async def _resource_groups(
        self, service_name: str, resource_guards: dict[_GuardTemplate, AccessCatalogEntryMeta]
    ) -> list[CapabilityGroup]:
        """Expands the controller's ``{path_param}`` guards over the concrete resources of enumerable services
        (agents, processes, knowledge) into the class → instance group tree. Services without a resolver have
        no subtree."""
        resolver = self._resource_resolvers().get(service_name)
        if resolver is None:
            return []
        tree = await resolver()
        return self._class_instance_groups(service_name, tree, resource_guards)

    def _resource_resolvers(self) -> dict[str, Callable[[], Awaitable[_ResourceTree]]]:
        """Maps a service to the loader that enumerates its resources. Adding a new enumerable service is a
        new entry here plus its ``_*_resources`` method — no branching in ``_resource_groups``."""
        return {
            "agent": self._agent_resources,
            "process": self._process_resources,
            "knowledge": self._knowledge_resources,
        }

    async def _agent_resources(self) -> _ResourceTree:
        # Imported here, not at module load, to break the import cycle (these services import API DTOs that
        # transitively reach this module).
        from swiss_ai_hub.api.routes.agent.agent_service import AgentService

        classes = [
            _ResourceNode(
                agent_class.agent_class, self._t.extract(agent_class.name), getattr(agent_class, "icon", None)
            )
            for agent_class in await AgentService.get_agent_classes(self._t)
        ]
        instances_by_class: dict[str, list[_ResourceNode]] = {}
        for instance in await AgentService.get_all_agent_instances(self._t):
            instances_by_class.setdefault(instance.agent_class, []).append(
                _ResourceNode(instance.agent_id, instance.name)
            )
        return _ResourceTree(classes, instances_by_class, ("agent_class", "agent_id"))

    async def _process_resources(self) -> _ResourceTree:
        from swiss_ai_hub.api.routes.process.process_service import ProcessService

        classes = [
            _ResourceNode(
                process_class.process_class, self._t.extract(process_class.name), getattr(process_class, "icon", None)
            )
            for process_class in await ProcessService.get_process_classes(self._t)
        ]
        instances_by_class: dict[str, list[_ResourceNode]] = {}
        for instance in await ProcessService.get_all_process_instances(self._t):
            instances_by_class.setdefault(instance.process_class, []).append(
                _ResourceNode(instance.process_id, instance.process_config.name)
            )
        return _ResourceTree(classes, instances_by_class, ("process_class", "process_id"))

    async def _knowledge_resources(self) -> _ResourceTree:
        from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

        databases: list[_ResourceNode] = []
        namespaces_by_database: dict[str, list[_ResourceNode]] = {}
        for database in KnowledgeService.get_databases(self._t):
            databases.append(_ResourceNode(database.name, database.display_name or database.name))
            namespaces_by_database[database.name] = [
                _ResourceNode(namespace.name, namespace.display_name or namespace.name)
                for namespace in database.namespaces
            ]
        return _ResourceTree(databases, namespaces_by_database, ("database", "namespace"))

    def _class_instance_groups(
        self, service_name: str, tree: _ResourceTree, resource_guards: dict[_GuardTemplate, AccessCatalogEntryMeta]
    ) -> list[CapabilityGroup]:
        """Builds the two-level class → instance tree. Class-level guards (one ``{param}``) become the class
        group's rows; instance-level guards (two) become each instance subgroup's rows."""
        class_param, instance_param = tree.param_names
        class_guards = sorted((template, meta) for template, meta in resource_guards.items() if template.is_class_level)
        instance_guards = sorted(
            (template, meta) for template, meta in resource_guards.items() if template.is_instance_level
        )

        groups = [
            self._class_group(
                service_name,
                class_node,
                tree.instances_by_class.get(class_node.value, []),
                class_guards,
                instance_guards,
                class_param,
                instance_param,
            )
            for class_node in tree.classes
        ]
        groups.sort(key=lambda group: group.label.lower())
        return groups

    def _class_group(
        self,
        service_name: str,
        class_node: _ResourceNode,
        instance_nodes: list[_ResourceNode],
        class_guards: list[tuple[_GuardTemplate, AccessCatalogEntryMeta]],
        instance_guards: list[tuple[_GuardTemplate, AccessCatalogEntryMeta]],
        class_param: str,
        instance_param: str,
    ) -> CapabilityGroup:
        class_capabilities = self._capabilities_for(class_guards, **{class_param: class_node.value})
        instance_groups = [
            self._instance_group(service_name, class_node, instance_node, instance_guards, class_param, instance_param)
            for instance_node in instance_nodes
        ]
        return CapabilityGroup(
            key=f"{service_name}:{class_node.value}",
            label=class_node.label,
            icon=class_node.icon,
            capabilities=class_capabilities,
            groups=instance_groups,
        )

    def _instance_group(
        self,
        service_name: str,
        class_node: _ResourceNode,
        instance_node: _ResourceNode,
        instance_guards: list[tuple[_GuardTemplate, AccessCatalogEntryMeta]],
        class_param: str,
        instance_param: str,
    ) -> CapabilityGroup:
        instance_capabilities = self._capabilities_for(
            instance_guards, **{class_param: class_node.value, instance_param: instance_node.value}
        )
        return CapabilityGroup(
            key=f"{service_name}:{class_node.value}:{instance_node.value}",
            label=instance_node.label,
            capabilities=instance_capabilities,
        )
