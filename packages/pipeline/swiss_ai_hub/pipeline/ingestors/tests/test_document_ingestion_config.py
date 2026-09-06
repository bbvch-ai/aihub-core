from swiss_ai_hub.core.form import Checkbox, ModelSelect
from swiss_ai_hub.core.form.config_specs import ConfigSpecs

from swiss_ai_hub.pipeline.ingestors.document_ingestion_config import DocumentIngestionConfig


def _form() -> DocumentIngestionConfig:
    return DocumentIngestionConfig.as_form(
        llm_model="text-generation/default-llm",
        embedding_model="embedding/default",
        with_summary_nodes=False,
    )


class TestAsForm:
    def test_the_deployment_defaults_pre_fill_the_pickers_and_flags(self):
        elements = {element.name: element for element in _form().to_formkit_form()}

        assert isinstance(elements["llm_model"], ModelSelect)
        assert elements["llm_model"].value == "text-generation/default-llm"
        assert elements["embedding_model"].mode == "embedding"
        assert isinstance(elements["with_summary_nodes"], Checkbox)
        assert elements["with_summary_nodes"].value is False

    def test_the_models_are_required_and_only_the_vision_model_is_an_opt_in_override(self):
        """The collection's dimension derives from the embedding model, so a database cannot exist without one;
        the vision model falls back to the text model, so it is offered behind an enable toggle."""
        elements = {element.name: element for element in _form().to_formkit_form()}

        assert elements["embedding_model"].required is True
        assert elements["llm_model"].required is True
        assert elements["vision_model"].required is False
        assert elements["vision_model"].nullable is True
        assert elements["vision_model"].default_enabled is False

    def test_the_announced_schema_names_every_knob(self):
        properties = ConfigSpecs.from_form(_form(), "DocumentIngestionConfig").config_schema["properties"]

        assert set(properties) == {
            "name",
            "description",
            "llm_model",
            "embedding_model",
            "vision_model",
            "with_summary_nodes",
            "with_table_refinement",
            "with_figure_descriptions",
        }
