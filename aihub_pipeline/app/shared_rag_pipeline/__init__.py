from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging import enable_logging

from aihub_pipeline.util.definitions_util import default_definitions

enable_logging()
print(AIHubSettings().startup_banner)

defs = default_definitions(
    datalake_container_name=AIHubSettings().SHARED_BUCKET_NAME,
    embedding_model_name="embedding/bge-m3",
    llm_model_name="text-generation/gpt-oss-120b",
    with_summary_nodes=True,
    with_table_refinement=True,
    observe_job_hour=2,
    observe_job_minute=0,
    remove_job_hour=3,
    remove_job_minute=0,
)
