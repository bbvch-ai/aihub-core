from swiss_ai_hub.core.infrastructure import RagPipelineSettings, enable_logging

from swiss_ai_hub.pipeline.util.rag_definitions_util import rag_pipeline_definitions

enable_logging()

settings = RagPipelineSettings()

defs = rag_pipeline_definitions(
    embedding_model_name=settings.EMBEDDING_MODEL,
    llm_model_name=settings.LLM_MODEL,
    with_summary_nodes=settings.WITH_SUMMARY_NODES,
    with_table_refinement=settings.WITH_TABLE_REFINEMENT,
    with_figure_descriptions=settings.WITH_FIGURE_DESCRIPTIONS,
    observe_job_hour=settings.OBSERVE_JOB_HOUR,
    observe_job_minute=settings.OBSERVE_JOB_MINUTE,
)
