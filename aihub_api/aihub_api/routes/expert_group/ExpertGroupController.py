from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Security, status
from mongoengine.errors import DoesNotExist, NotUniqueError

from aihub_api.routes.expert_group.dto.CreateExpertGroupRequest import CreateExpertGroupRequest
from aihub_api.routes.expert_group.dto.DeleteExpertGroupResponse import DeleteExpertGroupResponse
from aihub_api.routes.expert_group.dto.ExpertGroupResponse import ExpertGroupResponse
from aihub_api.routes.expert_group.dto.UpdateExpertGroupRequest import UpdateExpertGroupRequest
from aihub_api.routes.expert_group.ExpertGroupService import ExpertGroupService


class ExpertGroupController(Controller):
    """Controller for managing expert groups."""

    name = LocaleString(en="Expert Groups")
    description = LocaleString(en="Manage expert groups for the Expert-in-the-Loop workflow")
    icon = "mdi:account-group"

    def __init__(
        self,
        *,
        auth: AuthHandler,
        route: str = "/expert/groups",
        additionally_required_permission: str | None = None,
    ):
        super().__init__(
            auth=auth,
            route=route,
            additionally_required_permission=additionally_required_permission,
        )

    def create_group(self, route: str = "/") -> "ExpertGroupController":
        @self.router.post(
            route,
            summary="Create Expert Group",
            description="Creates a new expert group with a name and optional member list.",
            status_code=status.HTTP_201_CREATED,
            tags=self.tags,
        )
        async def create_group(
            group_data: CreateExpertGroupRequest,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.expert.groups.manage"))],
        ) -> ExpertGroupResponse:
            try:
                return ExpertGroupService.create_group(group_data)
            except NotUniqueError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Expert group with name '{group_data.name}' already exists.",
                )

        return self

    def get_groups(self, route: str = "/") -> "ExpertGroupController":
        @self.router.get(
            route,
            summary="List Expert Groups",
            description="Retrieves a list of all available expert groups.",
            tags=self.tags,
        )
        async def get_groups(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.expert.groups.read"))],
        ) -> list[ExpertGroupResponse]:
            return ExpertGroupService.list_groups()

        return self

    def get_group(self, route: str = "/{group_id}") -> "ExpertGroupController":
        @self.router.get(
            route,
            summary="Get Expert Group",
            description="Retrieves a single expert group by its unique ID.",
            tags=self.tags,
        )
        async def get_group(
            group_id: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.expert.groups.read"))],
        ) -> ExpertGroupResponse:
            try:
                return ExpertGroupService.get_group_by_id(group_id)
            except DoesNotExist:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expert group not found.")

        return self

    def update_group(self, route: str = "/{group_id}") -> "ExpertGroupController":
        @self.router.patch(
            route,
            summary="Update Expert Group",
            description="Updates an expert group's name, description, or member list.",
            tags=self.tags,
        )
        async def update_group(
            group_id: str,
            group_data: UpdateExpertGroupRequest,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.expert.groups.manage"))],
        ) -> ExpertGroupResponse:
            try:
                return ExpertGroupService.update_group(group_id, group_data)
            except DoesNotExist:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expert group not found.")
            except NotUniqueError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Expert group with name '{group_data.name}' already exists.",
                )

        return self

    def delete_group(self, route: str = "/{group_id}") -> "ExpertGroupController":
        @self.router.delete(
            route,
            summary="Delete Expert Group",
            description="Permanently deletes an expert group.",
            tags=self.tags,
        )
        async def delete_group(
            group_id: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.expert.groups.manage"))],
        ) -> DeleteExpertGroupResponse:
            try:
                ExpertGroupService.delete_group(group_id)
                return DeleteExpertGroupResponse()
            except DoesNotExist:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expert group not found.")

        return self

    def add_member(self, route: str = "/{group_id}/members/{user_id}") -> "ExpertGroupController":
        @self.router.post(
            route,
            summary="Add Member to Expert Group",
            description="Adds a user to an expert group.",
            tags=self.tags,
        )
        async def add_member(
            group_id: str,
            user_id: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.expert.groups.manage"))],
        ) -> ExpertGroupResponse:
            try:
                return ExpertGroupService.add_member(group_id, user_id)
            except DoesNotExist:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expert group not found.")

        return self

    def remove_member(self, route: str = "/{group_id}/members/{user_id}") -> "ExpertGroupController":
        @self.router.delete(
            route,
            summary="Remove Member from Expert Group",
            description="Removes a user from an expert group.",
            tags=self.tags,
        )
        async def remove_member(
            group_id: str,
            user_id: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.expert.groups.manage"))],
        ) -> ExpertGroupResponse:
            try:
                return ExpertGroupService.remove_member(group_id, user_id)
            except DoesNotExist:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expert group not found.")

        return self
