import abc
from typing import Annotated, Any, Literal, Self

from openai import BaseModel
from pydantic import ConfigDict, Field

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.form.base.config_authorization_violation import ConfigAuthorizationViolation
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler


class FormkitElement(BaseModel, abc.ABC):
    """
    https://formkit.com/essentials/schema
    Base class for all formkit elements. Instances of these formkit elements will be recognized when placed on
    a Form-model and be converted into data structures that formkit can render in the frontend.
    """

    model_config = ConfigDict(populate_by_name=True)

    is_formkit_element: Annotated[
        Literal[True], Field(description="Indicates that this element is a FormKit element")
    ] = True
    condition_if: Annotated[
        str | None, Field(description="Conditional expression to show this element", alias="if", pattern=r"^\$.+")
    ] = None
    ref: Annotated[str | None, Field(description="Unique identifier for this element", alias="id")] = None
    nullable: Annotated[
        bool,
        Field(description="Render with a sibling toggle that sets this field to null when off"),
    ] = False

    @abc.abstractmethod
    def in_locale(self, t: LocaleHandler) -> Self: ...

    def validate_authorization(
        self, field_path: str, value: Any, access_checker: AccessChecker, t: LocaleHandler
    ) -> list[ConfigAuthorizationViolation]:
        """Validate that the submitted value references only resources the user may access.

        Override in element subclasses that reference access-controlled resources
        (e.g. KnowledgeDatabaseSelector, AgentSelector). The default returns no violations.
        """
        return []
