import math
from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.model_ref_path import ModelRefPath
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ModelBoundInputNumber(InputNumber):
    """
    A number input whose upper bound and default hint come from the model picked elsewhere on the same form.

    A static range cannot be right for every model: an input-token budget a small-context model cannot serve, or
    a temperature hint that is only the default of some other model. The frontend reads the selected model's
    LiteLLM `model_info` and applies `max_from` as the maximum and `default_from` as the placeholder; the API
    rejects a save above the model's limit, since this bound is not part of the announced JSON schema.

    With an `override_label`, a nullable field gets an override checkbox of its own instead of the form's generic
    enable toggle: the input stays in view, disabled and showing the model's default while unset, and is pre-filled
    with that default when the admin starts overriding it, so the default is visible before deciding. A budget
    such as the input tokens has no curated default: unset, it fills `fill_factor` of the model's `max_from` limit,
    which is also the highest value it accepts (`maximum_for`).

    ```python
    number_of_input_tokens=ModelBoundInputNumber(
        label=LocaleString(en="Input tokens"), model_ref="llm.model_name", max_from="max_input_tokens", min=1024
    )
    ```
    """

    formkit: Annotated[Literal["modelBoundNumber"], Field(description="Model-bound number input.")] = (  # type: ignore[assignment]
        "modelBoundNumber"
    )
    model_ref: Annotated[
        str,
        Field(
            description="Dotted path of the model picker, relative to the declaring form; a leading '../' steps up "
            "one form. Rewritten to the path from the form root when the form is rendered. Never prefix it with '$': "
            "FormKit compiles such schema strings as expressions.",
            alias="modelRef",
        ),
    ]
    max_from: Annotated[
        str | None,
        Field(description="The model_info key supplying the maximum, e.g. 'max_input_tokens'.", alias="maxFrom"),
    ] = None
    default_from: Annotated[
        str | None,
        Field(
            description="The model_info key shown as the default the model uses when the field is left empty, "
            "e.g. 'default_temperature'.",
            alias="defaultFrom",
        ),
    ] = None

    fallback_default: Annotated[
        float | None,
        Field(
            description="What applies when the model curates no `default_from` value, shown in its place; unset means "
            "the provider decides and the label says so.",
            alias="fallbackDefault",
        ),
    ] = None
    override_label: Annotated[
        LocaleString | str | None,
        Field(
            description="Label of the element's own override checkbox, followed by the model's default. Set it on a "
            "nullable field whose unset value means 'use the model's default'.",
            alias="overrideLabel",
        ),
    ] = None

    fill_factor: Annotated[
        float | None,
        Field(
            description="The share of the `max_from` limit the runtime actually fills, when it keeps a margin below "
            "it. It is the field's bound, so a value never promises more than a run uses, and without a "
            "`default_from` also what an unset field applies, as a budget left to the model fills its window.",
            alias="fillFactor",
            gt=0,
            le=1,
        ),
    ] = None

    def maximum_for(self, model_limit: float) -> float:
        """The highest value the field accepts for a model whose `max_from` limit is `model_limit`: the share the
        runtime fills, since a value above it would behave exactly like it."""
        return model_limit if self.fill_factor is None else math.floor(model_limit * self.fill_factor)

    def renders_own_unset_state(self) -> bool:
        return self.override_label is not None

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.override_label, LocaleString):
            self_copy.override_label = t.extract(self_copy.override_label)
        return self_copy

    def anchored_at(self, id_prefix: str) -> Self:
        return self.model_copy(update={"model_ref": ModelRefPath.resolve(self.model_ref, id_prefix)})
