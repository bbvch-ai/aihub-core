from swiss_ai_hub.core.infrastructure import RclonePipelineSettings, enable_logging

from swiss_ai_hub.pipeline.util.rclone_pipeline_definitions_util import rclone_pipeline_definitions

enable_logging()

defs = rclone_pipeline_definitions(settings=RclonePipelineSettings())
