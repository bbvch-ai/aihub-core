from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import StepConfig
from swiss_ai_hub.core.form import Checkbox

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class ConversationMetadataStepConfig(StepConfig):
    """Configuration for the conversation-metadata steps.

    Each flag independently enables generation of one metadata type (title, tags, follow-up
    questions) by the agent so the chat UI never has to derive it from a task model.
    """

    generate_title: Annotated[
        bool | Checkbox,
        Field(description="Whether the agent generates a stable title for the conversation."),
    ] = True
    generate_tags: Annotated[
        bool | Checkbox,
        Field(description="Whether the agent generates category tags for the conversation each turn."),
    ] = True
    suggest_follow_ups: Annotated[
        bool | Checkbox,
        Field(description="Whether the agent suggests follow-up questions after each answer."),
    ] = True

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            generate_title=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.conversation_metadata.config.generate_title.label"),
                help=AgentLocaleString.from_i18n_path("agent.conversation_metadata.config.generate_title.help"),
            ),
            generate_tags=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.conversation_metadata.config.generate_tags.label"),
                help=AgentLocaleString.from_i18n_path("agent.conversation_metadata.config.generate_tags.help"),
            ),
            suggest_follow_ups=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.conversation_metadata.config.suggest_follow_ups.label"),
                help=AgentLocaleString.from_i18n_path("agent.conversation_metadata.config.suggest_follow_ups.help"),
            ),
        )
