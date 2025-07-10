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

        # Iterate over all fields in the original model
        for field_name, field_info in original_model.model_fields.items():
            current_annotation = field_info.annotation
            origin = get_origin(current_annotation)

            # We are looking for Annotated fields, as in the example
            if origin is Annotated:
                annotated_args = get_args(current_annotation)
                inner_type = annotated_args[0]
                metadata = annotated_args[1:] # Keep the Field, etc.

                inner_origin = get_origin(inner_type)

                # Check if the inner type is a Union
                if inner_origin is Union:
                    union_args = get_args(inner_type)

                    # Filter out the type we want to remove
                    filtered_args = tuple(
                        t for t in union_args
                        if not (isinstance(t, type) and issubclass(t, FormkitElement))
                    )
                    # Reconstruct the inner type
                    if len(filtered_args) == 1:
                        new_inner_type = filtered_args[0]
                    else:
                        # Use the Union type constructor directly
                        new_inner_type = Union[filtered_args]

                    # Rebuild the final annotation with the new inner type and original metadata
                    new_annotation = Annotated[new_inner_type, *metadata]
                    new_fields[field_name] = (new_annotation, field_info)
                else:
                    # Not a Union inside Annotated, so keep it as is
                    new_fields[field_name] = (current_annotation, field_info)
            else:
                # Field is not Annotated, so keep it as is
                new_fields[field_name] = (current_annotation, field_info)

        # Use Pydantic's create_model to build the new class
        new_model_name = f"{original_model.__name__}WithoutForms"

        return create_model(
            new_model_name,
            **new_fields,
            __base__=original_model.__base__
        )