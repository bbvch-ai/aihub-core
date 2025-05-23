from dagster import op

from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo


@op(code_version="v1")
def process_document_without_figures(
    doc_with_figures: DocumentWithFigureInfo,
) -> DocumentWithFigureInfo:
    """Process document when no figures are present or figure extraction was skipped."""
    if "operation_id" in doc_with_figures.metadata:
        del doc_with_figures.metadata["operation_id"]
    if "figure_ids" in doc_with_figures.metadata:
        del doc_with_figures.metadata["figure_ids"]

    return doc_with_figures
