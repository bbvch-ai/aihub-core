from typing import TYPE_CHECKING

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.access.access_level import AccessLevel
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import trace_fn

from swiss_ai_hub.api.routes.access.dto.access_dto import Access, UserAccess

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners import Runner


class AccessCatalogService:
    """Evaluates an AccessChecker against the full catalog of services, agents and processes.

    The same enumeration powers both the user "what can I see" view (``include_denied=False``)
    and the access-rule preview (``include_denied=True``, so denied resources can be shown crossed).
    """

    @staticmethod
    @trace_fn
    async def build_access(
        access_checker: AccessChecker, runner: "Runner", t: LocaleHandler, *, include_denied: bool
    ) -> Access:
        from swiss_ai_hub.api.routes.agent.agent_service import AgentService
        from swiss_ai_hub.api.routes.process.process_service import ProcessService

        access = Access()

        for controller in runner.controllers:
            service_access = access_checker.access_level_for_service(controller.service_name)
            if controller.additionally_required_permission and service_access != AccessLevel.ACCESS_DENIED:
                special_access = access_checker.access_level(controller.additionally_required_permission)
                # Effective level is the lower of the two gates, not just denied-if-denied: an ADMIN service
                # capped by a USER-only extra permission is USER, mirroring how the endpoint would enter.
                if special_access.value < service_access.value:
                    service_access = special_access
            if service_access == AccessLevel.ACCESS_DENIED and not include_denied:
                continue
            access.services.append(UserAccess(name=t.extract(controller.name), level=service_access))

        for agent_instance in await AgentService.get_all_agent_instances(t):
            agent_access = access_checker.access_level_for_agent(
                agent_class=agent_instance.agent_class, agent_id=agent_instance.agent_id
            )
            if agent_access == AccessLevel.ACCESS_DENIED and not include_denied:
                continue
            access.agents.append(UserAccess(name=agent_instance.name, level=agent_access))

        for process in await ProcessService.get_all_process_instances(t):
            process_access = access_checker.access_level_for_process(
                process_class=process.process_class, process_id=process.process_id
            )
            if process_access == AccessLevel.ACCESS_DENIED and not include_denied:
                continue
            access.processes.append(UserAccess(name=process.process_config.name, level=process_access))

        return access
