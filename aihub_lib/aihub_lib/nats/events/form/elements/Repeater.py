from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement

if TYPE_CHECKING:
    from aihub_lib.nats.events.form import ALL_FORM_OPTIONS


class Repeater(FormkitElement):
    """
    https://formkit.com/inputs/repeater
    Creates a dynamic array of form items with add/remove functionality.

    The repeater allows users to add multiple instances of the same form structure,
    each with its own set of values. The entire section can be collapsible.

    Example:
        repeater = Repeater(
            name="examples",
            label="Few-Shot Examples",
            add_label="Add Example",
            children=[
                InputText(name="user", label="User Input"),
                Checkbox(name="success", label="Success"),
                Textarea(name="reason", label="Reason"),
            ]
        )

        # Results in form data:
        # { "examples": [
        #     { "user": "...", "success": true, "reason": "..." },
        #     { "user": "...", "success": false, "reason": "..." }
        # ] }
    """

    formkit: Annotated[Literal["repeater"], Field(description="FormKit repeater element", alias="$formkit")] = (
        "repeater"
    )
    name: Annotated[str, Field(description="Key name for the array data in the form output")]
    label: Annotated[LocaleString | str | None, Field(description="Label displayed as the section header")] = None
    add_label: Annotated[LocaleString | str | None, Field(description="Text for the add button", alias="addLabel")] = (
        None
    )
    remove_label: Annotated[
        LocaleString | str | None, Field(description="Text for the remove button", alias="removeLabel")
    ] = None
    up_control: Annotated[bool | None, Field(description="Show up/reorder controls", alias="upControl")] = None
    down_control: Annotated[bool | None, Field(description="Show down/reorder controls", alias="downControl")] = None
    insert_control: Annotated[bool | None, Field(description="Show insert controls", alias="insertControl")] = None
    min: Annotated[int | None, Field(description="Minimum number of items")] = None
    max: Annotated[int | None, Field(description="Maximum number of items")] = None
    children: Annotated[list[ALL_FORM_OPTIONS], Field(description="Template form elements for each repeater item")]

    def in_locale(self, t: LocaleHandler) -> Repeater:
        self_copy = self.model_copy(deep=True)
        if isinstance(self_copy.label, LocaleString):
            self_copy.label = t.extract(self_copy.label)
        if isinstance(self_copy.add_label, LocaleString):
            self_copy.add_label = t.extract(self_copy.add_label)
        if isinstance(self_copy.remove_label, LocaleString):
            self_copy.remove_label = t.extract(self_copy.remove_label)
        # Type ignore: in_locale returns the same concrete type, but base class signature returns FormkitElement
        self_copy.children = [child.in_locale(t) for child in self_copy.children]  # type: ignore[misc]
        return self_copy
