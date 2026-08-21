"""Discovery must offer a schedule to exactly the agents that can be fired on one.

`AgentRunner` is the only place that knows both halves of that decision — the config, and which start
events the agent handles — so this is where the two published surfaces (the rendered form and the
submission JSON schema) are settled. Getting it wrong is quiet in both directions: a missing element
means an admin cannot schedule a schedulable agent, and a stray one means the API accepts a schedule
for an agent that will never fire.
"""

from typing import ClassVar

from swiss_ai_hub.core.agents import CRON_CONFIG_KEY, AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import AgentConfigSpecs, CronStartEvent, StopEvent, UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner
from swiss_ai_hub.agent.workflow.decorators.step import step


class _CronAgent(Agent):
    name: ClassVar[LocaleString] = LocaleString(en="Cron Agent")
    description: ClassVar[LocaleString] = LocaleString(en="Runs on a schedule")
    icon: ClassVar[str] = "mage:clock"

    @step()
    async def run(self, event: CronStartEvent, displayer: EventDisplayer) -> StopEvent:
        return StopEvent()


class _ChatAgent(Agent):
    name: ClassVar[LocaleString] = LocaleString(en="Chat Agent")
    description: ClassVar[LocaleString] = LocaleString(en="Answers messages")
    icon: ClassVar[str] = "mage:robot"

    @step()
    async def run(self, event: UserMessageEvent, displayer: EventDisplayer) -> StopEvent:
        return StopEvent()


def _runner(agent_type: type[Agent]) -> AgentRunner:
    return AgentRunner(agent_type=agent_type, agent_config=AgentConfig.as_form())


def _schema_properties(runner: AgentRunner) -> set[str]:
    specs = AgentConfigSpecs.from_agent_config(runner.agent_config, runner.agent_class)
    return set(specs.agent_config_schema["properties"])


class TestSchedulabilityIsDerived:
    def test_handling_the_cron_start_event_is_the_whole_opt_in(self) -> None:
        assert _runner(_CronAgent).is_schedulable is True

    def test_an_agent_that_does_not_handle_it_is_not_schedulable(self) -> None:
        assert _runner(_ChatAgent).is_schedulable is False


class TestSchedulableAgentsAdvertiseASchedule:
    def test_the_published_form_carries_the_cron_element(self) -> None:
        element = next(e for e in _runner(_CronAgent).form if e.name == CRON_CONFIG_KEY)

        assert element.formkit == "cronInput"

    def test_the_published_schema_accepts_a_schedule(self) -> None:
        """Without this the Admin UI would render a control the API then rejects."""
        assert CRON_CONFIG_KEY in _schema_properties(_runner(_CronAgent))


class TestOtherAgentsAdvertiseNone:
    def test_the_published_form_carries_no_cron_element(self) -> None:
        """#1580's acceptance criterion: agents that are not schedulable expose no schedule
        configuration. Structural here rather than a convention each blueprint has to remember."""
        assert CRON_CONFIG_KEY not in [element.name for element in _runner(_ChatAgent).form]

    def test_the_published_schema_does_not_accept_a_schedule(self) -> None:
        assert CRON_CONFIG_KEY not in _schema_properties(_runner(_ChatAgent))

    def test_the_runner_clears_a_schedule_the_blueprint_declared_itself(self) -> None:
        """The runner does not merely decline to add one — it removes what a blueprint set, so a config
        cannot advertise a schedule its agent will never be fired on."""
        config = AgentConfig.as_form()
        config.cron = AgentConfig.cron_form_field()

        runner = AgentRunner(agent_type=_ChatAgent, agent_config=config)

        assert runner.agent_config.cron is None
        assert CRON_CONFIG_KEY not in [element.name for element in runner.form]
