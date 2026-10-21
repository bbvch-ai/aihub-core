from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.elements.checkbox import Checkbox
from swiss_ai_hub.core.form.elements.model_ref_path import ModelRefPath


class ModelGatedCheckbox(Checkbox):
    """
    A checkbox that can only be switched on while the model picked elsewhere on the same form has a capability.

    The frontend disables it and shows it unchecked while the selected model's LiteLLM `model_info` sets
    `requires` to false; the API rejects a save that enables it for such a model. A model that does not declare
    the capability at all is not held against it, as LiteLLM leaves most flags unset.
    """

    formkit: Annotated[Literal["modelGatedCheckbox"], Field(description="Model-gated checkbox.")] = (  # type: ignore[assignment]
        "modelGatedCheckbox"
    )
    model_ref: Annotated[
        str,
        Field(
            description="Dotted path of the model picker, relative to the declaring form; a leading '../' steps up "
            "one form. Rewritten to the path from the form root when the form is rendered.",
            alias="modelRef",
        ),
    ]
    requires: Annotated[
        str,
        Field(description="The model_info capability flag that must not be false, e.g. 'supports_vision'."),
    ]

    def anchored_at(self, id_prefix: str) -> Self:
        return self.model_copy(update={"model_ref": ModelRefPath.resolve(self.model_ref, id_prefix)})
