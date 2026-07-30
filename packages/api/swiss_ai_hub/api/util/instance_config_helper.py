from typing import Any, NamedTuple, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
from swiss_ai_hub.core.form import normalize_empty_locale_strings, normalize_empty_objects_to_none
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

_LOCALE_KEYS = frozenset({"de", "en", "fr", "it"})


class ConfigMetadata(NamedTuple):
    """Metadata extracted from a validated configuration instance."""

    name: Any
    description: Any
    icon: str | None


class LocaleEntities(NamedTuple):
    """Locale-aware name and description entities for a new instance."""

    name: LocaleStringEntity
    description: LocaleStringEntity
    icon: str


T = TypeVar("T")


class InstanceConfigHelper:
    """Pure helper for configuration normalization, validation, and metadata extraction."""

    @staticmethod
    def normalize_form_configuration(config: dict[str, Any]) -> dict[str, Any]:
        """Strip FormKit internal fields (prefixed with '_') and normalize empty values."""
        config = {k: v for k, v in config.items() if not k.startswith("_")}
        config = normalize_empty_objects_to_none(config)
        config = normalize_empty_locale_strings(config)
        return config

    @staticmethod
    def validate_required_locale_fields(config: dict[str, Any], schema: dict[str, Any]) -> None:
        """Reject a create/update whose required localized field carries no populated locale.

        Localized fields (LocaleString: de/en/fr/it) are optional-per-locale, so an all-empty
        value normalizes to None and would either persist a blank record or surface the schema
        model's opaque "not a valid dictionary" error. This raises a clear, field-named 400 for
        every required localized field — name, description, system_prompt, and any future one —
        driven by the schema rather than a hardcoded list.
        """
        required = set(schema.get("required", []))
        empty_fields = sorted(
            field
            for field in required & InstanceConfigHelper._localized_field_names(schema)
            if not InstanceConfigHelper._locale_value_has_content(config.get(field))
        )
        if empty_fields:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The following field(s) require at least one language with content: "
                    f"{', '.join(empty_fields)}."
                ),
            )

    @staticmethod
    def _localized_field_names(schema: dict[str, Any]) -> set[str]:
        """Field names whose schema type resolves to a LocaleString (de/en/fr/it object)."""
        defs = schema.get("$defs", {})
        localized: set[str] = set()
        for field_name, prop in schema.get("properties", {}).items():
            candidates = [prop, *prop.get("allOf", []), *prop.get("anyOf", [])]
            for candidate in candidates:
                ref = candidate.get("$ref") if isinstance(candidate, dict) else None
                target = defs.get(ref.split("/")[-1], {}) if ref else candidate
                properties = target.get("properties") if isinstance(target, dict) else None
                if properties and set(properties).issubset(_LOCALE_KEYS):
                    localized.add(field_name)
                    break
        return localized

    @staticmethod
    def _locale_value_has_content(value: Any) -> bool:
        if isinstance(value, LocaleString):
            return value.has_content()
        if isinstance(value, dict):
            return any(value.get(locale) not in (None, "") for locale in _LOCALE_KEYS)
        return False

    @staticmethod
    def validate_config_for_create(config: dict[str, Any], config_model: type[BaseModel]) -> BaseModel:
        """Validate configuration for instance creation with detailed field-path error messages."""
        try:
            return config_model.model_validate(config)
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                error_messages.append(f"{field_path}: {error['msg']}")
            raise HTTPException(status_code=400, detail=f"Configuration validation failed: {'; '.join(error_messages)}")

    @staticmethod
    def validate_config_for_update(config: dict[str, Any], config_model: type[BaseModel]) -> BaseModel:
        """Validate configuration for instance update with simple error passthrough."""
        try:
            return config_model.model_validate(config)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Configuration validation failed: {e.errors()}")

    @staticmethod
    def extract_config_metadata(config_instance: BaseModel, fallback_icon: str) -> ConfigMetadata:
        """Extract optional name, description, and icon from a validated config instance."""
        name = config_instance.name if hasattr(config_instance, "name") and config_instance.name else None
        description = (
            config_instance.description
            if hasattr(config_instance, "description") and config_instance.description
            else None
        )
        icon = config_instance.icon if hasattr(config_instance, "icon") and config_instance.icon else fallback_icon
        return ConfigMetadata(name=name, description=description, icon=icon)

    @staticmethod
    def build_locale_entities(name: Any, description: Any, class_name: str, icon: str) -> LocaleEntities:
        """Build LocaleStringEntity objects with multilingual defaults for new instances."""
        name_entity = (
            LocaleStringEntity.from_locale_string(name)
            if name
            else LocaleStringEntity(
                de=f"New {class_name}",
                en=f"New {class_name}",
                fr=f"Nouveau {class_name}",
                it=f"Nuovo {class_name}",
            )
        )
        description_entity = (
            LocaleStringEntity.from_locale_string(description) if description else LocaleStringEntity()
        )
        return LocaleEntities(name=name_entity, description=description_entity, icon=icon)

    @staticmethod
    def apply_metadata_to_entity(config_instance: BaseModel, config_entity: T) -> T:
        """Apply name, description, and icon from a validated config to an existing entity."""
        if hasattr(config_instance, "name") and config_instance.name:
            config_entity.name = LocaleStringEntity.from_locale_string(config_instance.name)

        if hasattr(config_instance, "description") and config_instance.description:
            config_entity.description = LocaleStringEntity.from_locale_string(config_instance.description)

        if hasattr(config_instance, "icon") and config_instance.icon:
            config_entity.icon = config_instance.icon

        return config_entity
