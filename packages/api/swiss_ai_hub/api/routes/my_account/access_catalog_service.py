from typing import TYPE_CHECKING

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.access.access_level import AccessLevel
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import trace_fn

from swiss_ai_hub.api.routes.my_account.dto.access_dto import Access, UserAccess

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
        return Access(
            services=AccessCatalogService._service_entries(access_checker, runner, t, include_denied=include_denied),
            agents=await AccessCatalogService._agent_entries(access_checker, t, include_denied=include_denied),
            processes=await AccessCatalogService._process_entries(access_checker, t, include_denied=include_denied),
        )

    @staticmethod
    def _service_entries(
        access_checker: AccessChecker, runner: "Runner", t: LocaleHandler, *, include_denied: bool
    ) -> list[UserAccess]:
        entries: list[UserAccess] = []
        for controller in runner.controllers:
            level = AccessCatalogService._effective_service_access(access_checker, controller)
            if level == AccessLevel.ACCESS_DENIED and not include_denied:
                continue
            entries.append(UserAccess(name=t.extract(controller.name), level=level))
        return entries

    @staticmethod
    def _effective_service_access(access_checker: AccessChecker, controller) -> AccessLevel:
        """A service's level, capped by its ``additionally_required_permission`` when set: an ADMIN service
        behind a USER-only extra permission is USER, mirroring how the endpoint would actually enter."""
        level = access_checker.access_level_for_service(controller.service_name)
        if controller.additionally_required_permission and level != AccessLevel.ACCESS_DENIED:
            special = access_checker.access_level(controller.additionally_required_permission)
            if special.value < level.value:
                return special
        return level

    @staticmethod
    async def _agent_entries(
        access_checker: AccessChecker, t: LocaleHandler, *, include_denied: bool
    ) -> list[UserAccess]:
        from swiss_ai_hub.api.routes.agent.agent_service import AgentService

        entries: list[UserAccess] = []
        for agent_instance in await AgentService.get_all_agent_instances(t):
            level = access_checker.access_level_for_agent(
                agent_class=agent_instance.agent_class, agent_id=agent_instance.agent_id
            )
            if level == AccessLevel.ACCESS_DENIED and not include_denied:
                continue
            entries.append(UserAccess(name=agent_instance.name, level=level))
        return entries

    @staticmethod
    async def _process_entries(
        access_checker: AccessChecker, t: LocaleHandler, *, include_denied: bool
    ) -> list[UserAccess]:
        from swiss_ai_hub.api.routes.process.process_service import ProcessService

        entries: list[UserAccess] = []
        for process in await ProcessService.get_all_process_instances(t):
            level = access_checker.access_level_for_process(
                process_class=process.process_class, process_id=process.process_id
            )
            if level == AccessLevel.ACCESS_DENIED and not include_denied:
                continue
            entries.append(UserAccess(name=process.process_config.name, level=level))
        return entries
