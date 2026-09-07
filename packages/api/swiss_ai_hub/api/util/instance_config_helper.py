from typing import Any, NamedTuple, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
from swiss_ai_hub.core.agents import CRON_CONFIG_KEY
from swiss_ai_hub.core.form import normalize_empty_locale_strings, normalize_empty_objects_to_none
from swiss_ai_hub.core.i18n import LOCALES, LocaleString
from swiss_ai_hub.core.persistence import AgentInstanceRef
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.scheduling import CronSchedule, ScheduleAdmission


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
    def validate_config_for_create(
        config: dict[str, Any],
        config_model: type[BaseModel],
        agent: AgentInstanceRef | None = None,
    ) -> BaseModel:
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
        InstanceConfigHelper.validate_cron_field(config, agent)
        return instance

    @staticmethod
    def validate_config_for_update(
        config: dict[str, Any],
        config_model: type[BaseModel],
        agent: AgentInstanceRef | None = None,
    ) -> BaseModel:
        """Validate configuration for instance update with simple error passthrough."""
        try:
            instance = config_model.model_validate(config)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Configuration validation failed: {e.errors()}")

        InstanceConfigHelper.validate_identity_locale_fields(instance)
        InstanceConfigHelper.validate_cron_field(config, agent)
        return instance

    @staticmethod
    def validate_cron_field(config: dict[str, Any], agent: AgentInstanceRef | None = None) -> None:
        """Reject a config whose cron schedule is malformed or too costly, before it is stored.

        Same jambo gap as `validate_identity_locale_fields`, with a far wider blast radius. `CronSchedule` rejects a
        bad expression and an unknown timezone in a `model_validator`, which the generated model does not carry: every
        position is a bare string in the JSON schema, so a cleared field arrives as `""` and validates. Stored, it
        then breaks the whole profile rather than only its schedule — `AgentDispatcher` re-validates the real config
        on every control event, so manually triggered runs die too, and they die before any step runs, which means no
        `ExceptionEvent` and nothing in the UI to say why.

        Keyed on the field name because `CRON_CONFIG_KEY` is platform-owned: `cron` lives on the `AgentConfig` base
        and the scheduler reads a profile's schedule from exactly this top-level key, so a blueprint cannot use the
        name for anything else.

        The same call also rejects a schedule that is well-formed but produces more runs than the deployment allows.
        How many a cron expression produces is computable from the expression alone, so the admin who typed it can be
        told now — which is the only moment the answer is useful.
        """
        cron = config.get(CRON_CONFIG_KEY)
        if not isinstance(cron, dict):
            return
        if CronSchedule.is_unscheduled(cron):
            # An all-blank schedule means unscheduled, not invalid — rejecting it would 400 every profile
            # save on a schedulable agent whose owner did not want a schedule. Owned by `CronSchedule`
            # rather than spelled out here because the scheduler has to reach the same verdict on the
            # stored row: this is what it saves, and a second opinion there is an ERROR every tick.
            # It subsumes the empty-dict case too, so there is no separate falsy check above.
            return

        try:
            schedule = CronSchedule.model_validate(cron)
        except ValidationError as e:
            details = "; ".join(InstanceConfigHelper._cron_error_message(error) for error in e.errors())
            raise HTTPException(status_code=400, detail=f"Configuration validation failed: {details}")

        if agent is None:
            # Only the agent save path knows which profile is being written, and only agents carry a
            # schedule at all — `cron` lives on `AgentConfig`. Without an identity the aggregate check
            # would count the profile being edited against itself, so it is skipped rather than guessed.
            return

        rejection = ScheduleAdmission.rejection_reason(schedule, agent.agent_class, agent.agent_id)
        if rejection:
            raise HTTPException(
                status_code=400, detail=f"Configuration validation failed: {CRON_CONFIG_KEY}: {rejection}"
            )

    @staticmethod
    def _cron_error_message(error: Any) -> str:
        """One schedule error, named by the position that caused it.

        A `model_validator` failure carries no field in `loc` — the cron expression is only invalid as a whole — so
        those are reported against the schedule itself rather than as a blank field path.
        """
        field_path = ".".join(str(loc) for loc in error["loc"] if isinstance(loc, str))
        return f"{CRON_CONFIG_KEY}.{field_path}: {error['msg']}" if field_path else f"{CRON_CONFIG_KEY}: {error['msg']}"

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
