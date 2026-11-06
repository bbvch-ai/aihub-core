from typing import Any

from fastapi import HTTPException
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.form import (
    FormkitElement,
    Group,
    ModelBoundInputNumber,
    ModelGatedCheckbox,
    ModelSelect,
    Repeater,
    transform_formkit_arrays,
)
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.api.routes.model.dto.model_dto import ModelInfoDTO
from swiss_ai_hub.api.routes.model.model_service import ModelService

ModelBoundElement = ModelBoundInputNumber | ModelGatedCheckbox | ModelSelect


class ModelLimitValidator:
    """Rejects a save holding a value the model picked on the same form cannot serve, or a picked model the picker
    would not offer.

    The bound depends on another field's value, or on the model's LiteLLM info, so neither the announced JSON schema
    nor an element's own `validate_value` can express it; the frontend applies it as well, but only advisorily. A model
    the listing does not know (one removed from LiteLLM, or one the user may not use) and a limit the model does not
    declare are not held against the save, as the run caps its prompt to the real window anyway. An unreachable
    gateway is different: the listing's error fails the save, so any form holding a model-bound field or a model
    picker cannot be saved while LiteLLM is down.
    """

    @staticmethod
    async def reject_values_beyond_model_limits(
        elements: list[FormkitElement], config: dict[str, Any] | None, user: UserIdentity, t: LocaleHandler
    ) -> None:
        """Raise a 400 naming every field set beyond what its model allows."""
        config = transform_formkit_arrays(config or {})
        bound = ModelLimitValidator.bound_elements(elements, config, "")
        if not bound:
            return

        models = {model.model_name: model.model_info for model in await ModelService.get_model_list(user)}
        invalid = [
            message
            for field_path, element, value in bound
            if (message := ModelLimitValidator._violation(field_path, element, value, config, models, t))
        ]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Configuration validation failed: {'; '.join(invalid)}")

    @staticmethod
    def bound_elements(
        elements: list[FormkitElement], config: dict[str, Any], prefix: str
    ) -> list[tuple[str, ModelBoundElement, Any]]:
        """Every model-bound element holding a submitted value, with its dotted path.

        Inside a Repeater only model pickers are collected, one per entry. A `model_ref` there is anchored without the
        entry's index, so neither the frontend nor this check could tell which entry's model it names; no form puts a
        field bound to another field's model in one.
        """
        found: list[tuple[str, ModelBoundElement, Any]] = []
        for element in elements:
            name = getattr(element, "name", None)
            if not name or name not in config:
                continue
            value = config[name]
            if isinstance(element, Group) and isinstance(value, dict):
                found.extend(ModelLimitValidator.bound_elements(element.children, value, f"{prefix}{name}."))
            elif isinstance(element, Repeater) and isinstance(value, list):
                found.extend(ModelLimitValidator._pickers_in_entries(element, value, f"{prefix}{name}"))
            elif isinstance(element, ModelBoundElement) and value is not None:
                found.append((f"{prefix}{name}", element, value))
        return found

    @staticmethod
    def _pickers_in_entries(
        element: Repeater, entries: list[Any], field_path: str
    ) -> list[tuple[str, ModelBoundElement, Any]]:
        return [
            (entry_path, bound, value)
            for index, entry in enumerate(entries)
            if isinstance(entry, dict)
            for entry_path, bound, value in ModelLimitValidator.bound_elements(
                element.children, entry, f"{field_path}.{index}."
            )
            if isinstance(bound, ModelSelect)
        ]

    @staticmethod
    def _violation(
        field_path: str,
        element: ModelBoundElement,
        value: Any,
        config: dict[str, Any],
        models: dict[str, ModelInfoDTO],
        t: LocaleHandler,
    ) -> str | None:
        if isinstance(element, ModelSelect):
            return ModelLimitValidator._selection_violation(field_path, element, value, models, t)

        model_name = ModelLimitValidator.value_at(config, element.model_ref)
        model_info = models.get(model_name) if isinstance(model_name, str) else None
        if model_info is None:
            return None

        if isinstance(element, ModelGatedCheckbox):
            if value is True and getattr(model_info, element.requires, None) is False:
                return t("api.common.model_limits.capability_missing", field=field_path, model=model_name)
            return None

        model_limit = getattr(model_info, element.max_from, None) if element.max_from else None
        if not isinstance(model_limit, int | float) or not isinstance(value, int | float):
            return None
        maximum = element.maximum_for(model_limit)
        if value > maximum:
            return t("api.common.model_limits.above_maximum", field=field_path, maximum=maximum, model=model_name)
        return None

    @staticmethod
    def _selection_violation(
        field_path: str, element: ModelSelect, model_name: Any, models: dict[str, ModelInfoDTO], t: LocaleHandler
    ) -> str | None:
        """A picked model that is built for one job, or fails the picker's requirements; the picker never offers it."""
        model_info = models.get(model_name) if isinstance(model_name, str) else None
        if model_info is None:
            return None
        if model_info.aihub_general_purpose is False:
            return t("api.common.model_limits.special_purpose", field=field_path, model=model_name)
        unmet = element.requirements.unmet_by(model_info.model_dump())
        if unmet:
            return t(
                "api.common.model_limits.requirements_unmet",
                field=field_path,
                model=model_name,
                requirements=", ".join(t(f"api.common.model_limits.requirements.{name}") for name in unmet),
            )
        return None

    @staticmethod
    def value_at(config: dict[str, Any], dotted_path: str) -> Any:
        value: Any = config
        for segment in dotted_path.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(segment)
        return value
