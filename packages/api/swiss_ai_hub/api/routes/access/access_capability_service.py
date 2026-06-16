from typing import TYPE_CHECKING, Annotated, NamedTuple

from fastapi.routing import APIRoute
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.infrastructure import trace_fn
from swiss_ai_hub.core.routes.tenant_scoped_controller import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.access.capability import CAPABILITY_ATTRIBUTE, CapabilityMeta
from swiss_ai_hub.api.routes.access.dto.access_capabilities_dto import (
    AccessCapabilitiesResponse,
    Capability,
    CapabilityGroup,
)

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners import Runner

# The implicit per-service gate is not backed by a ``user_with_permission`` route, so it carries no
# ``@capability`` annotation — its labels live here instead of being read off a route.
_SERVICE_USE_LABEL = ApiLocaleString.from_i18n_path("api.access.capabilities.ops.service.use.label")
_SERVICE_USE_DESCRIPTION = ApiLocaleString.from_i18n_path("api.access.capabilities.ops.service.use.description")
_SERVICE_ADMIN_LABEL = ApiLocaleString.from_i18n_path("api.access.capabilities.ops.service.administer.label")
_SERVICE_ADMIN_DESCRIPTION = ApiLocaleString.from_i18n_path(
    "api.access.capabilities.ops.service.administer.description"
)


class _ResourceNode(NamedTuple):
    """One concrete resource a templated guard is expanded over — an agent or process class, a class
    instance, a knowledge database or a namespace. ``value`` is substituted for the guard's path
    parameter; ``label`` and ``icon`` drive the rendered group header."""

    value: str
    label: str
    icon: str | None = None


