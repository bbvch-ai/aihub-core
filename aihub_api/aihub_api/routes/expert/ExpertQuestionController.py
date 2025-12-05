from typing import Annotated, Literal

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats_js
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, HTTPException, Query, Security
from mongoengine import DoesNotExist
from nats.js import JetStreamContext

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.expert.dto.ExpertQuestionDTO import ExpertQuestionDTO
from aihub_api.routes.expert.dto.PaginatedExpertQuestionsResponse import PaginatedExpertQuestionsResponse
from aihub_api.routes.expert.dto.SubmitAnswerRequest import SubmitAnswerRequest
from aihub_api.routes.expert.ExpertQuestionService import ExpertQuestionService


class ExpertQuestionController(Controller):
    """Controller for managing expert questions via the GUI interface."""

    name = LocaleString(en="Expert Questions")
    description = LocaleString(en="View and answer expert questions")
    icon = "mdi:account-question-outline"

    def __init__(self, *, auth: AuthHandler, route: str = "/expert/questions", **kwargs):
        super().__init__(auth=auth, route=route, **kwargs)

    def get_pending_questions(self, route: str = "/pending") -> "ExpertQuestionController":
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

    def get_questions_by_status(self, route: str = "") -> "ExpertQuestionController":
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

    def get_question(self, route: str = "/{question_id}") -> "ExpertQuestionController":
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

    def get_pending_count(self, route: str = "/pending/count") -> "ExpertQuestionController":
        @self.router.get(route, tags=self.tags, response_model=dict)
        async def get_pending_count(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.expert.questions.read"))],
            expert_group: str | None = Query(None, description="Filter by expert group"),
        ) -> dict:
            """Returns the count of pending questions."""
            count = ExpertQuestionService.count_pending(expert_group)
            return {"count": count}

        return self

    def submit_answer(self, route: str = "/{question_id}/answer") -> "ExpertQuestionController":
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

    def cancel_question(self, route: str = "/{question_id}/cancel") -> "ExpertQuestionController":
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
