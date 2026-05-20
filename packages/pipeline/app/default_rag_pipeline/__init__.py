from swiss_ai_hub.core.infrastructure import AIHubSettings, enable_logging

from swiss_ai_hub.pipeline.util import default_definitions

enable_logging()

defs = default_definitions(
    datalake_container_name=AIHubSettings().DEFAULT_BUCKET_NAME,
    embedding_model_name="embedding/bge-m3",
    llm_model_name="text-generation/gemma-4-31B-it",
    with_summary_nodes=True,
    with_table_refinement=True,
    observe_job_hour=0,
    observe_job_minute=0,
)