class AccessCapabilityService:
    """Builds the human-readable capability catalog by introspecting each controller's routes at runtime.

    Groups are services (controllers). Each route annotated with ``@capability(...)`` becomes a capability
    whose access rule **is** the route's own ``user_with_permission`` guard — the single source of truth,
    never restated. ``granted`` is evaluated through the subject's ``AccessChecker`` with the exact
    ``has_access`` call the endpoint enforces with, so the table cannot drift from enforcement: the sysadmin
    short-circuit and the tenant ceiling are honoured for free. A guard containing a ``?`` query has no
    single satisfying rule, so its row is read-only; templated guards are enumerated over the concrete
    resources of the service.
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
        granted_rules = subject.access_rules
        groups: list[CapabilityGroup] = []
        for controller in runner.controllers:
            if not isinstance(controller, TenantScopedController):
                continue
            group = await AccessCapabilityService._service_group(controller, subject, granted_rules, ceiling, t)
            if AccessCapabilityService._prune(group):
                groups.append(group)
        groups.sort(key=lambda group: group.label.lower())
        return AccessCapabilitiesResponse(groups=groups)

    @staticmethod
    async def _service_group(
        controller: TenantScopedController,
        subject: AccessChecker,
        granted_rules: set[str],
        ceiling: AccessChecker | None,
        t: LocaleHandler,
    ) -> CapabilityGroup:
        """Builds one top-level group for a service: its service-level gate, any resource-wide capabilities
        (zero-parameter guards), and the nested class/instance tree for enumerable resources."""
        service_name = controller.service_name
        all_templates, annotated_guards = AccessCapabilityService._introspect(controller)
        gate_templates = {
            "aihub.user.?>",
            "aihub.admin.?>",
            f"aihub.user.service.{service_name}",
            f"aihub.admin.service.{service_name}",
        }
        resource_guards = {tmpl: meta for tmpl, meta in annotated_guards.items() if tmpl not in gate_templates}

        capabilities = AccessCapabilityService._service_gate_capabilities(
            service_name, all_templates, subject, granted_rules, ceiling, t
        )
        capabilities += [
            capability
            for guard_template, meta in sorted(resource_guards.items())
            if guard_template.count("{") == 0
            and (
                capability := AccessCapabilityService._capability_for_guard(
                    meta.label, meta.description, guard_template, {}, subject, granted_rules, ceiling, t
                )
            )
        ]
        subgroups = await AccessCapabilityService._resource_groups(
            service_name, resource_guards, subject, granted_rules, ceiling, t
        )
        return CapabilityGroup(
            key=f"service:{service_name}",
            label=t.extract(controller.name),
            icon=getattr(controller, "icon", None),
            capabilities=capabilities,
            groups=subgroups,
        )

    @staticmethod
    def _service_gate_capabilities(
        service_name: str,
        all_templates: set[str],
        subject: AccessChecker,
        granted_rules: set[str],
        ceiling: AccessChecker | None,
        t: LocaleHandler,
    ) -> list[Capability]:
        """The implicit per-service gate: every service has a "Use" capability; "Administer" is surfaced
        only when the controller actually exposes an ``aihub.admin.service.<name>`` endpoint."""
        gate_specs = [(_SERVICE_USE_LABEL, _SERVICE_USE_DESCRIPTION, f"aihub.user.service.{service_name}")]
        if f"aihub.admin.service.{service_name}" in all_templates:
            gate_specs.append((_SERVICE_ADMIN_LABEL, _SERVICE_ADMIN_DESCRIPTION, f"aihub.admin.service.{service_name}"))
        return [
            capability
            for label, description, guard_template in gate_specs
            if (
                capability := AccessCapabilityService._capability_for_guard(
                    label, description, guard_template, {}, subject, granted_rules, ceiling, t
                )
            )
        ]

    @staticmethod
    def _introspect(controller: TenantScopedController) -> tuple[set[str], dict[str, CapabilityMeta]]:
        """Reads every route's ``user_with_permission`` guard. Returns all guard templates (used to detect
        whether an "Administer" gate exists) and the subset annotated with ``@capability`` (the catalog rows)."""
        all_templates: set[str] = set()
        annotated_guards: dict[str, CapabilityMeta] = {}
        for route in controller.router.routes:
            if not isinstance(route, APIRoute):
                continue
            template = AccessCapabilityService._route_template(route)
            if template is None:
                continue
            all_templates.add(template)
            meta = getattr(route, CAPABILITY_ATTRIBUTE, None)
            if isinstance(meta, CapabilityMeta):
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
            if isinstance(value, str) and value.startswith("aihub."):
                return value
        return None

    @staticmethod
    def _capability_for_guard(
        label_locale: LocaleString,
        description_locale: LocaleString,
        guard_template: str,
        path_param_values: Annotated[
            dict[str, str],
            "Concrete values for the guard's ``{path_params}`` (e.g. ``{'agent_class': 'WeatherAgent'}``); "
            "empty for guards without parameters.",
        ],
        subject: AccessChecker,
        granted_rules: set[str],
        ceiling: AccessChecker | None,
        t: LocaleHandler,
    ) -> Capability | None:
        """Builds one capability row. ``granted`` comes from ``subject.has_access`` — the same call the
        endpoint's guard makes — so the row matches enforcement (sysadmin short-circuit and ceiling included).

        A guard containing ``?`` (a ``?>``/``?*`` existence query) has no single satisfying rule, so the row is
        read-only; a concrete guard *is* the grantable rule and is toggleable, and is ``locked`` when access
        comes from a broader rule than the one this checkbox would add. Returns ``None`` when a ``ceiling`` is
        given that cannot grant the capability — it is then hidden, never merely disabled (no information leak).
        """
        guard = guard_template.format(**path_param_values)
        if ceiling is not None and not ceiling.has_access(guard):
            return None

        label = t.extract(label_locale)
        description = t.extract(description_locale)
        granted = subject.has_access(guard)

        if "?" in guard_template:
            return Capability(
                key=f"ro:{guard}",
                label=label,
                description=description,
                rule=None,
                granted=granted,
                locked=False,
                toggleable=False,
            )
        return Capability(
            key=guard,
            label=label,
            description=description,
            rule=guard,
            granted=granted,
            locked=granted and guard not in granted_rules,
            toggleable=True,
        )

    @staticmethod
    def _prune(group: CapabilityGroup) -> bool:
        """Drops nested groups emptied by ceiling-filtering; returns whether ``group`` still shows anything."""
        group.groups = [sub for sub in group.groups if AccessCapabilityService._prune(sub)]
        return bool(group.capabilities or group.groups)

    @staticmethod
    async def _resource_groups(
        service_name: str,
        resource_guards: dict[str, CapabilityMeta],
        subject: AccessChecker,
        granted_rules: set[str],
        ceiling: AccessChecker | None,
        t: LocaleHandler,
    ) -> list[CapabilityGroup]:
        """Expands the controller's ``{path_param}`` guards over the concrete resources of enumerable services
        (agents, processes, knowledge) into the class → instance group tree. Other services have no subtree."""
        # Imported here, not at module load, to break the import cycle (these services import API DTOs that
        # transitively reach this module).
        from swiss_ai_hub.api.routes.agent.agent_service import AgentService
        from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService
        from swiss_ai_hub.api.routes.process.process_service import ProcessService

        if service_name == "agent":
            classes = [
                _ResourceNode(agent_class.agent_class, t.extract(agent_class.name), getattr(agent_class, "icon", None))
                for agent_class in await AgentService.get_agent_classes(t)
            ]
            instances_by_class: dict[str, list[_ResourceNode]] = {}
            for instance in await AgentService.get_all_agent_instances(t):
                instances_by_class.setdefault(instance.agent_class, []).append(
                    _ResourceNode(instance.agent_id, instance.name)
                )
            return AccessCapabilityService._class_instance_groups(
                service_name,
                classes,
                instances_by_class,
                ("agent_class", "agent_id"),
                resource_guards,
                subject,
                granted_rules,
                ceiling,
                t,
            )
        if service_name == "process":
            classes = [
                _ResourceNode(
                    process_class.process_class, t.extract(process_class.name), getattr(process_class, "icon", None)
                )
                for process_class in await ProcessService.get_process_classes(t)
            ]
            instances_by_class = {}
            for instance in await ProcessService.get_all_process_instances(t):
                instances_by_class.setdefault(instance.process_class, []).append(
                    _ResourceNode(instance.process_id, instance.process_config.name)
                )
            return AccessCapabilityService._class_instance_groups(
                service_name,
                classes,
                instances_by_class,
                ("process_class", "process_id"),
                resource_guards,
                subject,
                granted_rules,
                ceiling,
                t,
            )
        if service_name == "knowledge":
            databases = []
            namespaces_by_database: dict[str, list[_ResourceNode]] = {}
            for database in KnowledgeService.get_databases(t):
                databases.append(_ResourceNode(database.name, database.display_name or database.name))
                namespaces_by_database[database.name] = [
                    _ResourceNode(namespace.name, namespace.display_name or namespace.name)
                    for namespace in database.namespaces
                ]
            return AccessCapabilityService._class_instance_groups(
                service_name,
                databases,
                namespaces_by_database,
                ("database", "namespace"),
                resource_guards,
                subject,
                granted_rules,
                ceiling,
                t,
            )
        return []

    @staticmethod
    def _class_instance_groups(
        service_name: str,
        classes: list[_ResourceNode],
        instances_by_class: dict[str, list[_ResourceNode]],
        param_names: Annotated[
            tuple[str, str],
            "The guard's (class-level, instance-level) path-parameter names, e.g. ``('agent_class', 'agent_id')``.",
        ],
        resource_guards: dict[str, CapabilityMeta],
        subject: AccessChecker,
        granted_rules: set[str],
        ceiling: AccessChecker | None,
        t: LocaleHandler,
    ) -> list[CapabilityGroup]:
        """Builds the two-level class → instance tree. Guards with one ``{param}`` are class-level capabilities
        (e.g. "Create instance"); guards with two are instance-level (e.g. "Use this instance")."""
        class_param, instance_param = param_names
        class_guards = sorted((tmpl, meta) for tmpl, meta in resource_guards.items() if tmpl.count("{") == 1)
        instance_guards = sorted((tmpl, meta) for tmpl, meta in resource_guards.items() if tmpl.count("{") == 2)

        groups: list[CapabilityGroup] = []
        for class_node in classes:
            class_substitutions = {class_param: class_node.value}
            class_capabilities = [
                capability
                for guard_template, meta in class_guards
                if (
                    capability := AccessCapabilityService._capability_for_guard(
                        meta.label,
                        meta.description,
                        guard_template,
                        class_substitutions,
                        subject,
                        granted_rules,
                        ceiling,
                        t,
                    )
                )
            ]
            instance_groups: list[CapabilityGroup] = []
            for instance_node in instances_by_class.get(class_node.value, []):
                instance_substitutions = {class_param: class_node.value, instance_param: instance_node.value}
                instance_capabilities = [
                    capability
                    for guard_template, meta in instance_guards
                    if (
                        capability := AccessCapabilityService._capability_for_guard(
                            meta.label,
                            meta.description,
                            guard_template,
                            instance_substitutions,
                            subject,
                            granted_rules,
                            ceiling,
                            t,
                        )
                    )
                ]
                instance_groups.append(
                    CapabilityGroup(
                        key=f"{service_name}:{class_node.value}:{instance_node.value}",
                        label=instance_node.label,
                        capabilities=instance_capabilities,
                    )
                )
            groups.append(
                CapabilityGroup(
                    key=f"{service_name}:{class_node.value}",
                    label=class_node.label,
                    icon=class_node.icon,
                    capabilities=class_capabilities,
                    groups=instance_groups,
                )
            )
        groups.sort(key=lambda group: group.label.lower())
        return groups
