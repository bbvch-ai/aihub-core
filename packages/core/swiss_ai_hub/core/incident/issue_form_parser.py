from pathlib import Path
from typing import Annotated, Any

import yaml

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS
from swiss_ai_hub.core.form.base.html_element import HtmlElement
from swiss_ai_hub.core.form.elements.checkbox import Checkbox
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.multi_select import MultiSelect
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.form.elements.textarea import Textarea
from swiss_ai_hub.core.incident.issue_form import IssueForm
from swiss_ai_hub.core.incident.issue_form_field import IssueFormField

DEFAULT_FORM_PATH = Path(__file__).parent / "incident_form.yml"

ANSWERABLE_TYPES = {"input", "textarea", "dropdown", "checkboxes"}
TEXTAREA_ROWS = 4


class IssueFormParser:
    """Turns a GitHub issue-form definition into the platform's own form primitives.

    Deliberately not a `Form` subclass: everywhere else a form starts as a Pydantic
    model and produces elements, but the whole point here is that the form is data
    a non-programmer edits. So this builds the same elements from the far side, and
    everything downstream — the FormKit renderer, the JSON-Schema submission
    contract — is reached unchanged.
    """

    @classmethod
    def load(cls, path: Annotated[Path, "Definition to read"] = DEFAULT_FORM_PATH) -> IssueForm:
        return cls.parse(path.read_text(encoding="utf-8"))

    @classmethod
    def parse(cls, definition: Annotated[str, "Issue-form YAML"]) -> IssueForm:
        document = yaml.safe_load(definition)
        if not isinstance(document, dict) or not isinstance(document.get("body"), list):
            raise ValueError("Issue form definition must be a mapping with a 'body' list")

        elements: list[ALL_FORM_OPTIONS] = []
        fields: list[IssueFormField] = []
        for position, entry in enumerate(document["body"]):
            element, field = cls._parse_entry(entry, position)
            elements.append(element)
            if field:
                fields.append(field)

        cls._reject_duplicate_ids(fields)
        return IssueForm(
            title_prefix=document.get("title", "") or "",
            labels=list(document.get("labels", []) or []),
            elements=elements,
            fields=fields,
        )

    @classmethod
    def _parse_entry(
        cls,
        entry: Annotated[Any, "One body entry"],
        position: Annotated[int, "Index in the body list, used only for error messages"],
    ) -> tuple[ALL_FORM_OPTIONS, IssueFormField | None]:
        if not isinstance(entry, dict):
            raise ValueError(f"Body entry {position} must be a mapping")

        entry_type = entry.get("type")
        attributes = entry.get("attributes") or {}

        if entry_type == "markdown":
            return cls._prose(attributes, position), None

        if entry_type not in ANSWERABLE_TYPES:
            # Loud here rather than silent, so a mistyped definition breaks the build
            # and never reaches a user who is already annoyed enough to report a bug.
            raise ValueError(f"Body entry {position} has unsupported type {entry_type!r}")

        field = cls._field(entry, entry_type, attributes, position)
        return cls._element(field, attributes), field

    @staticmethod
    def _prose(
        attributes: Annotated[dict, "markdown attributes"],
        position: Annotated[int, "Index in the body list"],
    ) -> ALL_FORM_OPTIONS:
        value = attributes.get("value")
        if not value:
            raise ValueError(f"Body entry {position} is markdown without a value")
        return HtmlElement(**{"$el": "p", "children": str(value).strip()})

    @staticmethod
    def _field(
        entry: Annotated[dict, "One body entry"],
        entry_type: Annotated[str, "Entry type"],
        attributes: Annotated[dict, "Entry attributes"],
        position: Annotated[int, "Index in the body list"],
    ) -> IssueFormField:
        identifier = entry.get("id")
        if not identifier:
            raise ValueError(f"Body entry {position} of type {entry_type!r} needs an id")
        label = attributes.get("label")
        if not label:
            raise ValueError(f"Body entry {position} ({identifier}) needs a label")

        options = [str(option) for option in attributes.get("options", []) or []]
        if entry_type == "dropdown" and not options:
            raise ValueError(f"Dropdown {identifier} has no options")

        return IssueFormField(
            id=str(identifier),
            label=str(label),
            type=entry_type,
            required=bool((entry.get("validations") or {}).get("required", False)),
            options=options,
            multiple=bool(attributes.get("multiple", False)),
            render=attributes.get("render"),
        )

    @staticmethod
    def _element(
        field: Annotated[IssueFormField, "Parsed question"],
        attributes: Annotated[dict, "Entry attributes"],
        # `description` and `placeholder` are both prose under the label in GitHub's
        # renderer; the platform keeps them apart, so description becomes help text.
    ) -> ALL_FORM_OPTIONS:
        common = {
            "name": field.id,
            "label": field.label,
            "help": attributes.get("description"),
            "required": field.required,
        }
        placeholder = attributes.get("placeholder")

        match field.type:
            case "textarea":
                return Textarea(**common, placeholder=placeholder, rows=TEXTAREA_ROWS, autoResize=True)
            case "dropdown" if field.multiple:
                # MultiSelect takes option objects where Select takes plain strings,
                # so the same YAML list has to be reshaped for it.
                return MultiSelect(
                    **common,
                    options=[{"label": option, "value": option} for option in field.options],
                    optionLabel="label",
                    optionValue="value",
                    placeholder=placeholder,
                )
            case "dropdown":
                return Select(**common, options=field.options, placeholder=placeholder)
            case "checkboxes":
                return Checkbox(**common)
            case _:
                return InputText(**common, placeholder=placeholder)

    @staticmethod
    def _reject_duplicate_ids(fields: Annotated[list[IssueFormField], "Parsed questions"]) -> None:
        seen: set[str] = set()
        for field in fields:
            if field.id in seen:
                raise ValueError(f"Duplicate question id {field.id!r}")
            seen.add(field.id)
