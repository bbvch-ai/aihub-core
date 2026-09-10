import logging
from typing import TYPE_CHECKING, Annotated, Self

from pydantic import ConfigDict, Field, model_validator

from swiss_ai_hub.core.form.constraints import Pattern
from swiss_ai_hub.core.form.elements.cron_input import CronInput
from swiss_ai_hub.core.form.elements.icon_selector import IconSelector
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.locale_input import LocaleInput
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule

if TYPE_CHECKING:
    from swiss_ai_hub.core.persistence.agents import AgentConfigEntity

logger = logging.getLogger(__name__)

# The config key holding a profile's schedule. Platform-owned: `AgentRunner` writes the form element and
# `CronScheduler` reads the stored value, so neither depends on a blueprint naming the field correctly.
CRON_CONFIG_KEY = "cron"


class StepConfig(Form):
    """
    A base configuration class for workflow steps, allowing future extensions
    to store custom configuration fields relevant to particular steps.

    ### Why StepConfig?
    As workflow steps become more complex, certain steps may require configuration
    parameters - time limits, thresholds, behavior toggles, etc. By deriving from
    StepConfig, each step can define its own configuration model.

    The `AgentConfig` can then hold instances of these step configurations,
    keyed by step type, allowing easy retrieval and management of step-specific settings.

    Supports duality pattern for form rendering and data validation.
    """

    pass


class AgentConfig(Form):
    """
    The agent config is a flexible way to configure the runtime behavior of an agent.

    It can ensure that two agents that follow the same workflow can still be configured
    to achieve different outcomes through a different set of configurations.

    Usually, you will want to inherit from this AgentConfig and pass it to your runner.
    The dispatcher will then flexibly inject the config into each step,
    giving you full control over the agent's runtime behavior.

    Note that you can also define configs for individual workflow steps! Simply by naming
    the attribute the same way as your step, and assigning it a value of type `StepConfig`,
    you can configure the step's behavior.

    Supports duality pattern for form rendering and data validation.

    ```python
    class StepXConfig(StepConfig):
        some_setting: str

    class MyCustomAgentConfig(AgentConfig):
        step_x: StepXConfig = StepXConfig(some_setting="some value")

    class MyAgent(Agent):
        @step()
        def step_x(self, step_x_config: StepXConfig):
            print(step_x_config.some_setting)
    ```
    """

    agent_id: Annotated[
        str | InputText,
        Field(description="Uniquely identifies the agent instance."),
        Pattern(r"^[a-z0-9_-]+$"),
    ]
    name: Annotated[LocaleString | LocaleInput, Field(description="The name of the process or agent.")]
    description: Annotated[
        LocaleString | LocaleInput,
        Field(description="The description of the process or agent."),
    ]
    icon: Annotated[
        str | IconSelector,
        Field(description="The icon representing the process or agent."),
    ] = "mage:robot"
    # Platform-owned, so the scheduler can read a schedule off any profile without the blueprint having
    # to name the field correctly. Deliberately left None by `as_form()`: `AgentRunner` injects the
    # element for schedulable classes only (see `cron_form_field`), which is what keeps a cron control
    # off every other agent's form. The union carries CronSchedule rather than a bare cron string
    # because a string has no timezone, and "every day at 09:00" would then shift twice a year.
    cron: Annotated[
        CronSchedule | CronInput | None,
        Field(description="Cron schedule controlling when this profile runs automatically."),
    ] = None
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, use_enum_values=True, extra="allow")

    @model_validator(mode="after")
    def validate_locale_strings_have_content(self) -> Self:
        """Validate that name and description LocaleStrings have at least one non-empty value."""
        # Skip validation for form mode (when fields are LocaleInput elements)
        if isinstance(self.name, LocaleString) and not self.name.has_content():
            raise ValueError("name must have at least one language with content")
        if isinstance(self.description, LocaleString) and not self.description.has_content():
            raise ValueError("description must have at least one language with content")
        return self

    @classmethod
    def as_form(cls) -> Self:
        """
        Creates a form-mode AgentConfig with FormKit input elements.

        Subclasses should override this method and call super().as_form() to get
        the base identity fields, then extend with their own fields.

        `cron` is deliberately not populated here. A form element is only configurable while its value is
        one, so leaving it None keeps the schedule out of both the rendered form and the generated
        submission schema for every agent — and `AgentRunner` injects `cron_form_field()` for the
        schedulable ones. That is also why subclass overrides need no `cron=` line of their own.
        """
        return cls(
            agent_id=InputText(
                label=LocaleString.from_i18n_path("lib.agents.config.agent_id.label"),
                help=LocaleString.from_i18n_path("lib.agents.config.agent_id.help"),
                placeholder=LocaleString.from_i18n_path("lib.agents.config.agent_id.placeholder"),
                required=True,
            ),
            name=LocaleInput(
                label=LocaleString.from_i18n_path("lib.agents.config.name.label"),
                placeholder=LocaleString.from_i18n_path("lib.agents.config.placeholder.name"),
                input_type="text",
            ),
            description=LocaleInput(
                label=LocaleString.from_i18n_path("lib.agents.config.description.label"),
                placeholder=LocaleString.from_i18n_path("lib.agents.config.placeholder.description"),
                input_type="textarea",
            ),
            icon=IconSelector(
                label=LocaleString.from_i18n_path("lib.agents.config.icon.label"),
                help=LocaleString.from_i18n_path("lib.agents.config.icon.help"),
                placeholder=LocaleString.from_i18n_path("lib.agents.config.placeholder.icon"),
            ),
        )

    @classmethod
    def cron_form_field(cls) -> CronInput:
        """The schedule element, offered to schedulable classes only."""
        return CronInput(
            label=LocaleString.from_i18n_path("lib.agents.config.cron.label"),
            help=LocaleString.from_i18n_path("lib.agents.config.cron.help"),
            timezone_placeholder=LocaleString.from_i18n_path("lib.agents.config.cron.timezone_placeholder"),
        )

    def for_discovery(self, *, is_schedulable: bool) -> Self:
        """This config as discovery should publish it, with the schedule offered only where it applies.

        Whether a field is configurable follows from its *value* being a form element, so setting or
        clearing `cron` here settles both published surfaces at once: the rendered form and the
        submission JSON schema. Clearing rather than leaving it alone is deliberate — a blueprint that
        declared its own `cron` must not be able to offer a schedule it will never be fired on.
        """
        return self.model_copy(update={CRON_CONFIG_KEY: self.cron_form_field() if is_schedulable else None})

    @classmethod
    def from_entity(cls, entity: "AgentConfigEntity") -> Self:
        data = {
            "agent_id": entity.agent_id,
            "name": entity.name.to_locale_string(),
            "description": entity.description.to_locale_string(),
            "icon": entity.icon,
            **entity.config_data,
        }
        config = cls(**data)
        return config

    def get_step_configs(self) -> dict[type[StepConfig], StepConfig]:
        """
        Scans all fields in this AgentConfig and collects any that are `StepConfig` instances.
        """
        step_configs = {}
        for field_name in self.__class__.model_fields.keys():
            field_value = getattr(self, field_name, None)
            if isinstance(field_value, StepConfig):
                step_configs[type(field_value)] = field_value
        return step_configs
