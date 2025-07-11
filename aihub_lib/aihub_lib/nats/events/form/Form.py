import copy
from types import UnionType
from typing import Union, get_args, get_origin

from openai import BaseModel
from pydantic import create_model

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form import HtmlElement
from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class Form(BaseModel):
    def to_formkit_form(
        self,
        title: LocaleString | None = None,
        description: LocaleString | None = None,
    ) -> list[FormkitElement]:
        """
        Generates a list of FormkitElement objects from the event's attributes.

        This method iterates over the model's fields and identifies attributes
        that are instances of FormkitElement. For elements that are subclasses
        of PrimeVueElement, it automatically assigns the attribute's key as the
        element's 'name'.
        """
        formkit_elements: list[FormkitElement] = []

        if title is not None:
            formkit_elements.append(
                HtmlElement(el="h1", children=title)
            )

        if description is not None:
            formkit_elements.append(
                HtmlElement(el="p", children=description)
            )

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
        """
        Creates a new Pydantic model by removing a specific type from all Union fields.
        """
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
