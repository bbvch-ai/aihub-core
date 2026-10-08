from swiss_ai_hub.core.infrastructure import StructuredPipelineSettings, enable_logging

from swiss_ai_hub.pipeline.util.structured_pipeline_definitions_util import structured_pipeline_definitions

enable_logging()

defs = structured_pipeline_definitions(settings=StructuredPipelineSettings())
