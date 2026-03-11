from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class TemplateData(BaseModel):
    """Typed container for template data extracted from Form.to_template_data().

    Each agent/process type has different configurable fields, so extra fields
    are allowed and preserved through serialization.
    """

    model_config = ConfigDict(extra="allow")

    name: Annotated[LocaleString, Field(description="Localized display name of the template")]
    description: Annotated[LocaleString, Field(description="Localized description of the template")]
    icon: Annotated[str | None, Field(description="Icon identifier for the template")] = None
