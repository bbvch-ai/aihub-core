from typing import Annotated, Any

from pydantic import Field
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.attached_files.attached_files_config import AttachedFilesConfig


class AttachedFilesFields(Form):
    """The attached-files settings a blueprint's config gains by listing this mixin as a base.

    `AttachedFiles` annotates its step with this class. The defaults are models every deployment ships, so profiles
    stored before the mixin existed keep validating.
    """

    attached_files: Annotated[
        AttachedFilesConfig,
        Field(
            description="How the relevant parts of an attached file are picked when the whole file does not fit.",
            title="Attached Files",
        ),
    ] = AttachedFilesConfig()

    @classmethod
    def attached_files_form_elements(cls) -> dict[str, Any]:
        """The form elements for this class's own fields, for a subclass's `as_form()` to spread."""
        return {"attached_files": AttachedFilesConfig.as_form()}
