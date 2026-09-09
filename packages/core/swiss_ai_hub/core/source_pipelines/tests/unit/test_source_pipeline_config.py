from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.form.config_specs import ConfigSpecs
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.password import Password
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.source_pipelines.source_pipeline_config import SourcePipelineConfig


class _Credentials(Form):
    user: Annotated[str | InputText, Field(description="User")] = ""
    password: Annotated[str | Password, Field(description="Password")] = ""

    @classmethod
    def as_form(cls) -> Self:
        return cls(user=InputText(label=LocaleString(en="User")), password=Password(label=LocaleString(en="Password")))


class _SyncConfig(SourcePipelineConfig):
    """The shape a source pipeline's config takes: its own knobs only, no identity fields."""

    root_path: Annotated[str | InputText, Field(description="Root path")] = ""
    credentials: Annotated[_Credentials, Field(description="Credentials")] = Field(default_factory=_Credentials)

    @classmethod
    def as_form(cls) -> Self:
        return cls(root_path=InputText(label=LocaleString(en="Root")), credentials=_Credentials.as_form())


class TestAsForm:
    def test_the_base_announces_nothing_and_a_subclass_announces_only_its_own_knobs(self):
        assert SourcePipelineConfig.as_form().to_formkit_form() == []
        assert [element.name for element in _SyncConfig.as_form().to_formkit_form()] == ["root_path", "credentials"]

    def test_the_announced_schema_covers_the_knobs(self):
        specs = ConfigSpecs.from_form(_SyncConfig.as_form(), "_SyncConfig")

        assert set(specs.config_schema["properties"]) == {"root_path", "credentials"}


class TestSecretFieldPaths:
    def test_password_fields_are_derived_from_the_form_with_their_group_prefix(self):
        assert _SyncConfig.secret_field_paths() == {"credentials.password"}
        assert SourcePipelineConfig.secret_field_paths() == set()


class TestDataMode:
    def test_a_stored_configuration_validates_into_typed_values(self):
        config = _SyncConfig.model_validate({"root_path": "/docs", "credentials": {"user": "u", "password": "p"}})

        assert config.root_path == "/docs"
        assert config.credentials.password == "p"
