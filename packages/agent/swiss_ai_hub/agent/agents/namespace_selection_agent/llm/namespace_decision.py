"""Structured output model for LLM-based namespace determination."""

from typing import Annotated

from pydantic import BaseModel, Field


class NamespaceDecision(BaseModel):
    """LLM decision on whether enough information exists to determine namespaces.

    The LLM analyzes the conversation and available namespaces to decide if it can
    confidently determine which namespaces the user wants to query, or if it needs
    more information via a follow-up question.

    Field descriptions ask for an explicit ``null`` rather than for omission, because strict structured
    outputs put *all* properties in ``required``: a model that skips a field can never reach a closing
    brace — the grammar masks it, so the model pads whitespace until ``max_tokens`` and the JSON arrives
    unterminated. Descriptions alone do not steer this reliably (measured: Gemma ignores them), so the
    binding instruction lives in the ``prompts.determination`` template; keep both in agreement.
    """

    has_enough_information: Annotated[
        bool,
        Field(
            description=(
                "True if the user's intent is clear enough to determine namespaces. "
                "False if more clarification is needed."
            )
        ),
    ]

    selected_namespaces: Annotated[
        dict[str, str] | None,
        Field(
            description=(
                "Map of bucket_name to exactly ONE namespace_name. "
                "Each bucket MUST have exactly one namespace selected - no more, no less. "
                "Always include this field: set it to null when has_enough_information is false."
            )
        ),
    ] = None

    follow_up_question: Annotated[
        str | None,
        Field(
            description=(
                "Question to ask the user for clarification. "
                "Always include this field: set it to null when has_enough_information is true."
            )
        ),
    ] = None

    reasoning: Annotated[
        str,
        Field(description="Brief explanation of why the decision was made."),
    ]
