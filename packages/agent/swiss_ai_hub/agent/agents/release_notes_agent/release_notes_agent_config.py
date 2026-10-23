from typing import Annotated, Any, Self

from pydantic import Field, field_validator
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import Checkbox, ChipsInput, InputNumber, MultiSelect, Select, Textarea
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.jira import JiraConnectionConfig

from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString

_I18N = "agent.release_notes_agent.config"


class ReleaseNotesAgentConfig(ConversationFields, AgentConfig):
    """A Jira connection and its projects, the languages release notes are written in, and who reads them.

    The limits are deployment-fixed and live at the top level, because only top-level fields are fixed by the
    deployment: one set inside the Jira group would be whatever the stored profile says. They are bounded in the
    schema all the same, since a direct API save can set them.
    """

    jira: Annotated[JiraConnectionConfig, Field(title="Jira", description="The Jira the release notes are read from.")]
    project_keys: Annotated[
        list[str] | ChipsInput | None, Field(description="Keys of the Jira projects whose fix versions are read.")
    ] = None
    extra_jql: Annotated[
        str | Textarea, Field(description="JQL every ticket must also match, e.g. to leave out sub-tasks.")
    ] = ""
    language: Annotated[
        ReleaseLanguage | Select, Field(description="The language the release notes are written in.")
    ] = ReleaseLanguage.EN
    # Nullable on purpose: the form requires every field that cannot be None, and translating into nothing is a choice.
    translate_into: Annotated[
        list[ReleaseLanguage] | MultiSelect | None,
        Field(description="Further languages each changelog is translated into."),
    ] = None
    audience: Annotated[
        str | Textarea, Field(description="Who reads the release notes; the notes are written for them.")
    ] = "the customers who use the product"
    show_ticket_keys: Annotated[
        bool | Checkbox, Field(description="Lead each bullet with its ticket key, linked to the ticket.")
    ] = True
    max_release_tickets: Annotated[
        int,
        Field(ge=1, le=1000, description="Deployment-fixed: a release with more tickets is refused, not cut short."),
    ] = 300
    tickets_per_batch: Annotated[
        int, Field(ge=1, le=50, description="Deployment-fixed: tickets, or notes to translate, per model call.")
    ] = 10
    max_concurrent_calls: Annotated[
        int, Field(ge=1, le=16, description="Deployment-fixed: model calls a run makes at once.")
    ] = 4
    max_description_chars: Annotated[
        int, Field(ge=200, le=20_000, description="Deployment-fixed: characters of a description the model reads.")
    ] = 4000
    number_of_input_tokens: Annotated[
        int | InputNumber,
        Field(
            description="Maximum input tokens; low, since earlier changelogs in the chat are long and only the "
            "questions in it matter."
        ),
        Gt(0),
    ] = 16384

    @field_validator("project_keys", mode="before")
    @classmethod
    def _blank_means_none(cls, value: object) -> object:
        """The chips input submits an empty string once its last chip is removed."""
        return None if value == "" else value

    def projects(self) -> list[str]:
        return self.project_keys if isinstance(self.project_keys, list) else []

    def writing_language(self) -> ReleaseLanguage:
        """`AgentConfig` keeps an enum field's value, not the member."""
        return ReleaseLanguage(self.language)

    def translation_targets(self) -> list[ReleaseLanguage]:
        """The writing language picked again among the targets would only be written twice."""
        targets = self.translate_into if isinstance(self.translate_into, list) else []
        languages = [ReleaseLanguage(language) for language in dict.fromkeys(targets)]
        return [language for language in languages if language != self.writing_language()]

    def capped_jira(self) -> JiraConnectionConfig:
        return self.jira.model_copy(update={"max_tickets": self.max_release_tickets})

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            **cls.conversation_form_elements(),
            jira=JiraConnectionConfig.as_form(),
            **cls._release_form_elements(),
        )

    @classmethod
    def _release_form_elements(cls) -> dict[str, Any]:
        languages = [{"label": language.endonym, "value": language.value} for language in ReleaseLanguage]
        return {
            "project_keys": ChipsInput(**cls._labels("project_keys"), placeholder="ENG", required=True),
            "extra_jql": Textarea(**cls._labels("extra_jql"), placeholder="issuetype not in subTaskIssueTypes()"),
            "language": Select(
                **cls._labels("language"), options=languages, option_label="label", option_value="value", required=True
            ),
            "translate_into": MultiSelect(
                **cls._labels("translate_into"), options=languages, option_label="label", option_value="value"
            ),
            "audience": Textarea(**cls._labels("audience")),
            "show_ticket_keys": Checkbox(**cls._labels("show_ticket_keys")),
        }

    @staticmethod
    def _labels(field: str) -> dict[str, AgentLocaleString]:
        return {
            "label": AgentLocaleString.from_i18n_path(f"{_I18N}.{field}.label"),
            "help": AgentLocaleString.from_i18n_path(f"{_I18N}.{field}.help"),
        }
