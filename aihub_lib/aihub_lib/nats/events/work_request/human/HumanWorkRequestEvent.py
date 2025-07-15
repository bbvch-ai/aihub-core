from collections import Counter
from typing import Annotated, ClassVar, get_origin

from pydantic import Field, model_validator

from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement
from aihub_lib.nats.events.work.human.HumanWorkEvent import HumanWorkEvent
from aihub_lib.nats.events.work_request.WorkRequestEvent import WorkRequestEvent


class HumanWorkRequestEvent(WorkRequestEvent):
    """
    When requesting work from a human, it is not sufficient to just define which user groups
    must submit the work, we must also give the users forms that they can actually use to submit
    said work.

    Hence, when subclassing a HumanWorkRequestEvent, you usually simply define the work events
    that we expect the user to submit.

    ```python
    class MyHumanWorkRequestEvent(HumanWorkRequestEvent):
        option_a: ClassVar[type[HumanWorkOptionAEvent]] = HumanWorkOptionAEvent
        option_b: ClassVar[type[HumanWorkOptionBEvent]] = HumanWorkOptionBEvent
    ```

    Here, the MyHumanWorkRequestEvent class defines that the user must submit either Option A or Option B.
    Both of which will drive the underlaying agentic process forward. This can be compared to the different
    stop event that an agent can return.
    Think of it this way: An agentic process defines a step in which the human must review the work
    done by agents so far. The human can choose to either accept or reject the work.
    When accepting, the human must submit no data at all, just accept.
    When rejecting, the human must submit a reason why they rejected the work.
    Hence, to continue the process, the human must submit either of the two work events, and the
    process will continue accordingly.

    Now, in the agentic process step, when we request work by a human, we must specify the form that the
    user must fill in in order to submit either of the work events.

    We can do that easily as follows:

    ```python
    @process_step()
    def my_step(self, ...) -> Annotated[MyWorkRequestEvent, Human.Out(...)]:
        return MyWorkRequestEvent(
            forms=[
                MyWorkRequestEvent.option_a(),
                MyWorkRequestEvent.option_b(reason=TextInputField(label="Reason for rejection"))),
            ]
        )
    ```

    Hence, when actually creating the work request, we must provide a form for all the work event options placed
    on the work request event. The validator of the HumanWorkRequestEvent will ensure that the forms provided
    exactly match all work event options placed on the work request event.
    """

    endpoint: Annotated[str | None, Field(description="Endpoint to which this work must be submitted")] = None
    method: Annotated[str | None, Field(description="HTTP Method that must be used to submit this piece of work")] = (
        None
    )
    user_ids: Annotated[list[str], Field(description="The list of user IDs that can submit work.")] = []
    user_emails: Annotated[list[str], Field(description="The list of user E-Mails that can submit work.")] = []
    user_roles: Annotated[list[str], Field(description="The list of roles that can submit work.")] = []
    notify: Annotated[bool, Field(description="Whether to notify the users or not.")] = True

    forms: Annotated[list[HumanWorkEvent], Field(description="The list of forms.")]

    @model_validator(mode="after")
    def validate_forms_and_attributes(self) -> "HumanWorkRequestEvent":
        """Ensures that the forms provided exactly match all work event options placed on the work request event."""
        cls = self.__class__
        forms = self.forms
        all_errors = []

        # Part 1: Validate that custom form attributes are FormkitElements
        # Define the set of fields inherited from the base HumanWorkEvent to ignore.
        base_form_fields = set(HumanWorkEvent.model_fields.keys())

        for i, form in enumerate(forms):
            # Isolate fields specific to the subclass (e.g., in HumanBWork)
            # by removing the base event fields.
            custom_fields = set(form.model_fields.keys()) - base_form_fields

            for field_name in custom_fields:
                field_value = getattr(form, field_name)
                if not isinstance(field_value, FormkitElement):
                    all_errors.append(
                        f"Attribute Error: In form {i} ({type(form).__name__}), "
                        f"field '{field_name}' must be a FormkitElement, "
                        f"but received type '{type(field_value).__name__}'."
                    )

        # Part 2: Validate form types and counts against ClassVars
        expected_types = []
        # Find all ClassVars on this class (e.g., HumanBWorkRequest) that
        # define an expected form type.
        for key in cls.__annotations__:
            if get_origin(getattr(cls, "__annotations__", {}).get(key)) is ClassVar:
                class_var_value = getattr(cls, key, None)
                # Check if the ClassVar's value is a class that inherits from HumanWorkEvent
                if isinstance(class_var_value, type) and issubclass(class_var_value, HumanWorkEvent):
                    expected_types.append(class_var_value)

        # This check only runs if the class has defined expected forms via ClassVars.
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
