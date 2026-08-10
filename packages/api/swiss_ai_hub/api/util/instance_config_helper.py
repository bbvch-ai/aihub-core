from typing import Any, NamedTuple, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
from swiss_ai_hub.core.form import normalize_empty_locale_strings, normalize_empty_objects_to_none
from swiss_ai_hub.core.i18n import LOCALES, LocaleString
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity


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

    IDENTITY_LOCALE_FIELDS = ("name", "description")

    @staticmethod
    def normalize_form_configuration(config: dict[str, Any]) -> dict[str, Any]:
        """Strip FormKit internal fields (prefixed with '_') and normalize empty values."""
        config = {k: v for k, v in config.items() if not k.startswith("_")}
        config = normalize_empty_objects_to_none(config)
        config = normalize_empty_locale_strings(config)
        return config

    @staticmethod
    def validate_config_for_create(config: dict[str, Any], config_model: type[BaseModel]) -> BaseModel:
        """Validate configuration for instance creation with detailed field-path error messages."""
        try:
            instance = config_model.model_validate(config)
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                error_messages.append(f"{field_path}: {error['msg']}")
            raise HTTPException(status_code=400, detail=f"Configuration validation failed: {'; '.join(error_messages)}")

        InstanceConfigHelper.validate_identity_locale_fields(instance)
        return instance

    @staticmethod
    def validate_config_for_update(config: dict[str, Any], config_model: type[BaseModel]) -> BaseModel:
        """Validate configuration for instance update with simple error passthrough."""
        try:
            instance = config_model.model_validate(config)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Configuration validation failed: {e.errors()}")

        InstanceConfigHelper.validate_identity_locale_fields(instance)
        return instance

    @staticmethod
    def validate_identity_locale_fields(config_instance: BaseModel) -> None:
        """Reject a config whose name or description carries no text in any language.

        `AgentConfig`/`ProcessConfig` already assert this, but neither validator runs here:
        submissions are checked against a model jambo builds from the class's JSON schema,
        which reproduces the schema's shape and none of its Python validators. Since every
        locale field is individually optional, an all-blank name satisfies the generated
        model and gets stored, leaving a record that renders as nothing wherever it is read.
        """
        empty_fields = [
            field
            for field in InstanceConfigHelper.IDENTITY_LOCALE_FIELDS
            if hasattr(config_instance, field)
            and not InstanceConfigHelper._locale_value_has_content(getattr(config_instance, field))
        ]
        if not empty_fields:
            return

        raise HTTPException(
            status_code=400,
            detail=(
                f"Configuration validation failed: {', '.join(empty_fields)} "
                "must have content in at least one language."
            ),
        )

    @staticmethod
    def _locale_value_has_content(value: Any) -> bool:
        """Whether a locale value holds text in at least one language.

        Duck-typed rather than going straight to `LocaleString.has_content()`: on this path
        the value is an instance of the LocaleString class jambo generated from the JSON
        schema, which is a distinct class from the core one.
        """
        if value is None:
            return False
        if isinstance(value, LocaleString):
            return value.has_content()
        if isinstance(value, dict):
            return any((value.get(locale) or "").strip() for locale in LOCALES)
        return any((getattr(value, locale, None) or "").strip() for locale in LOCALES)

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
            LocaleStringEntity.from_locale_string(description)
            if description
            else LocaleStringEntity(de="", en="", fr="", it="")
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
