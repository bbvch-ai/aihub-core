from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.topic_managers.AbstractStreamTopicManager import AbstractStreamTopicManager
    from swiss_ai_hub.core.topic_managers.agents.AgentClassTopicManager import AgentClassTopicManager
    from swiss_ai_hub.core.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
    from swiss_ai_hub.core.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
    from swiss_ai_hub.core.topic_managers.agents.AgentTopicManager import AgentTopicManager
    from swiss_ai_hub.core.topic_managers.pipeline.PipelineInstanceTopicManager import PipelineInstanceTopicManager
    from swiss_ai_hub.core.topic_managers.pipeline.PipelineTopicManager import PipelineTopicManager
    from swiss_ai_hub.core.topic_managers.process.ProcessClassTopicManager import ProcessClassTopicManager
    from swiss_ai_hub.core.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
    from swiss_ai_hub.core.topic_managers.process.ProcessTopicManager import ProcessTopicManager
    from swiss_ai_hub.core.topic_managers.process.ProcessWalkthroughTopicManager import ProcessWalkthroughTopicManager
    from swiss_ai_hub.core.topic_managers.TopicManager import TopicManager

__all__ = [
    "AbstractStreamTopicManager",
    "AgentClassTopicManager",
    "AgentInstanceTopicManager",
    "AgentThreadTopicManager",
    "AgentTopicManager",
    "PipelineInstanceTopicManager",
    "PipelineTopicManager",
    "ProcessClassTopicManager",
    "ProcessInstanceTopicManager",
    "ProcessTopicManager",
    "ProcessWalkthroughTopicManager",
    "TopicManager",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AbstractStreamTopicManager": "swiss_ai_hub.core.topic_managers.AbstractStreamTopicManager",
    "AgentClassTopicManager": "swiss_ai_hub.core.topic_managers.agents.AgentClassTopicManager",
    "AgentInstanceTopicManager": "swiss_ai_hub.core.topic_managers.agents.AgentInstanceTopicManager",
    "AgentThreadTopicManager": "swiss_ai_hub.core.topic_managers.agents.AgentThreadTopicManager",
    "AgentTopicManager": "swiss_ai_hub.core.topic_managers.agents.AgentTopicManager",
    "PipelineInstanceTopicManager": "swiss_ai_hub.core.topic_managers.pipeline.PipelineInstanceTopicManager",
    "PipelineTopicManager": "swiss_ai_hub.core.topic_managers.pipeline.PipelineTopicManager",
    "ProcessClassTopicManager": "swiss_ai_hub.core.topic_managers.process.ProcessClassTopicManager",
    "ProcessInstanceTopicManager": "swiss_ai_hub.core.topic_managers.process.ProcessInstanceTopicManager",
    "ProcessTopicManager": "swiss_ai_hub.core.topic_managers.process.ProcessTopicManager",
    "ProcessWalkthroughTopicManager": "swiss_ai_hub.core.topic_managers.process.ProcessWalkthroughTopicManager",
    "TopicManager": "swiss_ai_hub.core.topic_managers.TopicManager",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
