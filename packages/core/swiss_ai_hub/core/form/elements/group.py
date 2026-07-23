from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import Field

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.form.base.config_authorization_violation import ConfigAuthorizationViolation
from swiss_ai_hub.core.form.base.formkit_element import FormkitElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString

if TYPE_CHECKING:
    from swiss_ai_hub.core.form import ALL_FORM_OPTIONS


class Group(FormkitElement):
    """
    https://formkit.com/inputs/group
    Groups child inputs into a nested object structure. The group itself outputs no markup by default
    and can be used to organize related form fields under a common key.

    The group's name becomes the key in the resulting form data object, with all child values nested inside.

    Example:
        group = Group(
            name="llm",
            label="LLM Configuration",
            children=[
                Select(name="model_name", label="Model", options=[...]),
                InputNumber(name="temperature", label="Temperature"),
            ]
        )

        # Results in form data:
        # { "llm": { "model_name": "gpt-4", "temperature": 0.7 } }
    """

    formkit: Annotated[Literal["group"], Field(description="FormKit group element", alias="$formkit")] = "group"
    name: Annotated[str, Field(description="Key name for the grouped data in the form output")]
    label: Annotated[LocaleString | str | None, Field(description="Optional label displayed above the group")] = None
    children: Annotated[list[ALL_FORM_OPTIONS], Field(description="Child form elements contained within this group")]
    access_rule: Annotated[
        str | None,
        Field(
            description="Access rule the user must satisfy to submit this section as enabled",
            alias="accessRule",
        ),
    ] = None
    access_denied_message_path: Annotated[
        str,
        Field(
            description="i18n path for the message shown when access_rule is not satisfied",
            alias="accessDeniedMessagePath",
        ),
    ] = "lib.common.authorization.no_access_section"

    def in_locale(self, t: LocaleHandler) -> Group:
        self_copy = self.model_copy(deep=True)
        if isinstance(self_copy.label, LocaleString):
            self_copy.label = t.extract(self_copy.label)
        # Type ignore: in_locale returns the same concrete type, but base class signature returns FormkitElement
        self_copy.children = [child.in_locale(t) for child in self_copy.children]  # type: ignore[misc]
        return self_copy

    def validate_authorization(
        self,
        field_path: str,
        value: Any,
        access_checker: AccessChecker,
        accessible_tenant_ids: set[str],
        t: LocaleHandler,
    ) -> list[ConfigAuthorizationViolation]:
        """A non-null value means the section was submitted as enabled, so the configuring user
        must hold the rule the section's Form declared via `required_access_rule`."""
        if self.access_rule is None or value is None:
            return []
        if access_checker.has_access(self.access_rule):
            return []
        return [
            ConfigAuthorizationViolation(
                field=field_path,
                resource_type="section",
                resource=self.name,
                message=t(self.access_denied_message_path, section=self.name),
            )
        ]
