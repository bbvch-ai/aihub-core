from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging import enable_logging

from aihub_pipeline.util.definitions_util import default_definitions

enable_logging()

defs = default_definitions(
    datalake_container_name=AIHubSettings().DEFAULT_BUCKET_NAME,
    embedding_model_name="embedding/bge-m3",
    llm_model_name="text-generation/Mistral-Small-3.2-24B-Instruct-2506",
    with_summary_nodes=True,
    with_table_refinement=True,
    observe_job_hour=0,
    observe_job_minute=0,
    remove_job_hour=1,
    remove_job_minute=0,
)
