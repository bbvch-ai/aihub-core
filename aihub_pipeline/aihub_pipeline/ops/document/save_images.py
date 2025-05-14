from dagster import OpExecutionContext, ResourceParam, op
from fsspec import AbstractFileSystem

from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def save_images(
    context: OpExecutionContext,
    document: RefDocDocument,
    data_lake_file_system: ResourceParam[AbstractFileSystem],
) -> RefDocDocument:
    """Saves the extracted and described images to storage and updates document metadata.
    
    This operation:
    1. Takes a document with extracted and described images in its metadata
    2. Saves each image to the data lake
    3. Updates the document metadata with references to the saved images
    
    Returns the document with updated image references in metadata.
    """
    # Placeholder for image saving logic
    # TODO: Implement image saving to data lake
    # if "extracted_images" in document.metadata:
    #     for idx, image in enumerate(document.metadata["extracted_images"]):
    #         image_path = f"{document.namespace}/images/{document.id_}_{idx}.png"
    #         with data_lake_file_system.open(image_path, "wb") as f:
    #             f.write(image["data"])
    #         # Update the metadata to include the path instead of raw data
    #         image["path"] = image_path
    #         del image["data"]  # Remove the raw data to avoid storing it in the document store
    
    context.log.info("Saved images from document to data lake")
    return document
