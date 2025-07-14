import copy
from types import UnionType
from typing import Union, get_args, get_origin

from openai import BaseModel
from pydantic import create_model

from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class Form(BaseModel):
    """
    This class can be used to transform a pydantic model into a list of formkit elements that can be rendered
    as a full-fledged form in a frontend application.

    The idea is simple: Define a pydantic model with keys and values, where the value types can either be
    primitives or formkit elements. This class then offers convenience functionality to convert the model
    holding both primitive and form elements to a pydantic model that only holds the primitives and can hence be
    used to validate the submitted form.

    It is easiest described by an example:

    ```python
    class MyForm(Form):
        note: Annotated[str | InputTextElement, Field(description="Enter a note")]
        terms: Annotated[bool | InputCheckboxElement, Field(description="Accept the terms")]

    submission_model = MyForm.to_form_submission_model()

    # Results in a pydantic model as follows:
    class MyFormWithoutForms(BaseModel):
        note: Annotated[str, Field(description="Enter a note")]
        terms: Annotated[bool, Field(description="Accept the terms")]

    # Also, create a formkit form from the model:
    my_form = MyForm(note=InputTextField(label="Note"), terms=InputCheckboxField(label="Accept the terms"))
    formkit_elements = my_form.to_formkit_form()
    ```

    # Results in a list of formkit elements that the frontend can render, like
    # [InputTextField(label="Note", name="note"), InputCheckboxField(label="Accept the terms", name="terms")]
    # Submitting that data will result in data like {"note": "My note", "terms": True}
    # Which can then be validated by the submission_model

    ```python
    submission = submission_model(**formkit_data)
    ```
    """

    def to_formkit_form(self) -> list[FormkitElement]:
        """
        Generates a list of FormkitElement objects from the event's attributes.

        This method iterates over the model's fields and identifies attributes
        that are instances of FormkitElement. For elements that are subclasses
        of PrimeVueElement, it automatically assigns the attribute's key as the
        element's 'name'.
        """
        formkit_elements: list[FormkitElement] = []
        # Iterate over the fields of the Pydantic model instance
        for field_name, field_info in self.model_fields.items():
            field_value = getattr(self, field_name)

            # Check if the field's value is an instance of FormkitElement
            if isinstance(field_value, FormkitElement):
                # If it's a PrimeVueElement, it requires a 'name'
                if isinstance(field_value, PrimeVueElement):
                    # Create a copy to avoid mutating the original object
                    element_copy = field_value.model_copy()

                    # Set the name of the element to the field's name
                    element_copy.name = field_name
                    formkit_elements.append(element_copy)
                else:
                    # For other FormkitElements (e.g., HtmlElement), just append them
                    formkit_elements.append(field_value)

        return formkit_elements

    @classmethod
    def to_form_submission_model(
        cls,
    ) -> type[BaseModel]:
        """Creates a new Pydantic model by removing a specific type from all Union fields."""
        new_fields = {}

        for field_name, field_info in cls.model_fields.items():
            current_annotation = field_info.annotation
            origin = get_origin(current_annotation)

            # Directly check if the core type is a Union
            if origin in (Union, UnionType):
                union_args = get_args(current_annotation)

                # Filter out FormkitElement and its subclasses
                if not any((isinstance(t, type) and issubclass(t, FormkitElement)) for t in union_args):
                    continue

                filtered_args = tuple(
                    t for t in union_args if not (isinstance(t, type) and issubclass(t, FormkitElement))
                )

                if len(filtered_args) == 1:
                    new_annotation = filtered_args[0]
                else:
                    new_annotation = Union[filtered_args]  # noqa: UP007

                # Rebuild the field with the new annotation and original FieldInfo
                new_fields[field_name] = (new_annotation, copy.deepcopy(field_info))

        # Use Pydantic's create_model to build the new class
        new_model_name = f"{cls.__name__}WithoutForms"
        return create_model(
            new_model_name,
            **new_fields,
        )
