"""Discovery must offer a schedule to exactly the agents that can be fired on one.

`AgentRunner` is the only place that knows both halves of that decision — the config, and which start
events the agent handles — so this is where the two published surfaces (the rendered form and the
submission JSON schema) are settled. Getting it wrong is quiet in both directions: a missing element
means an admin cannot schedule a schedulable agent, and a stray one means the API accepts a schedule
for an agent that will never fire.
"""

from typing import Annotated, ClassVar

from pydantic import Field
from swiss_ai_hub.core.agents import CRON_CONFIG_KEY, AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import CronStartEvent, StopEvent, UserMessageEvent
from swiss_ai_hub.core.form import ConfigSpecs
from swiss_ai_hub.core.form.elements.cron_input import CronInput
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.scheduling import CronSchedule

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


class _SettingsConfig(AgentConfig):
    """A blueprint with a setting of its own, so field ordering is observable."""

    system_prompt: Annotated[str | InputText, Field(description="Prompt")] = "hi"

    @classmethod
    def as_form(cls) -> "_SettingsConfig":
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            system_prompt=InputText(label=LocaleString(en="Prompt")),
        )


def _runner(agent_type: type[Agent]) -> AgentRunner:
    return AgentRunner(agent_type=agent_type, agent_config=AgentConfig.as_form())


def _schema_properties(runner: AgentRunner) -> set[str]:
    specs = ConfigSpecs.from_form(runner.published_config, runner.agent_class)
    return set(specs.config_schema["properties"])


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
        """The published view does not merely decline to add one — it removes what a blueprint set, so a
        config cannot advertise a schedule its agent will never be fired on."""
        config = AgentConfig.as_form()
        config.cron = AgentConfig.cron_form_field()

        runner = AgentRunner(agent_type=_ChatAgent, agent_config=config)

        assert runner.published_config.cron is None
        assert CRON_CONFIG_KEY not in [element.name for element in runner.form]


class TestTheCallerConfigIsNotAltered:
    """`AgentTestRunner` hands `agent_config` straight back as the run's actual config, so anything the
    runner writes onto it becomes runtime data rather than form metadata."""

    def test_a_data_mode_schedule_survives_construction(self) -> None:
        """Replacing this with the form element would hand the agent its own form to execute against —
        inert only until a schedulable blueprint is driven from a data-mode config."""
        schedule = CronSchedule(
            minute="0", hour="9", day_of_month="*", month="*", day_of_week="*", timezone="Europe/Zurich"
        )
        config = AgentConfig(
            agent_id="demo",
            name=LocaleString(en="Demo"),
            description=LocaleString(en="Demo"),
            cron=schedule,
        )

        runner = AgentRunner(agent_type=_CronAgent, agent_config=config)

        assert runner.agent_config.cron == schedule

    def test_the_published_view_still_offers_the_form_element(self) -> None:
        """Preserving the caller's config must not cost discovery its control."""
        config = AgentConfig(
            agent_id="demo",
            name=LocaleString(en="Demo"),
            description=LocaleString(en="Demo"),
        )

        runner = AgentRunner(agent_type=_CronAgent, agent_config=config)

        assert isinstance(runner.published_config.cron, CronInput)
        assert CRON_CONFIG_KEY in [element.name for element in runner.form]


class TestTheScheduleRendersAfterTheBlueprintsOwnSettings:
    def test_cron_is_the_last_element(self) -> None:
        """`cron` is declared on the base and Pydantic orders base fields first, so left in place it
        lands between the identity fields and a blueprint's first real setting. It is platform-injected,
        not something the blueprint asks an admin to configure."""
        runner = AgentRunner(agent_type=_CronAgent, agent_config=_SettingsConfig.as_form())

        assert [element.name for element in runner.form][-1] == CRON_CONFIG_KEY

    def test_the_blueprints_own_order_is_otherwise_preserved(self) -> None:
        runner = AgentRunner(agent_type=_CronAgent, agent_config=_SettingsConfig.as_form())

        names = [element.name for element in runner.form]
        assert names == ["agent_id", "name", "description", "icon", "system_prompt", CRON_CONFIG_KEY]
