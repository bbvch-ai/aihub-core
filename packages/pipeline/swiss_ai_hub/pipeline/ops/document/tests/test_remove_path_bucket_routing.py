from unittest.mock import patch

from dagster import build_op_context
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import SOURCE

from swiss_ai_hub.pipeline.ops.data_lake.fetch_ref_docs_to_remove import fetch_ref_docs_to_remove
from swiss_ai_hub.pipeline.ops.document.delete_figures_for_many_ref_doc import delete_figures_for_many_ref_doc
from swiss_ai_hub.pipeline.ops.document.delete_many_ref_doc_from_docstore import delete_many_ref_doc_from_docstore
from swiss_ai_hub.pipeline.ops.nodes.delete_many_nodes_from_vector_store import delete_many_nodes_from_vector_store
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

BUCKET = "researchdocs"
DB_NAME = "researchdocs_db"

_FIGURES = "swiss_ai_hub.pipeline.ops.document.delete_figures_for_many_ref_doc"
_DOCSTORE = "swiss_ai_hub.pipeline.ops.document.delete_many_ref_doc_from_docstore"
_VECTORS = "swiss_ai_hub.pipeline.ops.nodes.delete_many_nodes_from_vector_store"
_REF_DOCS = "swiss_ai_hub.pipeline.ops.data_lake.fetch_ref_docs_to_remove"


def _context():
    return build_op_context(run_tags={BUCKET_RUN_TAG: BUCKET})


def _ref_doc() -> RefDocDocument:
    return RefDocDocument(id_="doc1", text="body", metadata={SOURCE: f"s3://{BUCKET}/a.pdf"})


class TestRemovePathResolvesItsOwnStores:
    """Each op resolves the run's bucket itself; nothing hands it a pre-built, per-run store."""

    def test_docstore_deletion_targets_the_run_s_database(self):
        with (
            patch(f"{_DOCSTORE}.get_db_name_from_bucket_name", return_value=DB_NAME) as db_name,
            patch(f"{_DOCSTORE}.build_doc_store") as build_doc_store,
        ):
            delete_many_ref_doc_from_docstore(_context(), [_ref_doc()])

        db_name.assert_called_once_with(BUCKET)
        build_doc_store.assert_called_once_with(DB_NAME)
        build_doc_store.return_value.delete_document.assert_called_once_with("doc1", raise_error=True)

    def test_vector_deletion_targets_the_run_s_collection(self):
        with (
            patch(f"{_VECTORS}.get_db_name_from_bucket_name", return_value=DB_NAME),
            patch(f"{_VECTORS}.build_vector_store") as build_vector_store,
        ):
            delete_many_nodes_from_vector_store(_context(), [_ref_doc()])

        build_vector_store.assert_called_once_with(DB_NAME)
        build_vector_store.return_value.delete.assert_called_once_with("doc1")

    def test_figure_deletion_targets_the_run_s_bucket(self):
        with patch(f"{_FIGURES}.build_s3_data_lake_client") as build_client:
            build_client.return_value.directory_exists.return_value = False
            delete_figures_for_many_ref_doc(_context(), [_ref_doc()])

        build_client.assert_called_once_with(BUCKET)

    def test_ref_doc_lookup_targets_the_run_s_database(self):
        with (
            patch(f"{_REF_DOCS}.get_db_name_from_bucket_name", return_value=DB_NAME) as db_name,
            patch(f"{_REF_DOCS}.MongoConnectionRegistry") as registry,
            patch(f"{_REF_DOCS}.RefDoc") as ref_doc,
        ):
            ref_doc.get_documents.return_value = []
            fetch_ref_docs_to_remove(_context(), [])

        db_name.assert_called_once_with(BUCKET)
        registry.ensure_alias.assert_called_once_with(DB_NAME)
        assert ref_doc.get_documents.call_args.kwargs["db_alias"] == DB_NAME

    def test_an_untagged_run_fails_rather_than_deleting_from_the_wrong_database(self):
        """The guard that stops a mis-launched run purging a database it was never meant to touch."""
        with patch(f"{_VECTORS}.build_vector_store") as build_vector_store:
            try:
                delete_many_nodes_from_vector_store(build_op_context(), [_ref_doc()])
            except ValueError as error:
                assert BUCKET_RUN_TAG in str(error)
            else:
                raise AssertionError("expected an untagged run to be rejected")

        build_vector_store.assert_not_called()
