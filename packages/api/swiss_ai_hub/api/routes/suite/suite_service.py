from typing import TYPE_CHECKING

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.access.access_level import AccessLevel
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import trace_fn

from swiss_ai_hub.api.routes.suite.dto.service_dto import ServiceDTO
from swiss_ai_hub.api.routes.suite.dto.suite_dto import SuiteDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners import Runner


class SuiteService:
    @staticmethod
    @trace_fn
    def get_suite(user: UserIdentity, runner: "Runner", t: LocaleHandler) -> SuiteDTO:
        services: list[ServiceDTO] = []
        access_checker = AccessChecker.from_user(user)
        for controller in runner.controllers:
            user_service_access = access_checker.access_level_for_service(controller.service_name)
            if user_service_access == AccessLevel.ACCESS_DENIED:
                continue

            if controller.additionally_required_permission:
                user_special_access = access_checker.access_level(controller.additionally_required_permission)
                if user_special_access == AccessLevel.ACCESS_DENIED:
                    continue

            services.append(
                ServiceDTO(
                    name=t.extract(controller.name),
                    description=t.extract(controller.description),
                    icon=controller.icon,
                    path=f"/service{controller.base_route}",
                    user_is_admin=user_service_access == AccessLevel.ACCESS_ADMIN,
                )
            )
        services.sort(key=lambda s: s.name.lower())
        return SuiteDTO(services=services)
