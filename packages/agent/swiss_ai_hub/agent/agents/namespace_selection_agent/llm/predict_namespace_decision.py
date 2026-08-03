"""Namespace determination call, hardened against providers that never terminate strict JSON."""

import logging

from llama_index.core.llms import LLM
from llama_index.core.prompts import BasePromptTemplate
from pydantic import ValidationError

from swiss_ai_hub.agent.agents.namespace_selection_agent.llm.namespace_decision import NamespaceDecision

logger = logging.getLogger(__name__)

# A decision is a follow-up question plus a sentence of reasoning — ~200 tokens. The cap exists for the
# failure mode, not the happy path: a model that omits a required key pads whitespace at ~108 tok/s until
# max_tokens, so the model's own 8192 costs ~76s per attempt where 1024 costs ~9s.
MAX_DECISION_TOKENS = 1024


async def predict_namespace_decision(
    llm: LLM,
    prompt: BasePromptTemplate,
    available_namespaces: str,
    conversation_history: str,
) -> NamespaceDecision:
    """
    Predict the namespace decision, falling back to function calling when strict JSON comes back malformed.

    The two mechanisms fail on different models — Gemma cannot terminate a strict ``response_format``
    object it decided to leave a key out of, while Kimi returns truncated tool arguments — so trying
    ``response_format`` first and function calling second covers both instead of either alone.
    """
    bounded_llm = llm.model_copy(update={"max_tokens": MAX_DECISION_TOKENS})
    try:
        return await bounded_llm.astructured_predict(
            NamespaceDecision,
            prompt,
            available_namespaces=available_namespaces,
            conversation_history=conversation_history,
        )
    except (ValidationError, ValueError) as malformed_structured_output:
        logger.warning(
            "Namespace decision came back malformed on the response_format path, retrying via function calling: %s",
            malformed_structured_output,
        )

    function_calling_llm = bounded_llm.model_copy(update={"should_use_structured_outputs": False})
    return await function_calling_llm.astructured_predict(
        NamespaceDecision,
        prompt,
        available_namespaces=available_namespaces,
        conversation_history=conversation_history,
    )
