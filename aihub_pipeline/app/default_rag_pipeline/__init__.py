from aihub_pipeline.util.definitions_util import default_definitions

defs = default_definitions(
    datalake_container_name="playground",
    embedding_model_name="local/qwen-embedding",
    llm_model_name="local/gemma-3-multimodal-small",
    figures_directory_name="__figures__",
    with_summary_nodes=True,
    observe_job_hour=0,
    observe_job_minute=0,
    remove_job_hour=1,
    remove_job_minute=0,
)
