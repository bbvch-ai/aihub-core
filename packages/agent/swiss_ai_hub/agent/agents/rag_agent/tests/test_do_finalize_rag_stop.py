from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    ContextInsufficientRejectEvent,
    FewShotRejectEvent,
    LLMEvent,
    RAGFailureReason,
    RAGFailureStopEvent,
    RAGSuccessStopEvent,
)
from swiss_ai_hub.core.events.agent.semantic.llm.message import Message

from swiss_ai_hub.agent.agents.rag_agent.events.expert_answer_context_event import ExpertAnswerContextEvent
from swiss_ai_hub.agent.rag.step_functions import do_finalize_rag_stop


def _llm_event(content: str = "final answer") -> LLMEvent:
    return LLMEvent(
        input_messages=[],
        output_messages=[Message.from_string(role=MessageRole.ASSISTANT, content=content)],
    )


def _expert_answer_context() -> ExpertAnswerContextEvent:
    return ExpertAnswerContextEvent(
        context_message=ChatMessage(role=MessageRole.SYSTEM, content="expert says X"),
    )


def test_expert_answer_context_overrides_context_insufficient_reject():
    result = do_finalize_rag_stop(
        llm_event=_llm_event("grounded answer"),
        expert_answer_context=_expert_answer_context(),
        few_shot_reject=None,
        context_insufficient_reject=ContextInsufficientRejectEvent(reason="not enough"),
    )

    assert isinstance(result, RAGSuccessStopEvent)
    assert result.answer == "grounded answer"


def test_few_shot_reject_wins_over_context_insufficient_reject():
    result = do_finalize_rag_stop(
        llm_event=_llm_event(),
        expert_answer_context=None,
        few_shot_reject=FewShotRejectEvent(reason="no matching example"),
        context_insufficient_reject=ContextInsufficientRejectEvent(reason="not enough"),
    )

    assert isinstance(result, RAGFailureStopEvent)
    assert result.reason == RAGFailureReason.FEW_SHOT_REJECTED


def test_context_insufficient_reject_yields_failure_when_alone():
    result = do_finalize_rag_stop(
        llm_event=_llm_event(),
        expert_answer_context=None,
        few_shot_reject=None,
        context_insufficient_reject=ContextInsufficientRejectEvent(reason="not enough"),
    )

    assert isinstance(result, RAGFailureStopEvent)
    assert result.reason == RAGFailureReason.CONTEXT_INSUFFICIENT


def test_no_rejects_yields_success():
    result = do_finalize_rag_stop(
        llm_event=_llm_event("plain answer"),
        expert_answer_context=None,
        few_shot_reject=None,
        context_insufficient_reject=None,
    )

    assert isinstance(result, RAGSuccessStopEvent)
    assert result.answer == "plain answer"
