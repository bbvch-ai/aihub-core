from aihub_lib.infrastructure.logging import enable_logging

from aihub_pipeline.util.definitions_util import default_definitions

enable_logging()

defs = default_definitions(
    datalake_container_name="defaultknowledge",
    embedding_model_name="embedding/small",
    llm_model_name="text-generation/mini",
    with_summary_nodes=True,
    with_text_refinement=True,
    with_table_refinement=True,
    observe_job_hour=0,
    observe_job_minute=0,
    remove_job_hour=1,
    remove_job_minute=0,
)
