from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field

from aihub_lib.i18n.LocaleString import LocaleString

if TYPE_CHECKING:
    from aihub_lib.persistence.process import ProcessConfigEntity


class ProcessConfig(BaseModel):
    """
    Each process instance can be configured with its own parameters.
    Note that the process config is much less flexible than the agent config.
    Why?

    Well, the agent config is mostly used for runtime configuration, hence, to configure how the
    agent completes its steps. Or, in other words, how it does its work.
    In contrast, processes don't do work. At all. They just connect process entities and do the minimal amount
    of transformation between the work output of one entity and the input of another. Hence, there is little to no
    need for runtime configuration.

    Begs the question: Why can't we use the config to configure stuff like Agent.In or Agent.Out? Would it not be
    cool to have a flexible process with Agent.in(agent_class=config.agent_class, agent_id=config.agent_id)?
    Yes! It would be cool, but it is not possible. The Agent.In and Agent.Out must be statically defined such that
    the process dispatcher and the process entity delegators know a-priori to which agents they must subscribe.
    Hence, you can do funny things like Agent.In(agent_class=config.agent_class, agent_id=config.agent_id),
    but then you must import the process config class into the process entity.
    That is possible and also allowed. It's just not the same flexibility as the agent config, which is dynamically
    injected into each agent step at-runtime.
    """

    name: Annotated[LocaleString, Field(description="The name of the process.")]
    description: Annotated[LocaleString, Field(description="The description of the process.")]
    icon: Annotated[str, Field(description="The icon representing the process.")] = "carbon:ibm-event-processing"

    process_class: Annotated[str, Field(description="The class name of the process, used for identification.")]
    process_id: Annotated[
        str, Field(description="Used to uniquely identify this process instance.", pattern=r"^[a-z0-9_-]+$")
    ]

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, use_enum_values=True, extra="allow")

    @classmethod
    def from_entity(cls, entity: "ProcessConfigEntity") -> "ProcessConfig":
        data = {
            "process_class": entity.process_class,
            "process_id": entity.process_id,
            "name": entity.name.to_locale_string(),
            "description": entity.description.to_locale_string(),
            "icon": entity.icon,
            **entity.config_data,
        }
        config = cls(**data)
        return config
