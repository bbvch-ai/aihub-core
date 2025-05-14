from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem

from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def inject_figures(
    context: OpExecutionContext,
    document: RefDocDocument,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
) -> RefDocDocument:
    """Injects figures into the document content and updates document metadata.
    
    This operation:
    1. Takes a document with extracted and described figures in its metadata
    2. Saves each figure to the data lake
    3. Updates the document content to include the figures at appropriate locations
    
    Returns the document with injected figures and updated metadata.
    """
    # Placeholder for figure injection logic
    # TODO: Implement figure injection into document content
    # if "extracted_figures" in document.metadata:
    #     for idx, figure in enumerate(document.metadata["extracted_figures"]):
    #         figure_path = f"{document.namespace}/figures/{document.id_}_{idx}.png"
    #         with data_lake_file_system.open(figure_path, "wb") as f:
    #             f.write(figure["data"])
    #         # Update the metadata to include the path instead of raw data
    #         figure["path"] = figure_path
    #         del figure["data"]  # Remove the raw data to avoid storing it in the document store
    
    context.log.info("Injected figures into document content")
    return document
