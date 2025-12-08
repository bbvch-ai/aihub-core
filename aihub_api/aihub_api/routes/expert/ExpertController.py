from typing import Annotated, Literal

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats_js
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, HTTPException, Query, Security, status
from mongoengine import DoesNotExist
from mongoengine.errors import NotUniqueError
from nats.js import JetStreamContext

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.expert.dto.ExpertQuestionDTO import ExpertQuestionDTO
from aihub_api.routes.expert.dto.PaginatedExpertQuestionsResponse import PaginatedExpertQuestionsResponse
from aihub_api.routes.expert.dto.SubmitAnswerRequest import SubmitAnswerRequest
from aihub_api.routes.expert.ExpertQuestionService import ExpertQuestionService
from aihub_api.routes.expert_group.dto.CreateExpertGroupRequest import CreateExpertGroupRequest
from aihub_api.routes.expert_group.dto.DeleteExpertGroupResponse import DeleteExpertGroupResponse
from aihub_api.routes.expert_group.dto.ExpertGroupResponse import ExpertGroupResponse
from aihub_api.routes.expert_group.dto.UpdateExpertGroupRequest import UpdateExpertGroupRequest
from aihub_api.routes.expert_group.ExpertGroupService import ExpertGroupService


class ExpertController(Controller):
    """Unified controller for managing expert questions and groups via the GUI interface."""

    name = LocaleString(en="Experts")
    description = LocaleString(en="View and answer expert questions, manage expert groups")
    icon = "mdi:account-question-outline"

    def __init__(self, *, auth: AuthHandler, route: str = "/expert", **kwargs):
        super().__init__(auth=auth, route=route, **kwargs)

    # ==================== Questions Endpoints ====================

    def get_pending_questions(self, route: str = "/questions/pending") -> "ExpertController":
        @self.router.get(route, tags=self.tags, response_model=PaginatedExpertQuestionsResponse)
        async def get_pending_questions(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.expert.questions.read"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            expert_group: str | None = Query(None, description="Filter by expert group"),
            page: int = Query(1, ge=1),
            page_size: int = Query(20, ge=1, le=100),
        ) -> PaginatedExpertQuestionsResponse:
            """Retrieves a paginated list of pending expert questions."""
            return ExpertQuestionService.get_pending_questions(
                expert_group=expert_group,
                page=page,
                page_size=page_size,
            )

        return self

    def get_questions_by_status(self, route: str = "/questions") -> "ExpertController":
        @self.router.get(route, tags=self.tags, response_model=PaginatedExpertQuestionsResponse)
        async def get_questions_by_status(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.expert.questions.read"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            status: Literal["pending", "answered", "expired", "cancelled"] = Query("pending"),
            expert_group: str | None = Query(None, description="Filter by expert group"),
            page: int = Query(1, ge=1),
            page_size: int = Query(20, ge=1, le=100),
        ) -> PaginatedExpertQuestionsResponse:
            """Retrieves a paginated list of expert questions filtered by status."""
            return ExpertQuestionService.get_questions_by_status(
                status=status,
                expert_group=expert_group,
                page=page,
                page_size=page_size,
            )

        return self

    def get_question(self, route: str = "/questions/{question_id}") -> "ExpertController":
        @self.router.get(route, tags=self.tags, response_model=ExpertQuestionDTO)
        async def get_question(
            question_id: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.expert.questions.read"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ExpertQuestionDTO:
            """Retrieves a single expert question by ID."""
            try:
                return ExpertQuestionService.get_question_by_id(question_id)
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="Question not found.")

        return self

    def get_pending_count(self, route: str = "/questions/pending/count") -> "ExpertController":
        @self.router.get(route, tags=self.tags, response_model=dict)
        async def get_pending_count(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.expert.questions.read"))],
            expert_group: str | None = Query(None, description="Filter by expert group"),
        ) -> dict:
            """Returns the count of pending questions."""
            count = ExpertQuestionService.count_pending(expert_group)
            return {"count": count}

        return self

    def submit_answer(self, route: str = "/questions/{question_id}/answer") -> "ExpertController":
        @self.router.post(route, tags=self.tags, response_model=ExpertQuestionDTO)
        async def submit_answer(
            question_id: str,
            request: SubmitAnswerRequest,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.expert.questions.answer"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            js: Annotated[JetStreamContext, Depends(use_nats_js)],
            expert_group: str | None = Query(None, description="The expert group the responder belongs to"),
        ) -> ExpertQuestionDTO:
            """Submits an answer to an expert question and notifies the requesting agent."""
            try:
                return await ExpertQuestionService.submit_answer(
                    question_id=question_id,
                    response=request.response,
                    user=user,
                    js=js,
                    expert_group=expert_group,
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        return self

    def cancel_question(self, route: str = "/questions/{question_id}/cancel") -> "ExpertController":
        @self.router.post(route, tags=self.tags, response_model=ExpertQuestionDTO)
        async def cancel_question(
            question_id: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.expert.questions.cancel"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ExpertQuestionDTO:
            """Cancels a pending expert question (admin only)."""
            try:
                return ExpertQuestionService.cancel_question(question_id)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        return self

    # ==================== Groups Endpoints ====================

    def create_group(self, route: str = "/groups") -> "ExpertController":
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

    def get_groups(self, route: str = "/groups") -> "ExpertController":
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

    def get_group(self, route: str = "/groups/{group_id}") -> "ExpertController":
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

    def update_group(self, route: str = "/groups/{group_id}") -> "ExpertController":
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

    def delete_group(self, route: str = "/groups/{group_id}") -> "ExpertController":
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

    def add_member(self, route: str = "/groups/{group_id}/members/{user_id}") -> "ExpertController":
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

    def remove_member(self, route: str = "/groups/{group_id}/members/{user_id}") -> "ExpertController":
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
