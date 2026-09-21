from dagster import OpExecutionContext, op
from swiss_ai_hub.core.generative_ai.utils.path_utils import create_figures_folder_name

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client


@op(code_version="v1")
def delete_figures_for_many_ref_doc(
    context: OpExecutionContext,
    ref_docs: list[RefDocDocument],
) -> list[RefDocDocument]:
    """Deletes figures associated with each RefDocDocument from this run's data lake bucket."""
    data_lake_client = build_s3_data_lake_client(bucket_from_run_tag(context))
    for ref_doc in ref_docs:
        figures_folder = create_figures_folder_name(uri=ref_doc.uri)
        if data_lake_client.directory_exists(directory_path=figures_folder):
            paths = data_lake_client.list_directory_contents(directory_path=figures_folder)
            for path in paths:
                if not path.endswith("/"):
                    file_uri = data_lake_client.build_uri(file_path=path)
                    data_lake_client.delete_file(uri=file_uri)

            data_lake_client.delete_directory(directory_path=figures_folder)
        else:
            context.log.info(f"Figures directory '{figures_folder}' for {ref_doc.uri} not found, skipping deletion.")

    context.log.info(f"All figures were deleted for {len(ref_docs)} documents.")
    return ref_docs
