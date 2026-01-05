"""
Approval response interpreter for NamespaceSelectionAgent.

Uses LLM to interpret user's response to the namespace selection approval question.
Determines if user approved, rejected, or wants to correct the selection.
"""

from typing import Annotated, Literal

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import KnowledgeSource
from llama_index.core.llms import LLM
from llama_index.core.prompts.rich import RichPromptTemplate
from pydantic import BaseModel, Field

from aihub_agent.agents.NamespaceSelectionAgent.helpers.namespace_selector import AvailableNamespace


class ApprovalInterpretation(BaseModel):
    """Result of interpreting user's approval response."""

    intent: Annotated[
        Literal["approve", "reject", "correct"],
        Field(description="The user's intent: approve, reject, or correct the selection"),
    ]

    correction_details: Annotated[
        str | None,
        Field(description="If correcting, what the user wants changed"),
    ] = None

    preferred_sources: Annotated[
        list[str] | None,
        Field(description="Specific namespace names the user mentioned as preferences"),
    ] = None

    reasoning: Annotated[
        str,
        Field(description="Brief explanation of how the response was interpreted"),
    ]


async def interpret_approval_response(
    user_response: str,
    current_selection: list[KnowledgeSource],
    available_namespaces: list[AvailableNamespace],
    llm: LLM,
    t: LocaleHandler,
) -> ApprovalInterpretation:
    """
    Interpret user's response to namespace selection approval.

    Determines if user:
    - Approved: "yes", "ok", "proceed", "looks good", etc.
    - Rejected: "no", "not those", "wrong", etc. without alternatives
    - Corrected: "use X instead", "also include Y", "only Z", etc.

    Args:
        user_response: The user's text response.
        current_selection: Currently selected knowledge sources.
        available_namespaces: All available namespaces for selection.
        llm: LLM for interpretation.
        t: Locale handler for translations.

    Returns:
        ApprovalInterpretation with the user's intent and any corrections.
    """
    # Build context about current selection and available sources
    current_str = "\n".join(f"- {s.display_name or s.namespace_name}" for s in current_selection)
    available_str = "\n".join(
        f"- {ns.display_name or ns.namespace_name}: {ns.description or 'No description'}" for ns in available_namespaces
    )

    # Create a localized result model for structured prediction
    class LocalizedApprovalInterpretation(ApprovalInterpretation):
        intent: Annotated[
            Literal["approve", "reject", "correct"],
            Field(description=t("agent.namespace_selection.prompts.approval_intent_description")),
        ]
        correction_details: Annotated[
            str | None,
            Field(description=t("agent.namespace_selection.prompts.correction_details_description")),
        ] = None
        preferred_sources: Annotated[
            list[str] | None,
            Field(description=t("agent.namespace_selection.prompts.preferred_sources_description")),
        ] = None
        reasoning: Annotated[
            str,
            Field(description=t("agent.namespace_selection.prompts.interpretation_reasoning_description")),
        ]

    LocalizedApprovalInterpretation.__doc__ = t("agent.namespace_selection.prompts.approval_interpretation_docstring")

    prompt_text = t(
        "agent.namespace_selection.prompts.approval_interpretation",
        user_response=user_response,
        current_selection=current_str,
        available_sources=available_str,
    )
    prompt = RichPromptTemplate(prompt_text)

    result = await llm.astructured_predict(
        LocalizedApprovalInterpretation,
        prompt,
    )

    return ApprovalInterpretation.model_validate(result)


async def interpret_topic_change_response(
    user_response: str,
    llm: LLM,
    t: LocaleHandler,
) -> bool:
    """
    Interpret user's response to topic change question.

    Simple yes/no interpretation for "Should I search different sources?"

    Args:
        user_response: The user's text response.
        llm: LLM for interpretation.
        t: Locale handler for translations.

    Returns:
        True if user wants new sources, False if they want to keep current sources.
    """

    class TopicChangeInterpretation(BaseModel):
        wants_new_sources: Annotated[
            bool,
            Field(description=t("agent.namespace_selection.prompts.wants_new_sources_description")),
        ]
        reasoning: Annotated[
            str,
            Field(description=t("agent.namespace_selection.prompts.topic_response_reasoning_description")),
        ]

    TopicChangeInterpretation.__doc__ = t("agent.namespace_selection.prompts.topic_change_interpretation_docstring")

    prompt_text = t(
        "agent.namespace_selection.prompts.topic_change_interpretation",
        user_response=user_response,
    )
    prompt = RichPromptTemplate(prompt_text)

    result = await llm.astructured_predict(
        TopicChangeInterpretation,
        prompt,
    )

    return result.wants_new_sources
