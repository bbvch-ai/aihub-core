"""Verify which steps run on `task_llm` and which stay on the main `llm`.

Auxiliary/classification steps (detection, condensation, guards) must be attributed to the task model;
the user-facing answer stream and context-window trimming must stay on the main model.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.generative_ai import LLMConfig

from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.agents.tests.test_task_llm_resolution import MAIN_MODEL, TASK_MODEL, _rag_config

RAG_MODULE = "swiss_ai_hub.agent.agents.rag_agent.rag_agent"


@pytest.fixture
def config_with_task_llm():
    return _rag_config(task_llm=LLMConfig(model_name=TASK_MODEL))


@pytest.fixture
def config_without_task_llm():
    return _rag_config()


def _event(**attributes) -> MagicMock:
    return MagicMock(**attributes)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("config_fixture", "expected_model"),
    [("config_with_task_llm", TASK_MODEL), ("config_without_task_llm", MAIN_MODEL)],
)
async def test_detect_meta_question_uses_task_llm(request, config_fixture: str, expected_model: str) -> None:
    config = request.getfixturevalue(config_fixture)

    with patch(f"{RAG_MODULE}.do_detect_meta_question", new=AsyncMock()) as detect:
        await RAGAgent().detect_meta_question_step(
            event=_event(user_query="hi"), agent_config=config, displayer=MagicMock(), t=MagicMock()
        )

    assert detect.await_args.kwargs["llm_config"].model_name == expected_model


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("config_fixture", "expected_model"),
    [("config_with_task_llm", TASK_MODEL), ("config_without_task_llm", MAIN_MODEL)],
)
async def test_answer_meta_question_uses_task_llm(request, config_fixture: str, expected_model: str) -> None:
    config = request.getfixturevalue(config_fixture)

    with (
        patch(f"{RAG_MODULE}.do_answer_meta_question", new=AsyncMock()) as answer,
        patch(f"{RAG_MODULE}.summarize_workflow_for_meta_answer", return_value="summary"),
    ):
        await RAGAgent().answer_meta_question_step(
            event=_event(),
            user_message_event=_event(messages=[]),
            agent_config=config,
            displayer=MagicMock(),
            t=MagicMock(),
        )

    assert answer.await_args.kwargs["llm_config"].model_name == expected_model


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("config_fixture", "expected_model"),
    [("config_with_task_llm", TASK_MODEL), ("config_without_task_llm", MAIN_MODEL)],
)
async def test_condense_standalone_question_uses_task_llm(request, config_fixture: str, expected_model: str) -> None:
    config = request.getfixturevalue(config_fixture)

    with patch(f"{RAG_MODULE}.do_condense_standalone_question", new=AsyncMock()) as condense:
        await RAGAgent().condense_standalone_question_step(
            event=_event(limited_history=[]),
            start_event=_event(),
            agent_config=config,
            t=MagicMock(),
            displayer=MagicMock(),
        )

    assert condense.await_args.args[2].model_name == expected_model


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("config_fixture", "expected_model"),
    [("config_with_task_llm", TASK_MODEL), ("config_without_task_llm", MAIN_MODEL)],
)
async def test_few_shot_guard_uses_task_llm(request, config_fixture: str, expected_model: str) -> None:
    config = request.getfixturevalue(config_fixture)

    with patch(f"{RAG_MODULE}.do_few_shot_guard", new=AsyncMock()) as guard:
        await RAGAgent().few_shot_guard_step(event=_event(), agent_config=config, displayer=MagicMock(), t=MagicMock())

    assert guard.await_args.args[2].model_name == expected_model


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("config_fixture", "expected_model"),
    [("config_with_task_llm", TASK_MODEL), ("config_without_task_llm", MAIN_MODEL)],
)
async def test_context_sufficient_guard_uses_task_llm(request, config_fixture: str, expected_model: str) -> None:
    config = request.getfixturevalue(config_fixture)

    with patch(f"{RAG_MODULE}.do_context_sufficient_guard", new=AsyncMock()) as guard:
        await RAGAgent().context_sufficient_guard_step(
            agent_config=config,
            guard_config=MagicMock(),
            displayer=MagicMock(),
            t=MagicMock(),
            event=_event(),
            user_query_event=_event(),
            chat_history_event=_event(limited_history=[]),
            run_context=MagicMock(),
        )

    assert guard.await_args.args[5].model_name == expected_model


@pytest.mark.asyncio
async def test_main_answer_and_trimming_stay_on_main_llm(config_with_task_llm) -> None:
    with patch(f"{RAG_MODULE}.do_respond_with_llm", new=AsyncMock()) as respond:
        await RAGAgent().respond_with_llm_step(
            event=_event(),
            limited_history_without_context=_event(limited_history=[]),
            agent_config=config_with_task_llm,
            guard_config=MagicMock(),
            displayer=MagicMock(),
            t=MagicMock(),
        )

    assert respond.await_args.args[4].model_name == MAIN_MODEL

    with (
        patch(f"{RAG_MODULE}.do_limit_chat_history_with_context") as trim,
        patch.object(LLMConfig, "token_counter", property(lambda config: f"counter::{config.model_name}")),
    ):
        await RAGAgent().limit_chat_history_with_context_step(
            context_event=_event(),
            chat_history_event=_event(limited_history=[]),
            _=None,
            start_event=_event(),
            agent_config=config_with_task_llm,
        )

    assert trim.call_args.args[3] == f"counter::{MAIN_MODEL}"
