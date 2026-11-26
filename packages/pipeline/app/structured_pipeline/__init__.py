from swiss_ai_hub.core.generative_ai import LiteLLMModelInfo
from swiss_ai_hub.core.infrastructure import StructuredPipelineSettings, enable_logging

from swiss_ai_hub.pipeline.util.structured_pipeline_definitions_util import structured_pipeline_definitions

enable_logging()
# Runs have no caller waiting on them, so a busy LiteLLM should delay a run rather than fail it.
LiteLLMModelInfo.wait_patiently()

defs = structured_pipeline_definitions(settings=StructuredPipelineSettings())
