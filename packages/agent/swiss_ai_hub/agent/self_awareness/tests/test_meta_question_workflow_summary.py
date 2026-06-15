from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.self_awareness.meta_question_workflow_summary import (
    SELF_AWARENESS_STEP_NAMES,
    summarize_workflow_for_meta_answer,
)


def test_summary_is_a_mermaid_flowchart() -> None:
    summary = summarize_workflow_for_meta_answer(RAGAgent, LocaleHandler("en"))

    assert summary.startswith("flowchart TD")
    assert " --> " in summary
    assert "respond_with_llm_step" in summary


def test_self_awareness_steps_are_pruned() -> None:
    summary = summarize_workflow_for_meta_answer(RAGAgent, LocaleHandler("en"))

    for step_name in SELF_AWARENESS_STEP_NAMES:
        assert step_name not in summary


def test_summary_is_localized() -> None:
    english = summarize_workflow_for_meta_answer(RAGAgent, LocaleHandler("en"))
    german = summarize_workflow_for_meta_answer(RAGAgent, LocaleHandler("de"))

    assert english != german
