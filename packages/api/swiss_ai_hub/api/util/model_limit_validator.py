from typing import Any

from fastapi import HTTPException
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.form import (
    FormkitElement,
    Group,
    ModelBoundInputNumber,
    ModelGatedCheckbox,
    transform_formkit_arrays,
)
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.api.routes.model.dto.model_dto import ModelInfoDTO
from swiss_ai_hub.api.routes.model.model_service import ModelService

ModelBoundElement = ModelBoundInputNumber | ModelGatedCheckbox


class ModelLimitValidator:
    """Rejects a save holding a value the model picked on the same form cannot serve.

    The bound depends on another field's value, so neither the announced JSON schema nor an element's own
    `validate_value` can express it; the frontend applies it as well, but only advisorily. A model or limit that
    cannot be established is not held against the save, as the run caps its prompt to the real window anyway.
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
        """Every model-bound element holding a submitted value, with its dotted path. Repeaters are not walked: no
        model-bound field sits in one."""
        found: list[tuple[str, ModelBoundElement, Any]] = []
        for element in elements:
            name = getattr(element, "name", None)
            if not name or name not in config:
                continue
            value = config[name]
            if isinstance(element, Group) and isinstance(value, dict):
                found.extend(ModelLimitValidator.bound_elements(element.children, value, f"{prefix}{name}."))
            elif isinstance(element, ModelBoundElement) and value is not None:
                found.append((f"{prefix}{name}", element, value))
        return found

    @staticmethod
    def _violation(
        field_path: str,
        element: ModelBoundElement,
        value: Any,
        config: dict[str, Any],
        models: dict[str, ModelInfoDTO],
        t: LocaleHandler,
    ) -> str | None:
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
    def value_at(config: dict[str, Any], dotted_path: str) -> Any:
        value: Any = config
        for segment in dotted_path.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(segment)
        return value
