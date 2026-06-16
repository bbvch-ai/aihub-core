from typing import TYPE_CHECKING

from fastapi.routing import APIRoute
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.infrastructure import trace_fn
from swiss_ai_hub.core.routes.tenant_scoped_controller import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.access.capability import CAPABILITY_ATTRIBUTE
from swiss_ai_hub.api.routes.access.dto.access_capabilities_dto import (
    AccessCapabilitiesResponse,
    Capability,
    CapabilityGroup,
)

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners import Runner

# Generic labels for the implicit service gate (not a ``user_with_permission`` route, so not annotated).
_SERVICE_USE_LABEL = ApiLocaleString.from_i18n_path("api.access.capabilities.ops.service.use.label")
_SERVICE_USE_DESCRIPTION = ApiLocaleString.from_i18n_path("api.access.capabilities.ops.service.use.description")
_SERVICE_ADMIN_LABEL = ApiLocaleString.from_i18n_path("api.access.capabilities.ops.service.administer.label")
_SERVICE_ADMIN_DESCRIPTION = ApiLocaleString.from_i18n_path(
    "api.access.capabilities.ops.service.administer.description"
)


class AccessCapabilityService:
    """Builds a capability catalog by introspecting each controller's routes at runtime.

    Groups are controllers (services). Each route annotated with ``@capability(...)`` becomes a
    capability: its **access rule is derived from the route's own ``user_with_permission`` guard**
    (the single source of truth — never restated), and its label/description come from the annotation.
    A guard containing ``?`` (a ``?>``/``?*`` query) has no single satisfying rule, so its checkbox is
    read-only. Path-param guards are enumerated across the concrete resources. Each capability is
    evaluated against the supplied draft rules (``granted`` / ``locked``).
    """

    @staticmethod
    @trace_fn
    async def build_capabilities(
        access_rules: list[str], runner: "Runner", t: LocaleHandler, tenant_rules: list[str] | None = None
    ) -> AccessCapabilitiesResponse:
        """``tenant_rules`` (when given) hides capabilities the tenant ceiling cannot grant — the role
        editor must never offer, or even reveal, access the tenant itself does not hold. Pass ``None``
        when editing the tenant ceiling itself (sysadmin), where the full catalog must stay visible.
        """
        from swiss_ai_hub.api.routes.agent.agent_service import AgentService
        from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService
        from swiss_ai_hub.api.routes.process.process_service import ProcessService

        draft_set = set(access_rules)
        groups: list[CapabilityGroup] = []

        for controller in runner.controllers:
            if not isinstance(controller, TenantScopedController):
                continue
            svc = controller.service_name
            all_templates, annotated = AccessCapabilityService._introspect(controller)
            gate = {"aihub.user.?>", "aihub.admin.?>", f"aihub.user.service.{svc}", f"aihub.admin.service.{svc}"}
            resource = {tmpl: meta for tmpl, meta in annotated.items() if tmpl not in gate}

            gate_specs = [(_SERVICE_USE_LABEL, _SERVICE_USE_DESCRIPTION, f"aihub.user.service.{svc}")]
            if f"aihub.admin.service.{svc}" in all_templates:
                gate_specs.append((_SERVICE_ADMIN_LABEL, _SERVICE_ADMIN_DESCRIPTION, f"aihub.admin.service.{svc}"))

            capabilities = [
                cap
                for label, description, guard in gate_specs
                if (
                    cap := AccessCapabilityService._cap(
                        label, description, guard, {}, access_rules, draft_set, tenant_rules, t
                    )
                )
            ]
            # 0-param resource guards (e.g. "see all assistants", memory) live on the controller itself.
            capabilities += [
                cap
                for tmpl, meta in sorted(resource.items())
                if tmpl.count("{") == 0
                and (
                    cap := AccessCapabilityService._cap(
                        meta.label, meta.description, tmpl, {}, access_rules, draft_set, tenant_rules, t
                    )
                )
            ]

            subgroups = await AccessCapabilityService._resource_groups(
                svc, resource, access_rules, draft_set, tenant_rules, t, AgentService, ProcessService, KnowledgeService
            )

            groups.append(
                CapabilityGroup(
                    key=f"service:{svc}",
                    label=t.extract(controller.name),
                    icon=getattr(controller, "icon", None),
                    capabilities=capabilities,
                    groups=subgroups,
                )
            )

        groups = [group for group in groups if AccessCapabilityService._prune(group)]
        groups.sort(key=lambda group: group.label.lower())
        return AccessCapabilitiesResponse(groups=groups)

    @staticmethod
    def _prune(group: CapabilityGroup) -> bool:
        """Drops nested groups left empty by tenant-scope filtering; returns whether the group survives."""
        group.groups = [sub for sub in group.groups if AccessCapabilityService._prune(sub)]
        return bool(group.capabilities or group.groups)

    @staticmethod
    def _introspect(controller: TenantScopedController) -> tuple[set[str], dict[str, object]]:
        """Returns (all guard templates, {guard template -> CapabilityMeta}) for the controller's routes."""
        all_templates: set[str] = set()
        annotated: dict[str, object] = {}
        for route in controller.router.routes:
            if not isinstance(route, APIRoute):
                continue
            template = AccessCapabilityService._route_template(route)
            if not template:
                continue
            all_templates.add(template)
            meta = getattr(route, CAPABILITY_ATTRIBUTE, None)
            if meta is not None:
                annotated.setdefault(template, meta)
        return all_templates, annotated

    @staticmethod
    def _route_template(route: APIRoute) -> str | None:
        """The ``user_with_permission`` template guarding the route — read from its dependency closure."""
        stack = [route.dependant]
        while stack:
            dependant = stack.pop()
            call = getattr(dependant, "call", None)
            closure = getattr(call, "__closure__", None)
            if call is not None and closure:
                for _, cell in zip(call.__code__.co_freevars, closure, strict=False):
                    try:
                        value = cell.cell_contents
                    except ValueError:
                        continue
                    if isinstance(value, str) and value.startswith("aihub."):
                        return value
            stack.extend(dependant.dependencies)
        return None

    @staticmethod
    def _cap(
        label_locale: LocaleString,
        description_locale: LocaleString,
        guard_template: str,
        subs: dict[str, str],
        access_rules: list[str],
        draft_set: set[str],
        tenant_rules: list[str] | None,
        t,
    ) -> Capability | None:
        # The grant IS the guard, unless the guard is a ``?``-query with no single satisfying rule.
        grant_template = guard_template if "?" not in guard_template else None
        label = t.extract(label_locale)
        description = t.extract(description_locale)

        if grant_template is not None:
            rule = grant_template.format(**subs)
            if tenant_rules is not None and not AccessChecker.rules_grant(tenant_rules, rule):
                return None
            granted = AccessChecker.rules_grant(access_rules, rule)
            return Capability(
                key=rule,
                label=label,
                description=description,
                rule=rule,
                granted=granted,
                locked=granted and rule not in draft_set,
                toggleable=True,
            )
        guard = guard_template.format(**subs)
        if tenant_rules is not None and not AccessChecker(tenant_rules, tenant_rules).has_access(guard):
            return None
        return Capability(
            key=f"ro:{guard}",
            label=label,
            description=description,
            rule=None,
            granted=AccessChecker(access_rules, access_rules).has_access(guard),
            locked=False,
            toggleable=False,
        )

    @staticmethod
    async def _resource_groups(
        svc, resource, access_rules, draft_set, tenant_rules, t, agent_service, process_service, knowledge_service
    ) -> list[CapabilityGroup]:
        if svc == "agent":
            classes = [
                (c.agent_class, t.extract(c.name), getattr(c, "icon", None))
                for c in await agent_service.get_agent_classes(t)
            ]
            children: dict[str, list[tuple[str, str]]] = {}
            for instance in await agent_service.get_all_agent_instances(t):
                children.setdefault(instance.agent_class, []).append((instance.agent_id, instance.name))
            return AccessCapabilityService._two_level(
                svc, classes, children, ("agent_class", "agent_id"), resource, access_rules, draft_set, tenant_rules, t
            )
        if svc == "process":
            classes = [
                (c.process_class, t.extract(c.name), getattr(c, "icon", None))
                for c in await process_service.get_process_classes(t)
            ]
            children = {}
            for instance in await process_service.get_all_process_instances(t):
                children.setdefault(instance.process_class, []).append(
                    (instance.process_id, instance.process_config.name)
                )
            return AccessCapabilityService._two_level(
                svc,
                classes,
                children,
                ("process_class", "process_id"),
                resource,
                access_rules,
                draft_set,
                tenant_rules,
                t,
            )
        if svc == "knowledge":
            databases = []
            children = {}
            for database in knowledge_service.get_databases(t):
                databases.append((database.name, database.display_name or database.name, None))
                children[database.name] = [(ns.name, ns.display_name or ns.name) for ns in database.namespaces]
            return AccessCapabilityService._two_level(
                svc, databases, children, ("database", "namespace"), resource, access_rules, draft_set, tenant_rules, t
            )
        return []

    @staticmethod
    def _two_level(
        svc, parents, children_of, param_names, resource, access_rules, draft_set, tenant_rules, t
    ) -> list[CapabilityGroup]:
        parent_param, child_param = param_names
        parent_specs = sorted((tmpl, meta) for tmpl, meta in resource.items() if tmpl.count("{") == 1)
        child_specs = sorted((tmpl, meta) for tmpl, meta in resource.items() if tmpl.count("{") == 2)

        groups: list[CapabilityGroup] = []
        for parent_value, parent_label, parent_icon in parents:
            parent_subs = {parent_param: parent_value}
            parent_caps = [
                cap
                for tmpl, meta in parent_specs
                if (
                    cap := AccessCapabilityService._cap(
                        meta.label, meta.description, tmpl, parent_subs, access_rules, draft_set, tenant_rules, t
                    )
                )
            ]
            child_groups = []
            for child_value, child_label in children_of.get(parent_value, []):
                child_subs = {parent_param: parent_value, child_param: child_value}
                child_caps = [
                    cap
                    for tmpl, meta in child_specs
                    if (
                        cap := AccessCapabilityService._cap(
                            meta.label, meta.description, tmpl, child_subs, access_rules, draft_set, tenant_rules, t
                        )
                    )
                ]
                child_groups.append(
                    CapabilityGroup(
                        key=f"{svc}:{parent_value}:{child_value}", label=child_label, capabilities=child_caps
                    )
                )
            groups.append(
                CapabilityGroup(
                    key=f"{svc}:{parent_value}",
                    label=parent_label,
                    icon=parent_icon,
                    capabilities=parent_caps,
                    groups=child_groups,
                )
            )
        groups.sort(key=lambda group: group.label.lower())
        return groups
