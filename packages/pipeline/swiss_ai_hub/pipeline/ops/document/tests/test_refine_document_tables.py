"""Table refinement decides per run whether to work, and with which model."""

from unittest.mock import Mock, patch

from dagster import build_op_context
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

from swiss_ai_hub.pipeline.ops.document.refine_document_tables import refine_document_tables
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument

_MODULE = "swiss_ai_hub.pipeline.ops.document.refine_document_tables"
_PARTITION = "contracts|s3:%2F%2Fcontracts%2Fa.pdf"


def _config(with_table_refinement: bool) -> Mock:
    return Mock(with_table_refinement=with_table_refinement)


def _ref_doc() -> RefDocDocument:
    return RefDocDocument(text="| a | b |", id_="doc", metadata={})


class TestRefineDocumentTables:
    def test_a_database_that_opted_out_gets_its_document_back_untouched(self):
        resource = Mock()
        with patch(f"{_MODULE}.ingestor_config_for_bucket", return_value=_config(False)):
            result = refine_document_tables(build_op_context(partition_key=_PARTITION), _ref_doc(), resource)

        assert result.value.text == "| a | b |"
        resource.refine.assert_not_called()

    def test_a_database_that_opted_in_is_refined_with_its_own_text_model(self):
        """#1818: two databases side by side each refine tables with the model they chose."""
        resource = Mock()
        resource.refine.return_value = RefDocDocument(text="refined", id_="doc", metadata={})
        own_model = LLMConfig(model_name="text-generation/picked")
        with (
            patch(f"{_MODULE}.ingestor_config_for_bucket", return_value=_config(True)),
            patch(f"{_MODULE}.llm_config_for_bucket", return_value=own_model) as llm_config_for_bucket,
        ):
            result = refine_document_tables(build_op_context(partition_key=_PARTITION), _ref_doc(), resource)

        llm_config_for_bucket.assert_called_once_with("contracts")
        resource.refine.assert_called_once()
        assert resource.refine.call_args.args[1] is own_model
        assert result.value.text == "refined"
