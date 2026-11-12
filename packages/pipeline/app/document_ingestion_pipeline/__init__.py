from swiss_ai_hub.core.generative_ai import LiteLLMModelInfo
from swiss_ai_hub.core.infrastructure import DocumentIngestionPipelineSettings, enable_logging

from swiss_ai_hub.pipeline.util.document_ingestion_definitions_util import document_ingestion_pipeline_definitions

enable_logging()
# Runs have no caller waiting on them, so a busy LiteLLM should delay a run rather than fail it.
LiteLLMModelInfo.wait_patiently()

defs = document_ingestion_pipeline_definitions(settings=DocumentIngestionPipelineSettings())
