from unittest.mock import MagicMock, patch

from swiss_ai_hub.pipeline.io.routed_doc_store_io_manager import RoutedDocStoreIOManager
from swiss_ai_hub.pipeline.io.vector_store_io_manager import VectorStoreIOManager
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.id_utils import uri_to_id
from swiss_ai_hub.pipeline.util.partition_utils import make_composite_partition_key

_DOC_MODULE = "swiss_ai_hub.pipeline.io.routed_doc_store_io_manager"
_VEC_MODULE = "swiss_ai_hub.pipeline.io.vector_store_io_manager"


class TestRoutedDocStoreIOManager:
    def test_handle_output_routes_to_store_resolved_from_composite_key(self) -> None:
        store = MagicMock()
        ctx = MagicMock()
        ctx.partition_key = make_composite_partition_key("alpha", "s3://alpha/docs/a.pdf")

        ref_doc = RefDocDocument(text="hello")

        with (
            patch(f"{_DOC_MODULE}.get_db_name_from_bucket_name", side_effect=lambda b: f"db_{b}") as db_name,
            patch(f"{_DOC_MODULE}.build_doc_store", return_value=store) as build,
        ):
            RoutedDocStoreIOManager().handle_output(ctx, ref_doc)

        db_name.assert_called_once_with("alpha")
        build.assert_called_once_with("db_alpha")
        store.add_documents.assert_called_once_with([ref_doc])

    def test_load_input_partitioned_fetches_by_doc_id_from_decoded_uri(self) -> None:
        uri = "s3://alpha/docs/some file.pdf"
        store = MagicMock()
        store.get_document.return_value.to_dict.return_value = {"id_": "x", "text": "t", "metadata": {}}

        ctx = MagicMock()
        ctx.has_partition_key = True
        ctx.partition_key = make_composite_partition_key("alpha", uri)

        with (
            patch(f"{_DOC_MODULE}.get_db_name_from_bucket_name", side_effect=lambda b: f"db_{b}"),
            patch(f"{_DOC_MODULE}.build_doc_store", return_value=store),
        ):
            RoutedDocStoreIOManager().load_input(ctx)

        store.get_document.assert_called_once_with(uri_to_id(uri))

    def test_load_input_non_partitioned_filters_upstream_keys_to_run_bucket(self) -> None:
        store = MagicMock()
        store.get_document.return_value.to_dict.return_value = {"id_": "x", "text": "t", "metadata": {}}

        alpha_uri = "s3://alpha/docs/a.pdf"
        beta_uri = "s3://beta/docs/b.pdf"
        all_keys = [
            make_composite_partition_key("alpha", alpha_uri),
            make_composite_partition_key("beta", beta_uri),
        ]

        ctx = MagicMock()
        ctx.has_partition_key = False
        ctx.step_context.run_tags = {"aihub/bucket": "alpha"}
        ctx.upstream_output.asset_partitions_def.get_partition_keys.return_value = all_keys

        with (
            patch(f"{_DOC_MODULE}.get_db_name_from_bucket_name", side_effect=lambda b: f"db_{b}"),
            patch(f"{_DOC_MODULE}.build_doc_store", return_value=store),
        ):
            RoutedDocStoreIOManager().load_input(ctx)

        # Only the run-bucket's document is loaded; the other bucket's key is ignored.
        store.get_document.assert_called_once_with(uri_to_id(alpha_uri))


class TestVectorStoreIOManager:
    def test_handle_output_routes_nodes_to_collection_resolved_from_composite_key(self) -> None:
        store = MagicMock()
        ctx = MagicMock()
        ctx.partition_key = make_composite_partition_key("gamma", "s3://gamma/docs/c.pdf")
        nodes = [MagicMock(), MagicMock()]

        with (
            patch(f"{_VEC_MODULE}.get_db_name_from_bucket_name", side_effect=lambda b: f"db_{b}") as db_name,
            patch(f"{_VEC_MODULE}.build_vector_store", return_value=store) as build,
            patch(f"{_VEC_MODULE}.mark_ref_docs_as_ingested") as mark_ingested,
            patch(f"{_VEC_MODULE}.embedding_dimension_for_bucket", return_value=1024) as dimension,
        ):
            VectorStoreIOManager().handle_output(ctx, nodes)

        db_name.assert_called_once_with("gamma")
        dimension.assert_called_once_with("gamma")
        build.assert_called_once_with("db_gamma", 1024)
        store.add.assert_called_once_with(nodes)
        mark_ingested.assert_called_once()
        assert mark_ingested.call_args.args[:2] == (nodes, "db_gamma")

    def test_handle_output_marks_documents_ingested_only_after_the_vector_write(self) -> None:
        """A document is queryable only once its nodes are in Milvus, so the flip must follow the write."""
        calls = MagicMock()
        store = MagicMock()
        ctx = MagicMock()
        ctx.partition_key = make_composite_partition_key("gamma", "s3://gamma/docs/c.pdf")

        with (
            patch(f"{_VEC_MODULE}.get_db_name_from_bucket_name", side_effect=lambda b: f"db_{b}"),
            patch(f"{_VEC_MODULE}.build_vector_store", return_value=store),
            patch(f"{_VEC_MODULE}.mark_ref_docs_as_ingested") as mark_ingested,
            patch(f"{_VEC_MODULE}.embedding_dimension_for_bucket", return_value=1024),
        ):
            calls.attach_mock(store.add, "add")
            calls.attach_mock(mark_ingested, "mark_ingested")
            VectorStoreIOManager().handle_output(ctx, [MagicMock()])

        assert [call[0] for call in calls.mock_calls] == ["add", "mark_ingested"]

    def test_handle_output_skips_empty_nodes(self) -> None:
        ctx = MagicMock()
        ctx.partition_key = make_composite_partition_key("gamma", "s3://gamma/docs/c.pdf")

        with patch(f"{_VEC_MODULE}.build_vector_store") as build:
            VectorStoreIOManager().handle_output(ctx, [])

        build.assert_not_called()
