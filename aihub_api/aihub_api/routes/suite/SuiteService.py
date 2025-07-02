from typing import TYPE_CHECKING, List

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler

from aihub_api.routes.suite.dto.ServiceDTO import ServiceDTO
from aihub_api.routes.suite.dto.SuiteDTO import SuiteDTO

if TYPE_CHECKING:
    from aihub_api.runners.ApiRunner import ApiRunner


class SuiteService:
    @staticmethod
    def get_suite(user: UserIdentity, runner: "ApiRunner", t: LocaleHandler) -> SuiteDTO:
        services: List[ServiceDTO] = []
        access_checker = AccessChecker.from_user(user)
        for controller in runner.controllers:
            service_name = controller.__class__.__name__.lower().replace("controller", "")
            user_access = access_checker.access_level_for_service(service_name)
            print("service", service_name, user_access)
            if user_access == AccessLevel.ACCESS_DENIED:
                continue
            services.append(
                ServiceDTO(
                    name=t.extract(controller.name),
                    description=t.extract(controller.description),
                    icon=controller.icon,
                    path=f"/service{controller.base_route}",
                    user_is_admin=user_access == AccessLevel.ACCESS_ADMIN
                )
            )
        return SuiteDTO(
            services=services
        )
