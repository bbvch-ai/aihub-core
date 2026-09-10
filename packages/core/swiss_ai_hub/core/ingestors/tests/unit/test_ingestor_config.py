from typing import Annotated, Self

import pytest
from pydantic import Field, ValidationError

from swiss_ai_hub.core.form.config_specs import ConfigSpecs
from swiss_ai_hub.core.form.elements.checkbox import Checkbox
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.ingestors.ingestor_config import IngestorConfig
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor import Ingestor


class _PipelineConfig(IngestorConfig):
    """The shape a pipeline's config takes: identity fields from the base, its own knobs in form duality."""

    embedding_model: Annotated[str | ModelSelect | None, Field(description="Embedding model")] = None
    with_summaries: Annotated[bool | Checkbox, Field(description="Generate summaries")] = True

    @classmethod
    def as_form(cls) -> Self:
        base = IngestorConfig.as_form()
        return cls(
            name=base.name,
            description=base.description,
            embedding_model=ModelSelect(label=LocaleString(en="Embedding"), mode="embedding"),
            with_summaries=Checkbox(label=LocaleString(en="Summaries"), value=True),
        )


class TestAsForm:
    def test_identity_fields_render_first_and_the_pipeline_knobs_follow(self):
        names = [element.name for element in _PipelineConfig.as_form().to_formkit_form()]

        assert names == ["name", "description", "embedding_model", "with_summaries"]

    def test_the_identity_fields_are_required_as_they_are_for_agents(self):
        elements = {element.name: element for element in _PipelineConfig.as_form().to_formkit_form()}

        assert elements["name"].required is True
        assert elements["description"].required is True


class TestSchema:
    def test_the_announced_schema_covers_identity_and_pipeline_knobs(self):
        specs = ConfigSpecs.from_form(_PipelineConfig.as_form(), "_PipelineConfig")

        assert set(specs.config_schema["properties"]) == {"name", "description", "embedding_model", "with_summaries"}
        assert specs.config_class == "_PipelineConfig"

    def test_a_submission_round_trips_into_data_mode(self):
        config = _PipelineConfig.model_validate(
            {"name": {"en": "Contracts"}, "description": {"en": "Signed"}, "embedding_model": "embedding/bge-m3"}
        )

        assert config.embedding_model == "embedding/bge-m3"
        assert config.with_summaries is True

    def test_a_blank_name_is_rejected_in_data_mode(self):
        with pytest.raises(ValidationError, match="name must have"):
            _PipelineConfig.model_validate({"name": {"en": ""}, "description": {"en": "x"}})


class TestIngestorFromConfig:
    def test_both_announced_surfaces_come_from_one_form_mode_config(self):
        ingestor = Ingestor.from_config(
            "acme_rag", LocaleString(en="Acme"), LocaleString(en="Acme's pipeline"), _PipelineConfig.as_form()
        )

        assert [element.name for element in ingestor.form] == [
            "name",
            "description",
            "embedding_model",
            "with_summaries",
        ]
        assert set(ingestor.config_specs.config_schema["properties"]) == set(element.name for element in ingestor.form)
