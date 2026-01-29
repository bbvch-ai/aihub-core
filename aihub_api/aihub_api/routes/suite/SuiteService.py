from typing import TYPE_CHECKING

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

from aihub_api.routes.suite.dto.ServiceDTO import ServiceDTO
from aihub_api.routes.suite.dto.SuiteDTO import SuiteDTO

if TYPE_CHECKING:
    from aihub_lib.runners.Runner import Runner


class SuiteService:
    @staticmethod
    @trace_fn
    def get_suite(user: UserIdentity, runner: "Runner", t: LocaleHandler) -> SuiteDTO:
        services: list[ServiceDTO] = []
        access_checker = AccessChecker.from_user(user)
        for controller in runner.controllers:
            user_service_access = access_checker.access_level_for_service(controller.service_name)
            if user_service_access != AccessLevel.ACCESS_ADMIN:
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
