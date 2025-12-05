"""Configuration for optional expert escalation workflow."""

from typing import Annotated

from pydantic import BaseModel, Field


class ExpertWorkflowConfig(BaseModel):
    """
    Configuration for optional expert escalation workflow.

    When enabled, the RAGAgent will escalate to human experts
    when retrieved context is insufficient to answer a question.
    """

    enabled: Annotated[
        bool,
        Field(description="Whether expert escalation is enabled"),
    ] = False

    expert_asking_agent_class: Annotated[
        str,
        Field(description="Class name of ExpertAskingAgent"),
    ] = "ExpertAskingAgent"

    expert_asking_agent_id: Annotated[
        str,
        Field(description="Instance ID of ExpertAskingAgent"),
    ] = "expert_asking_agent"

    max_context_nodes_for_expert: Annotated[
        int,
        Field(description="Max nodes to include when formulating expert question", ge=1),
    ] = 5
