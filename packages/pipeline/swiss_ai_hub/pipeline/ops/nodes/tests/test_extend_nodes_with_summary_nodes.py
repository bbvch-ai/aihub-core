"""Summary generation decides per run whether to work; opting out yields nothing to embed or insert."""

from unittest.mock import Mock, patch

import pytest
from dagster import build_op_context
from llama_index.core.schema import TextNode
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_token_budget import ModelTokenBudget

from swiss_ai_hub.pipeline.ops.nodes.extend_nodes_with_summary_nodes_using_recursive_summary_parser import (
    extend_nodes_with_summary_nodes_using_recursive_summary_parser,
)

_MODULE = "swiss_ai_hub.pipeline.ops.nodes.extend_nodes_with_summary_nodes_using_recursive_summary_parser"
_PARTITION = "contracts|s3:%2F%2Fcontracts%2Fa.pdf"
_DECLARED = {"max_input_tokens": 8192, "aihub_tokenizer": "bge-m3", "aihub_input_overhead_tokens": 2}


def _summarise(summaries: list[TextNode]) -> list[TextNode]:
    content = TextNode(text="a")
    resource = Mock()
    resource.get_summary_parser.return_value.summarize_nodes.return_value = [content, *summaries]
    embedding_config = Mock()
    embedding_config.token_budget.return_value = ModelTokenBudget.for_model("embedding/bge-m3", _DECLARED)
    with (
        patch(f"{_MODULE}.ingestor_config_for_bucket", return_value=Mock(with_summary_nodes=True)),
        patch(f"{_MODULE}.build_language_model", return_value="llm"),
        patch(f"{_MODULE}.llm_config_for_bucket", return_value="llm-config"),
        patch(f"{_MODULE}.embedding_config_for_bucket", return_value=embedding_config),
    ):
        return extend_nodes_with_summary_nodes_using_recursive_summary_parser(
            build_op_context(partition_key=_PARTITION), [content], resource
        )


class TestExtendNodesWithSummaryNodes:
    def test_a_database_that_opted_out_yields_no_nodes_at_all(self):
        """Returning the content nodes instead would embed and upsert them a second time."""
        resource = Mock()
        with patch(f"{_MODULE}.ingestor_config_for_bucket", return_value=Mock(with_summary_nodes=False)):
            result = extend_nodes_with_summary_nodes_using_recursive_summary_parser(
                build_op_context(partition_key=_PARTITION), [TextNode(text="a")], resource
            )

        assert result == []
        resource.get_summary_parser.assert_not_called()

    def test_a_database_that_opted_in_is_summarised_with_its_own_text_model(self):
        resource = Mock()
        resource.get_summary_parser.return_value.summarize_nodes.return_value = [TextNode(text="a"), TextNode(text="s")]
        with (
            patch(f"{_MODULE}.ingestor_config_for_bucket", return_value=Mock(with_summary_nodes=True)),
            patch(f"{_MODULE}.build_language_model", return_value="llm") as build_language_model,
            patch(f"{_MODULE}.llm_config_for_bucket", return_value="llm-config"),
            patch(
                f"{_MODULE}.embedding_config_for_bucket",
                return_value=Mock(token_budget=Mock(return_value=ModelTokenBudget.tiktoken_fallback())),
            ),
        ):
            result = extend_nodes_with_summary_nodes_using_recursive_summary_parser(
                build_op_context(partition_key=_PARTITION), [TextNode(text="a")], resource
            )

        build_language_model.assert_called_once_with("contracts")
        resource.get_summary_parser.assert_called_once_with(llm="llm", llm_config="llm-config")
        assert len(result) == 2

    def test_summaries_within_the_embedding_window_pass(self):
        assert len(_summarise([TextNode(text="A short summary.")])) == 2

    def test_a_summary_over_the_embedding_window_fails_the_run_naming_it(self):
        """A skipped summary would leave its section without one; the run fails instead, saying which."""
        oversized = TextNode(text="Zusammenfassung des Vertrags. " * 3000, metadata={"source": "contract.pdf"})

        with pytest.raises(ValueError, match=rf"{oversized.node_id} of document 'contract\.pdf'"):
            _summarise([oversized])
