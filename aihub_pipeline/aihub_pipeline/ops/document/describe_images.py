from dagster import OpExecutionContext, ResourceParam, op

from aihub_pipeline.resources.llm.LanguageModelResource import LanguageModelResource
from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def describe_images(
    context: OpExecutionContext,
    document: RefDocDocument,
    language_model: ResourceParam[LanguageModelResource],
) -> RefDocDocument:
    """Generates descriptions for images that were extracted from the document.
    
    This operation:
    1. Takes a document with extracted images in its metadata
    2. Uses a language model to generate a description for each image
    3. Adds the descriptions to the image metadata
    
    Returns the document with image descriptions added to metadata.
    """
    # Placeholder for image description logic
    # TODO: Implement image description using language model
    # if "extracted_images" in document.metadata:
    #     for image in document.metadata["extracted_images"]:
    #         image["description"] = language_model.get_model().generate_description(image["data"])
    
    context.log.info("Generated descriptions for images in document")
    return document
