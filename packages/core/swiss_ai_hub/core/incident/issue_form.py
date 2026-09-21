from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints, create_model

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS
from swiss_ai_hub.core.incident.issue_form_field import IssueFormField
from swiss_ai_hub.core.incident.issue_form_upload import IssueFormUpload


class IssueForm(BaseModel):
    """A parsed issue-form definition, in the shapes the platform needs.

    `elements` goes to the browser and is rendered by the same machinery that
    renders agent configuration. `fields` stays server-side and drives both
    submission validation and the issue body. `upload` is neither: files travel
    as multipart rather than as answers, so the definition's attachment field is
    carried on its own and rendered by the dialog's own picker.
    """

    title_prefix: Annotated[str, Field(description="Prefix the definition puts in front of every issue title")] = ""
    labels: Annotated[list[str], Field(description="Labels every issue created from this form carries")] = []
    elements: Annotated[list[ALL_FORM_OPTIONS], Field(description="Renderable form elements, in definition order")]
    fields: Annotated[list[IssueFormField], Field(description="Answerable questions, in definition order")]
    upload: Annotated[
        IssueFormUpload | None, Field(description="Attachment field, when the definition declares one")
    ] = None

    def field_ids(self) -> set[str]:
        return {field.id for field in self.fields}

    def with_prefill(self, values: dict[str, str]) -> "IssueForm":
        """The same form with known values already in it.

        Applied per request rather than at parse time, because the values differ
        for every reporter and every conversation.
        """
        prefilled = []
        for element in self.elements:
            name = getattr(element, "name", None)
            value = values.get(name) if name else None
            prefilled.append(element.model_copy(update={"value": value}) if value else element)
        return self.model_copy(update={"elements": prefilled})

    def submission_model(self) -> type[BaseModel]:
        """Build the Pydantic model a submission is validated against.

        The same contract agents get from `ConfigSpecs`, reached differently: an
        agent declares its configuration as a Pydantic model and derives a form,
        whereas this form is declared as YAML and derives the model. Dropdowns
        become `Literal`, so a submission naming an option the form does not
        offer is rejected by the schema rather than by a hand-written check.
        """
        definitions: dict[str, Any] = {}
        for field in self.fields:
            annotation = self._annotation_for(field)
            if field.required:
                definitions[field.id] = (annotation, ...)
            else:
                definitions[field.id] = (annotation | None, None)
        return create_model("IncidentSubmission", **definitions)

    @staticmethod
    def _annotation_for(field: IssueFormField) -> Any:
        if field.type == "checkboxes":
            return bool
        if field.type == "dropdown" and field.options:
            # Literal accepts a tuple, which is how a runtime-sized option list gets in.
            option_literal = Literal[tuple(field.options)]  # type: ignore[valid-type]
            return list[option_literal] if field.multiple else option_literal  # type: ignore[valid-type]
        if field.required:
            # GitHub's `required` means "answered", not "present": a key holding "" or whitespace
            # is a skipped question and would otherwise file an issue reading `_No response_`.
            return Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
        return str
