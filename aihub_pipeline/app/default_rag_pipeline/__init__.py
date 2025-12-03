from aihub_pipeline.util.definitions_util import default_definitions

defs = default_definitions(
    datalake_container_name="defaultknowledge",
    embedding_model_name="embedding/large",
    llm_model_name="text-generation/mini",
    with_summary_nodes=True,
    observe_job_hour=0,
    observe_job_minute=0,
    remove_job_hour=1,
    remove_job_minute=0,
)
