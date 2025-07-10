from collections import Counter
from typing import Annotated, ClassVar, get_args, get_origin

from pydantic import Field, model_validator

from aihub_lib.nats.events.work.human.HumanWorkEvent import HumanWorkEvent
from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement
from aihub_lib.nats.events.work_request.WorkRequestEvent import WorkRequestEvent


class HumanWorkRequestEvent(WorkRequestEvent):
    """
    WIP
    """

    endpoint: Annotated[str | None, Field(description="Endpoint to which this work must be submitted")] = None
    method: Annotated[str | None, Field(description="HTTP Method that must be used to submit this piece of work")] = (
        None
    )
    users: Annotated[list[str] | None, Field(description="The list of users.")] = None

    forms: Annotated[list[HumanWorkEvent], Field(description="The list of forms.")]

    @model_validator(mode="after")
    def validate_forms_and_attributes(self) -> "HumanWorkRequestEvent":
        cls = self.__class__
        forms = self.forms
        all_errors = []

        # Validate that form attributes are FormkitElements
        base_event_fields = set(HumanWorkEvent.model_fields.keys())
        for i, form in enumerate(forms):
            for field_name, field_value in form:
                if field_name in base_event_fields:
                    continue
                if not isinstance(field_value, FormkitElement):
                    all_errors.append(
                        f"Attribute Error: In form {i} ({type(form).__name__}), "
                        f"field '{field_name}' must be a FormkitElement, "
                        f"but received type '{type(field_value).__name__}'."
                    )

        # Validate form types and counts against ClassVars
        expected_types = []
        for ann in cls.__annotations__.values():
            if get_origin(ann) is ClassVar and get_args(ann):
                type_arg = get_args(ann)[0]
                if get_origin(type_arg) is type and get_args(type_arg):
                    form_class = get_args(type_arg)[0]
                    if issubclass(form_class, HumanWorkEvent):
                        expected_types.append(form_class)

        # This check only runs if the class has defined expected forms.
        if expected_types:
            actual_types = [type(form) for form in forms]
            if Counter(actual_types) != Counter(expected_types):
                expected = sorted([t.__name__ for t in expected_types])
                actual = sorted([t.__name__ for t in actual_types])
                all_errors.append(
                    f"Form List Error: The list of forms is incorrect. Expected: {expected}, Got: {actual}."
                )

        # Raise a single error with all collected messages
        if all_errors:
            raise ValueError("\n".join(all_errors))

        return self
