from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging import enable_logging

from aihub_pipeline.util.definitions_util import default_definitions

enable_logging()

settings = AIHubSettings()

defs = default_definitions(
    datalake_container_name=settings.SHARED_KNOWLEDGE_BUCKET,
    embedding_model_name="embedding/large",
    llm_model_name="text-generation/mini",
    with_summary_nodes=True,
    with_table_refinement=True,
    observe_job_hour=2,
    observe_job_minute=0,
    remove_job_hour=3,
    remove_job_minute=0,
)
