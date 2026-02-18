from pydantic import BaseModel, ConfigDict

from aihub_lib.i18n.LocaleString import LocaleString


class TemplateData(BaseModel):
    """Typed container for template data extracted from Form.to_template_data().

    Each agent/process type has different configurable fields, so extra fields
    are allowed and preserved through serialization.
    """

    model_config = ConfigDict(extra="allow")

    name: LocaleString
    description: LocaleString
    icon: str | None = None
