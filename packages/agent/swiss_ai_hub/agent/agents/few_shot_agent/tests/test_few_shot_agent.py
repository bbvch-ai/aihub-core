import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.events.agent import (
    AgentSuitabilityAcceptEvent,
    GuardRejectionEvent,
    LimitChatHistoryEvent,
    LLMEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import FewShotExample, LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.few_shot_agent.events.few_shot_event import FewShotEvent
from swiss_ai_hub.agent.agents.few_shot_agent.events.few_shot_standalone_question_condenser_event import (
    FewShotStandaloneQuestionCondenserEvent,
)
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent import FewShotAgent
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent_config import FewShotAgentConfig
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner
from swiss_ai_hub.agent.steps.prompting.few_shot_step.few_shot_step_config import FewShotStepConfig

scenarios("features/few_shot_agent.feature")

enable_logging()


@pytest.fixture
def agent_config_data():
    """
    Stores all dynamic config items at the scenario level so they persist
    across steps in a single scenario.
    """
    return {"description": "", "system_prompt": "", "few_shot_examples": []}


@pytest.fixture
def self_hosted_llm_config():
    """
    Return an LLM config for testing with LiteLLM.
    """
    return LLMConfig(model_name="text-generation/gpt-oss-120b")


@given("I have an empty agent config")
def given_empty_scenario_config(agent_config_data):
    """
    Just ensure scenario_data is initialized. (It's already done by the fixture, but
    we have a step for clarity.)
    """
    pass


@given(parsers.parse('the agent description is "{desc}"'))
def given_agent_description(agent_config_data, desc: str):
    agent_config_data["description"] = desc


@given(parsers.parse('the few shot system prompt is "{prompt}"'))
def given_system_prompt(agent_config_data, prompt: str):
    agent_config_data["system_prompt"] = prompt


@given("the following few-shot examples:")
def given_few_shot_examples(agent_config_data, datatable):
    """
    Parse the table of few-shot examples from the feature and store them in the config.
    Example table rows:
      | user         | agent      |
      | James Bond   | 🤵🍸🔫      |
      | Harry Potter | 👓⚡️🪄     |
    """
    for row in datatable[1:]:
        user_text, agent_text = row
        agent_config_data["few_shot_examples"].append({"user": user_text, "agent": agent_text})


@pytest.mark.usefixtures("self_hosted_agent_config")
@given(
    "I create a FewShotAgent runner with the config with valid self hosted configuration", target_fixture="agent_runner"
)
def _(agent_config_data, self_hosted_llm_config):
    """
    Finally build the actual AgentTestRunner now that we have
    description, system prompt, and examples in scenario_data.
    """
    examples = [
        FewShotExample(user=LocaleString(en=example["user"]), agent=LocaleString(en=example["agent"]))
        for example in agent_config_data["few_shot_examples"]
    ]

    config = FewShotAgentConfig(
        agent_id="few_shot_agent",
        name=LocaleString(en="FewShotAgent"),
        description=LocaleString(en=agent_config_data["description"]),
        llm=self_hosted_llm_config,
        number_of_input_tokens=100000,
        few_shot=FewShotStepConfig(
            few_shot_examples=examples,
            system_prompt=LocaleString(en=agent_config_data["system_prompt"]),
        ),
    )

    return AgentTestRunner(agent_type=FewShotAgent, agent_config=config)


@when(parsers.parse('the start event is sent with a user query "{query}"'))
@async_test
async def when_start_event_sent(agent_runner: AgentTestRunner, query: str):
    async with agent_runner.test_run(delay_before_stop=30) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                locale="en",
                user=fake_user(),
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
            ),
        )


@then(parsers.parse('a StartEvent is present with payload "{payload}"'))
def then_start_event_present(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.has_start_event, "Agent did not receive StartEvent"

    start_event = agent_runner.get_event_of_class(UserMessageEvent)
    user_messages = [m for m in start_event.messages if m.role == MessageRole.USER]
    assert any(payload in m.content for m in user_messages), "No user message payload found in StartEvent"


@then("a LimitChatHistoryEvent is present")
def then_limit_chat_history_event(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(LimitChatHistoryEvent), "Agent did not produce a LimitChatHistoryEvent"


@then("a RightAgentEvent is present")
def then_guard_or_rejection_event(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(AgentSuitabilityAcceptEvent), (
        "Agent did not produce AgentSuitabilityAcceptEvent"
    )


@then("a FewShotStandaloneQuestionCondenserEvent is present with condensed question")
def then_few_shot_condenser_event(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(FewShotStandaloneQuestionCondenserEvent), (
        "FewShotStandaloneQuestionCondenserEvent was not emitted"
    )
    condenser_event = agent_runner.get_event_of_class(FewShotStandaloneQuestionCondenserEvent)
    assert condenser_event.condensed_chat_message.content, "Condensed question content was empty"


@then("a FewShotEvent is present with few shot context")
def then_few_shot_event(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(FewShotEvent), "FewShotEvent was not emitted"
    few_shot_event = agent_runner.get_event_of_class(FewShotEvent)
    assert few_shot_event.few_shot_examples, "No few shot examples found in FewShotEvent"
    assert few_shot_event.system_prompt, "No few shot system prompt found in FewShotEvent"
    assert few_shot_event.full_context, "No full context found in FewShotEvent"


@then("an LLMEvent is present with a generated response")
def then_llm_event(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(LLMEvent), "LLMEvent not produced"
    llm_event = agent_runner.get_event_of_class(LLMEvent)
    assert llm_event.output_messages[0].content, "LLMEvent response content is empty"


@then("a StopEvent is present")
def then_stop_event_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not produce StopEvent"


@then("a GuardRejectionEvent is present")
def then_guard_reject_event_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(GuardRejectionEvent), "Agent did not produce GuardRejectionEvent"
