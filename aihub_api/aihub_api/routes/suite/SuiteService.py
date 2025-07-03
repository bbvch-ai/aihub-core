from typing import TYPE_CHECKING

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler

from aihub_api.routes.suite.dto.ServiceDTO import ServiceDTO
from aihub_api.routes.suite.dto.SuiteDTO import SuiteDTO

if TYPE_CHECKING:
    from aihub_api.runners.ApiRunner import ApiRunner


class SuiteService:
    @staticmethod
    def get_suite(user: UserIdentity, runner: "ApiRunner", t: LocaleHandler) -> SuiteDTO:
        return SuiteDTO(
            services=[
                ServiceDTO(
                    name=t.extract(controller.name),
                    description=t.extract(controller.description),
                    icon=controller.icon,
                    path=f"{'/admin' if controller.is_admin_only else '/service'}{controller.base_route}",
                )
                for controller in runner.controllers
            ]
        )
