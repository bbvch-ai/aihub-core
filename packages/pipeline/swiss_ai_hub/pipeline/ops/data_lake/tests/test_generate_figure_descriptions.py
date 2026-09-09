"""Figure descriptions decide per run whether to work, and with which model."""

from unittest.mock import Mock, patch

from dagster import build_op_context

from swiss_ai_hub.pipeline.ops.data_lake.generate_figure_descriptions import generate_figure_descriptions
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument

_MODULE = "swiss_ai_hub.pipeline.ops.data_lake.generate_figure_descriptions"
_PARTITION = "contracts|s3:%2F%2Fcontracts%2Fa.pdf"


class TestGenerateFigureDescriptions:
    def test_a_database_that_opted_out_gets_its_document_back_without_a_model_call(self):
        ref_doc = RefDocDocument(text="<figure>![](s3://contracts/fig.png)</figure>", id_="doc", metadata={})
        with (
            patch(f"{_MODULE}.ingestor_config_for_bucket", return_value=Mock(with_figure_descriptions=False)),
            patch(f"{_MODULE}.build_vision_model") as build_vision_model,
        ):
            result = generate_figure_descriptions(
                build_op_context(partition_key=_PARTITION, resources={"data_lake_file_system": Mock()}),
                ref_doc,
            )

        build_vision_model.assert_not_called()
        assert result is ref_doc

    def test_a_database_that_opted_in_describes_with_its_vision_model(self):
        """#1819: the vision model is resolved per database, falling back to its text model inside the resolver."""
        ref_doc = RefDocDocument(text="no figures here", id_="doc", metadata={})
        with (
            patch(f"{_MODULE}.ingestor_config_for_bucket", return_value=Mock(with_figure_descriptions=True)),
            patch(f"{_MODULE}.build_vision_model") as build_vision_model,
        ):
            generate_figure_descriptions(
                build_op_context(partition_key=_PARTITION, resources={"data_lake_file_system": Mock()}),
                ref_doc,
            )

        build_vision_model.assert_called_once_with("contracts")
