from swiss_ai_hub.core.infrastructure import enable_logging

from swiss_ai_hub.pipeline.util.rag_definitions_util import rag_pipeline_definitions

enable_logging()

defs = rag_pipeline_definitions(
    embedding_model_name="embedding/bge-m3",
    llm_model_name="text-generation/gemma-4-31B-it",
    with_summary_nodes=True,
    with_table_refinement=True,
    observe_job_hour=0,
    observe_job_minute=0,
)
