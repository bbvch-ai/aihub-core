import copy
import json
import logging
from types import UnionType
from typing import Any, ClassVar, Union, get_args, get_origin

from pydantic import BaseModel, computed_field, create_model

from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement

logger = logging.getLogger(__name__)


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
        note: Annotated[str | InputText, Field(description="Enter a note")]
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

    _form_registry: ClassVar[dict[str, type["Form"]]] = {}

    @computed_field
    @property
    def _form_name(self) -> str:
        """The form type name, used for polymorphic deserialization."""
        return self.__class__.__name__

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        logger.debug(f"Registering Form {cls.__name__}")
        Form._form_registry[cls.__name__] = cls

    @classmethod
    def deserialize_form(cls, data: bytes | str | dict[str, Any]) -> "Form":
        """Deserialize JSON data into the correct Form subclass based on _form_name."""
        if isinstance(data, dict):
            json_data = data.copy()
        elif isinstance(data, str):
            json_data = json.loads(data)
        elif isinstance(data, bytes):
            json_data = json.loads(data.decode())
        else:
            raise ValueError(f"Cannot deserialize data of type {type(data)}")

        form_name = json_data.get("_form_name")
        if form_name and isinstance(form_name, str):
            form_class = cls._form_registry.get(form_name)
            if form_class:
                return form_class.model_validate(json_data)

        # Fallback to base Form
        logger.warning(f"Form {form_name} not found in registry. Using fallback Form.")
        return Form.model_validate(json_data)

    def to_formkit_form(self) -> list[FormkitElement]:
        """
        Generates a list of FormkitElement objects from the event's attributes.

        This method iterates over the model's fields and identifies attributes
        that are instances of FormkitElement. For elements that are subclasses
        of PrimeVueElement, it automatically assigns the attribute's key as the
        element's 'name' and sets 'required' based on whether the field type
        includes None in its union.
        """
        formkit_elements: list[FormkitElement] = []
        for field_name, field_info in self.model_fields.items():
            field_value = getattr(self, field_name)

            if isinstance(field_value, FormkitElement):
                if isinstance(field_value, PrimeVueElement):
                    element_copy = field_value.model_copy()

                    element_copy.name = field_name
                    element_copy.id = field_name

                    current_annotation = field_info.annotation
                    origin = get_origin(current_annotation)
                    is_required = True

                    if origin in (Union, UnionType):
                        union_args = get_args(current_annotation)
                        if type(None) in union_args:
                            is_required = False

                    element_copy.required = is_required
                    formkit_elements.append(element_copy)
                else:
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

            if origin in (Union, UnionType):
                union_args = get_args(current_annotation)

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
