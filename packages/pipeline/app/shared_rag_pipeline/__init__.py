from swiss_ai_hub.core.infrastructure import AIHubSettings, enable_logging

from swiss_ai_hub.pipeline.util import default_definitions

enable_logging()

defs = default_definitions(
    datalake_container_name=AIHubSettings().SHARED_BUCKET_NAME,
    embedding_model_name="embedding/bge-m3",
    llm_model_name="text-generation/Qwen3-VL-235B-A22B-Instruct",
    with_summary_nodes=True,
    with_table_refinement=True,
    observe_job_hour=2,
    observe_job_minute=0,
    remove_job_hour=3,
    remove_job_minute=0,
)
