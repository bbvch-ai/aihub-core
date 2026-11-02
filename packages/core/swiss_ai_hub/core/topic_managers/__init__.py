from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.topic_managers.abstract_stream_topic_manager import AbstractStreamTopicManager
    from swiss_ai_hub.core.topic_managers.agents.agent_class_topic_manager import AgentClassTopicManager
    from swiss_ai_hub.core.topic_managers.agents.agent_instance_topic_manager import AgentInstanceTopicManager
    from swiss_ai_hub.core.topic_managers.agents.agent_thread_topic_manager import AgentThreadTopicManager
    from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager
    from swiss_ai_hub.core.topic_managers.pipeline.pipeline_instance_topic_manager import PipelineInstanceTopicManager
    from swiss_ai_hub.core.topic_managers.pipeline.pipeline_subject_types import (
        PipelineSourceType,
        PipelineTargetType,
    )
    from swiss_ai_hub.core.topic_managers.pipeline.pipeline_topic_manager import PipelineTopicManager
    from swiss_ai_hub.core.topic_managers.pipeline.pipeline_type_topic_manager import PipelineTypeTopicManager
    from swiss_ai_hub.core.topic_managers.process.process_class_topic_manager import ProcessClassTopicManager
    from swiss_ai_hub.core.topic_managers.process.process_instance_topic_manager import ProcessInstanceTopicManager
    from swiss_ai_hub.core.topic_managers.process.process_topic_manager import ProcessTopicManager
    from swiss_ai_hub.core.topic_managers.process.process_walkthrough_topic_manager import (
        ProcessWalkthroughTopicManager,
    )
    from swiss_ai_hub.core.topic_managers.topic_manager import TopicManager

__all__ = [
    "AbstractStreamTopicManager",
    "AgentClassTopicManager",
    "AgentInstanceTopicManager",
    "AgentThreadTopicManager",
    "AgentTopicManager",
    "PipelineInstanceTopicManager",
    "PipelineSourceType",
    "PipelineTargetType",
    "PipelineTopicManager",
    "PipelineTypeTopicManager",
    "ProcessClassTopicManager",
    "ProcessInstanceTopicManager",
    "ProcessTopicManager",
    "ProcessWalkthroughTopicManager",
    "TopicManager",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AbstractStreamTopicManager": "swiss_ai_hub.core.topic_managers.abstract_stream_topic_manager",
    "AgentClassTopicManager": "swiss_ai_hub.core.topic_managers.agents.agent_class_topic_manager",
    "AgentInstanceTopicManager": "swiss_ai_hub.core.topic_managers.agents.agent_instance_topic_manager",
    "AgentThreadTopicManager": "swiss_ai_hub.core.topic_managers.agents.agent_thread_topic_manager",
    "AgentTopicManager": "swiss_ai_hub.core.topic_managers.agents.agent_topic_manager",
    "PipelineInstanceTopicManager": "swiss_ai_hub.core.topic_managers.pipeline.pipeline_instance_topic_manager",
    "PipelineSourceType": "swiss_ai_hub.core.topic_managers.pipeline.pipeline_subject_types",
    "PipelineTargetType": "swiss_ai_hub.core.topic_managers.pipeline.pipeline_subject_types",
    "PipelineTopicManager": "swiss_ai_hub.core.topic_managers.pipeline.pipeline_topic_manager",
    "PipelineTypeTopicManager": "swiss_ai_hub.core.topic_managers.pipeline.pipeline_type_topic_manager",
    "ProcessClassTopicManager": "swiss_ai_hub.core.topic_managers.process.process_class_topic_manager",
    "ProcessInstanceTopicManager": "swiss_ai_hub.core.topic_managers.process.process_instance_topic_manager",
    "ProcessTopicManager": "swiss_ai_hub.core.topic_managers.process.process_topic_manager",
    "ProcessWalkthroughTopicManager": "swiss_ai_hub.core.topic_managers.process.process_walkthrough_topic_manager",
    "TopicManager": "swiss_ai_hub.core.topic_managers.topic_manager",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
