"""
Integration guard for the guard-reject exit path: when the agent-suitability guard rejects a request,
the run used to terminate via a bare StopEvent with no conversation metadata at all. Drives the real
dispatcher with detection/guard forced, proving both title and follow-ups now fire on that path.

Needs the dev stack (NATS + Valkey) but no LLM — detection, the guard, and the metadata generators are
all stubbed. Marked self_hosted so the lean CI skips it.
"""

from unittest.mock import patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    ConversationTitleEvent,
    FollowUpQuestionsEvent,
    NotAMetaQuestionEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import FewShotExample, LLMConfig
from swiss_ai_hub.core.generative_ai.guards import GuardResult
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent import FewShotAgent
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent_config import FewShotAgentConfig
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner
from swiss_ai_hub.agent.steps.prompting.few_shot_step.few_shot_step_config import FewShotStepConfig

pytestmark = pytest.mark.self_hosted

FEW_SHOT_MODULE = "swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent"


def _config() -> FewShotAgentConfig:
    return FewShotAgentConfig(
        agent_id="guard_reject_metadata_test",
        name=LocaleString(en="Test FewShot"),
        description=LocaleString(en="A test few-shot agent."),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        few_shot=FewShotStepConfig(
            few_shot_examples=[FewShotExample(user=LocaleString(en="hi"), agent=LocaleString(en="hello"))],
            system_prompt=LocaleString(en="Respond briefly."),
        ),
    )


def _user_message(text: str) -> UserMessageEvent:
    return UserMessageEvent(messages=[ChatMessage(content=text, role=MessageRole.USER)], user=fake_user(), locale="en")


@async_test
async def test_guard_reject_generates_title_and_follow_ups(monkeypatch):
    async def fake_detect(*, user_query, **_):
        return NotAMetaQuestionEvent(reasoning="forced normal")

    async def fake_guard(**_):
        return GuardResult(success=False, reasoning="forced rejection")

    async def fake_generate_metadata(chat_messages, llm_config, displayer, t, thread_context, user):
        await displayer.display_event(ConversationTitleEvent(title="Fake Title"))
        await displayer.display_event(FollowUpQuestionsEvent(questions=["Fake follow-up?"]))

    monkeypatch.setattr(f"{FEW_SHOT_MODULE}.do_detect_meta_question", fake_detect)
    monkeypatch.setattr(f"{FEW_SHOT_MODULE}.agent_description_guard", fake_guard)

    runner = AgentTestRunner(agent_type=FewShotAgent, agent_config=_config())
    # autospec, not monkeypatch.setattr: a bare stub silently accepts whatever the step passes, so when
    # the real helper gained its `user` parameter this test kept passing while production raised
    # TypeError on every guard rejection. autospec binds the call against the real signature instead.
    with patch(f"{FEW_SHOT_MODULE}.generate_conversation_metadata", autospec=True, side_effect=fake_generate_metadata):
        async with runner.test_run(delay_before_stop=20) as topic:
            await runner.send_event_from_topic(topic=topic, start_event=_user_message("Fight Club"))

    assert runner.has_stop_event, "guard-reject path did not terminate the run"
    assert runner.has_event_of_class(ConversationTitleEvent), "guard-reject path did not generate a title"
    assert runner.has_event_of_class(FollowUpQuestionsEvent), "guard-reject path did not generate follow-ups"
    assert not runner.has_exception_event
