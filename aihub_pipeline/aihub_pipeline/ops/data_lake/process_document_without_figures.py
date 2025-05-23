from dagster import In, Nothing, op, Out

from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo


@op(
    code_version="v1",
    ins={
        "doc_with_figures": In(DocumentWithFigureInfo),
        "figures_extracted": In(Nothing),
    },
    out=Out(DocumentWithFigureInfo),
)
def process_document_without_figures(
    doc_with_figures: DocumentWithFigureInfo,
) -> DocumentWithFigureInfo:
    """Process document when no figures are present or figure extraction was skipped"""
    # Just return the original document, but clean up any figure-related metadata
    if "operation_id" in doc_with_figures.metadata:
        del doc_with_figures.metadata["operation_id"]
    if "figure_ids" in doc_with_figures.metadata:
        del doc_with_figures.metadata["figure_ids"]

    return doc_with_figures
