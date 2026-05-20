from swiss_ai_hub.pipeline.util.definitions_util import default_definitions

defs = default_definitions(
    datalake_container_name="playground",
    embedding_model_name="embedding/bge-m3",
    llm_model_name="text-generation/gemma-4-31B-it",
    with_summary_nodes=True,
    observe_job_hour=2,
    observe_job_minute=0,
)
