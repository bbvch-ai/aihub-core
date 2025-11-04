from aihub_pipeline.util.definitions_util import default_definitions

defs = default_definitions(
    datalake_container_name="playground",
    embedding_model_name="local/qwen-embedding",
    llm_model_name="local/qwen-2.5-multimodal-small",
    with_summary_nodes=True,
    observe_job_hour=2,
    observe_job_minute=0,
    remove_job_hour=3,
    remove_job_minute=0,
)
