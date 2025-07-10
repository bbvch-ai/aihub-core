from types import UnionType
from typing import Annotated, get_origin, get_args, Union

from openai import BaseModel
from pydantic import Field, create_model


class FormkitElement(BaseModel):
    condition_if: Annotated[
        str | None, Field(description="Conditional expression to show this element", alias="if", pattern=r"^\$.+")
    ] = None

    @staticmethod
    def remove_formkit_elements(
        original_model: type[BaseModel],
    ) -> type[BaseModel]:
        """
        Creates a new Pydantic model by removing a specific type from all Union fields.
        """
        new_fields = {}

        for field_name, field_info in original_model.model_fields.items():
            current_annotation = field_info.annotation
            origin = get_origin(current_annotation)

            # Directly check if the core type is a Union
            if origin in (Union, UnionType):
                union_args = get_args(current_annotation)

                # Filter out FormkitElement and its subclasses
                if not any((isinstance(t, type) and issubclass(t, FormkitElement)) for t in union_args):
                    continue

                filtered_args = tuple(
                    t for t in union_args
                    if not (isinstance(t, type) and issubclass(t, FormkitElement))
                )

                if len(filtered_args) == 1:
                    new_annotation = filtered_args[0]
                else:
                    new_annotation = Union[filtered_args]

                # Rebuild the field with the new annotation and original FieldInfo
                new_fields[field_name] = (new_annotation, field_info)

        # Use Pydantic's create_model to build the new class
        new_model_name = f"{original_model.__name__}WithoutForms"
        return create_model(
            new_model_name,
            **new_fields,
        )