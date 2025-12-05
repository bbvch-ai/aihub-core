from datetime import datetime
from typing import Annotated, Literal

from aihub_lib.persistence.expert.ExpertQuestionEntity import ExpertQuestionEntity
from pydantic import BaseModel, Field

PriorityLevel = Literal["low", "normal", "high", "urgent"]
QuestionStatus = Literal["pending", "answered", "expired", "cancelled"]
LocaleCode = Literal["de", "en", "fr", "it"]


class RequestingUserDTO(BaseModel):
    """Information about the user who triggered the question."""

    user_id: Annotated[str, Field(description="The unique identifier of the requesting user.")]
    user_name: Annotated[str | None, Field(description="The display name of the requesting user.")] = None
    email: Annotated[str | None, Field(description="The email address of the requesting user.")] = None


class RequestingAgentDTO(BaseModel):
    """Information about the agent requesting expert input."""

    agent_class: Annotated[str, Field(description="The class of the requesting agent.")]
    agent_id: Annotated[str, Field(description="The instance ID of the requesting agent.")]
    thread_id: Annotated[str, Field(description="The thread ID where the question originated.")]
    run_id: Annotated[str, Field(description="The run ID of the agent workflow.")]


class ExpertResponderDTO(BaseModel):
    """Information about the expert who answered the question."""

    user_id: Annotated[str, Field(description="The unique identifier of the expert.")]
    user_name: Annotated[str | None, Field(description="The display name of the expert.")] = None
    email: Annotated[str | None, Field(description="The email address of the expert.")] = None
    expert_group: Annotated[str | None, Field(description="The expert group this user belongs to.")] = None


class ExpertQuestionDTO(BaseModel):
    """Data Transfer Object for an expert question."""

    id: Annotated[str, Field(description="The unique identifier of the question.")]
    question: Annotated[str, Field(description="The question posed to experts.")]
    context: Annotated[str | None, Field(description="Additional context to help answer the question.")] = None
    expert_group: Annotated[str | None, Field(description="The expert group this question is directed to.")] = None
    priority: Annotated[PriorityLevel, Field(description="The priority level of the question.")] = "normal"
    locale: Annotated[LocaleCode, Field(description="The language of the question.")] = "en"
    status: Annotated[QuestionStatus, Field(description="The current status of the question.")]
    requesting_user: Annotated[RequestingUserDTO, Field(description="Information about the user who triggered this.")]
    requesting_agent: Annotated[RequestingAgentDTO, Field(description="Information about the requesting agent.")]
    response: Annotated[str | None, Field(description="The expert's answer, if provided.")] = None
    responder: Annotated[ExpertResponderDTO | None, Field(description="Information about the expert who answered.")] = (
        None
    )
    responded_at: Annotated[datetime | None, Field(description="When the question was answered.")] = None
    created_at: Annotated[datetime, Field(description="When the question was created.")]
    updated_at: Annotated[datetime, Field(description="When the question was last updated.")]

    @classmethod
    def from_entity(cls, entity: ExpertQuestionEntity) -> "ExpertQuestionDTO":
        """Creates an ExpertQuestionDTO from an ExpertQuestionEntity."""
        requesting_user = RequestingUserDTO(
            user_id=entity.requesting_user.user_id,
            user_name=entity.requesting_user.user_name,
            email=entity.requesting_user.email,
        )

        requesting_agent = RequestingAgentDTO(
            agent_class=entity.requesting_agent.agent_class,
            agent_id=entity.requesting_agent.agent_id,
            thread_id=entity.requesting_agent.thread_id,
            run_id=entity.requesting_agent.run_id,
        )

        responder = None
        if entity.responder:
            responder = ExpertResponderDTO(
                user_id=entity.responder.user_id,
                user_name=entity.responder.user_name,
                email=entity.responder.email,
                expert_group=entity.responder.expert_group,
            )

        return cls(
            id=str(entity.id),
            question=entity.question,
            context=entity.context,
            expert_group=entity.expert_group,
            priority=entity.priority,
            locale=entity.locale,
            status=entity.status,
            requesting_user=requesting_user,
            requesting_agent=requesting_agent,
            response=entity.response,
            responder=responder,
            responded_at=entity.responded_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
