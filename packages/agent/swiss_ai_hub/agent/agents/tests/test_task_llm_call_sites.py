"""Verify which steps run on `task_llm` and which stay on the main `llm`.

Auxiliary/classification steps (detection, condensation, guards) must be attributed to the task model;
the user-facing answer stream and context-window trimming must stay on the main model. The auxiliary steps
the conversation capability contributes are exercised on the capability, with `RAGAgent` as the blueprint.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    AttachedFilesReadEvent,
    ConversationContextualizedEvent,
    KnowledgeSearchedEvent,
    LLMEvent,
    MemoryRecalledEvent,
    NotAMetaQuestionEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.agents.tests.test_task_llm_resolution import MAIN_MODEL, TASK_MODEL, _rag_config
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation

RAG_MODULE = "swiss_ai_hub.agent.agents.rag_agent.rag_agent"
CONVERSATION_MODULE = "swiss_ai_hub.agent.capabilities.conversation.conversation"

TASK_LLM_CASES = [("config_with_task_llm", TASK_MODEL), ("config_without_task_llm", MAIN_MODEL)]
TURN = ConversationContextualizedEvent(
    history=[ChatMessage(role=MessageRole.USER, content="hi")], query="what is the vacation policy?"
)


@pytest.fixture
def config_with_task_llm():
    return _rag_config(task_llm=LLMConfig(model_name=TASK_MODEL))


@pytest.fixture
def config_without_task_llm():
    return _rag_config()


def _event(**attributes) -> MagicMock:
    return MagicMock(**attributes)


def _reporting() -> MagicMock:
    reporting = MagicMock()
    reporting.__aenter__ = AsyncMock(return_value=MagicMock())
    reporting.__aexit__ = AsyncMock(return_value=False)
    return reporting


@pytest.mark.asyncio
@pytest.mark.parametrize(("config_fixture", "expected_model"), TASK_LLM_CASES)
async def test_inspection_uses_task_llm(request, config_fixture: str, expected_model: str) -> None:
    config = request.getfixturevalue(config_fixture)

    with patch(f"{CONVERSATION_MODULE}.do_detect_meta_question", new=AsyncMock()) as detect:
        await Conversation.inspect_message_step(
            RAGAgent(),
            request=Conversation.contextualize(history=TURN.history, message=_event(user_query="hi")),
            conversation=config,
            displayer=MagicMock(),
            t=MagicMock(),
            user=fake_user(),
        )

    assert detect.await_args.kwargs["llm_config"].model_name == expected_model


@pytest.mark.asyncio
@pytest.mark.parametrize(("config_fixture", "expected_model"), TASK_LLM_CASES)
async def test_meta_answer_uses_task_llm(request, config_fixture: str, expected_model: str) -> None:
    config = request.getfixturevalue(config_fixture)

    with (
        patch(f"{CONVERSATION_MODULE}.do_answer_meta_question", new=AsyncMock()) as answer,
        patch(f"{CONVERSATION_MODULE}.summarize_workflow_for_meta_answer", return_value="summary"),
    ):
        await Conversation.answer_meta_question_step(
            RAGAgent(),
            event=_event(),
            request=Conversation.contextualize(history=TURN.history),
            agent_config=config,
            conversation=config,
            displayer=MagicMock(),
            t=MagicMock(),
            user=fake_user(),
        )

    assert answer.await_args.kwargs["llm_config"].model_name == expected_model


@pytest.mark.asyncio
@pytest.mark.parametrize(("config_fixture", "expected_model"), TASK_LLM_CASES)
async def test_condensation_uses_task_llm(request, config_fixture: str, expected_model: str) -> None:
    config = request.getfixturevalue(config_fixture)
    condensed = ChatMessage(role=MessageRole.USER, content="q")

    with (
        patch.object(LLMConfig, "cost_reporting_llm", autospec=True, return_value=_reporting()) as cost_reporting,
        patch(f"{CONVERSATION_MODULE}.condense_standalone_question", new=AsyncMock(return_value=condensed)),
    ):
        await Conversation.derive_query_step(
            RAGAgent(),
            request=Conversation.contextualize(history=[condensed]),
            _cleared=NotAMetaQuestionEvent(reasoning="cleared"),
            conversation=config,
            displayer=MagicMock(display_thought=AsyncMock()),
            t=MagicMock(),
            user=fake_user(),
        )

    assert cost_reporting.call_args.args[0].model_name == expected_model


@pytest.mark.asyncio
@pytest.mark.parametrize(("config_fixture", "expected_model"), TASK_LLM_CASES)
async def test_few_shot_guard_uses_task_llm(request, config_fixture: str, expected_model: str) -> None:
    config = request.getfixturevalue(config_fixture)

    with patch(f"{RAG_MODULE}.do_few_shot_guard", new=AsyncMock()) as guard:
        await RAGAgent().few_shot_guard_step(
            ctx=TURN, agent_config=config, displayer=MagicMock(), t=MagicMock(), user=fake_user()
        )

    assert guard.await_args.args[2].model_name == expected_model


@pytest.mark.asyncio
@pytest.mark.parametrize(("config_fixture", "expected_model"), TASK_LLM_CASES)
async def test_context_sufficient_guard_uses_task_llm(request, config_fixture: str, expected_model: str) -> None:
    config = request.getfixturevalue(config_fixture)

    with patch(f"{RAG_MODULE}.do_context_sufficient_guard", new=AsyncMock()) as guard:
        await RAGAgent().context_sufficient_guard_step(
            agent_config=config,
            guard_config=MagicMock(),
            displayer=MagicMock(),
            t=MagicMock(),
            user=fake_user(),
            event=_event(),
            ctx=TURN,
            memories=MemoryRecalledEvent(),
            files=AttachedFilesReadEvent(),
            knowledge=KnowledgeSearchedEvent(),
            run_context=MagicMock(),
        )

    assert guard.await_args.args[5].model_name == expected_model


@pytest.mark.asyncio
async def test_main_answer_stays_on_main_llm(config_with_task_llm) -> None:
    with patch(f"{RAG_MODULE}.do_respond_with_llm", new=AsyncMock(return_value=LLMEvent())) as respond:
        await RAGAgent().respond_with_llm_step(
            outcome=_event(),
            composed=_event(history=[]),
            ctx=TURN,
            agent_config=config_with_task_llm,
            displayer=MagicMock(),
            topic=AgentInstanceTopic(
                agent_class="RAGAgent",
                agent_id="hr",
                thread_id="t",
                display_id="d",
                run_id="r",
                event_type="control_event",
                event_name="X",
                event_id="e",
            ),
            t=MagicMock(locale="en"),
            user=fake_user(),
        )

    assert respond.await_args.args[1].model_name == MAIN_MODEL
