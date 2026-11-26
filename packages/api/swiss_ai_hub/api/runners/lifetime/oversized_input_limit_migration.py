import logging
from typing import Any

from httpx import HTTPError
from swiss_ai_hub.core.form import FormkitElement, ModelBoundInputNumber, transform_formkit_arrays
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.persistence import AgentClassEntity, AgentConfigEntityDocument

from swiss_ai_hub.api.util.model_limit_validator import ModelLimitValidator

logger = logging.getLogger(__name__)


class OversizedInputLimitMigration:
    """Unsets every stored model-bound limit above what its model allows, such as the input tokens.

    The input-token limit used to be pre-filled with 128,000 for every model, and a save is now rejected above the
    model's bound (`ModelBoundInputNumber.maximum_for`: 85% of the window), so a profile on a smaller model (Apertus,
    Ministral, gemma on Infomaniak) could no longer be saved, not even for an unrelated edit. Unset, the limit fills
    that bound, which is what such a profile ran at already: the run caps the limit to it. A limit within the bound may
    be an admin's deliberate cost ceiling and is kept.

    The bound is read from the agent class's announced form, so the margin lives only where the field declares it.
    Only fields with their own unset state are unset. A profile whose class has not been announced, or whose model's
    limit cannot be established (a model missing from LiteLLM, a gateway not reachable yet), is left as it is; the
    migration runs on every start and picks it up once both are known.
    """

    @staticmethod
    async def run() -> list[str]:
        """Unsets every oversized limit; returns which profiles it rewrote."""
        forms: dict[str, list[FormkitElement]] = {}
        model_limits: dict[tuple[str, str], float | None] = {}
        migrated: list[str] = []
        for document in await AgentConfigEntityDocument.list_all():
            if document.agent_class not in forms:
                class_entity = await AgentClassEntity.get_by_agent_class(document.agent_class)
                forms[document.agent_class] = class_entity.form_elements if class_entity else []
            config_data = document.config_data
            rewritten = OversizedInputLimitMigration.rewritten(config_data, forms[document.agent_class], model_limits)
            if rewritten != config_data and await AgentConfigEntityDocument.replace_config_data_if_unchanged(
                document.id, config_data, rewritten
            ):
                migrated.append(f"agent {document.agent_class}/{document.agent_id}")
        return migrated

    @staticmethod
    def rewritten(
        config_data: dict[str, Any],
        elements: list[FormkitElement],
        model_limits: dict[tuple[str, str], float | None],
    ) -> dict[str, Any]:
        """`config_data` with every oversized limit unset; `model_limits` caches the LiteLLM lookups."""
        config = transform_formkit_arrays(config_data)
        rewritten = config_data
        for field_path, element, value in ModelLimitValidator.bound_elements(elements, config, ""):
            if not OversizedInputLimitMigration._can_unset(element) or not isinstance(value, int | float):
                continue
            model_name = ModelLimitValidator.value_at(config, element.model_ref)
            if not isinstance(model_name, str):
                continue
            key = (model_name, element.max_from)
            if key not in model_limits:
                model_limits[key] = OversizedInputLimitMigration._model_limit(model_name, element.max_from)
            model_limit = model_limits[key]
            if model_limit is not None and value > element.maximum_for(model_limit):
                rewritten = OversizedInputLimitMigration._unset(rewritten, field_path.split("."))
        return rewritten

    @staticmethod
    def _can_unset(element: FormkitElement) -> bool:
        """A limit with a model-given bound and its own unset state, which means 'what the model allows'."""
        return (
            isinstance(element, ModelBoundInputNumber) and bool(element.max_from) and element.renders_own_unset_state()
        )

    @staticmethod
    def _model_limit(model_name: str, max_from: str) -> float | None:
        try:
            limit = LLMConfig(model_name=model_name).get_model_info()["model_info"].get(max_from)
        except (ValueError, KeyError, HTTPError) as lookup_failure:
            logger.warning(
                "No %s for %s (%s); its profiles keep their limits until a later start.",
                max_from,
                model_name,
                type(lookup_failure).__name__,
            )
            return None
        return limit if isinstance(limit, int | float) and not isinstance(limit, bool) else None

    @staticmethod
    def _unset(config: dict[str, Any], path: list[str]) -> dict[str, Any]:
        """A copy of `config` with the field at `path` set to None; groups are plain dicts on every path to it."""
        head, *rest = path
        if not rest:
            return config | {head: None}
        return config | {head: OversizedInputLimitMigration._unset(config[head], rest)}
