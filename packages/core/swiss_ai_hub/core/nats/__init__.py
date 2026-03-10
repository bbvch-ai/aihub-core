from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.nats.dependencies.use_nats import use_nats
    from swiss_ai_hub.core.nats.dispatcher.BaseDispatcher import BaseDispatcher
    from swiss_ai_hub.core.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
    from swiss_ai_hub.core.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor
    from swiss_ai_hub.core.nats.polling.JSPoller import JSPoller
    from swiss_ai_hub.core.nats.publishers.JSPublisher import JSPublisher
    from swiss_ai_hub.core.nats.publishers.NCPublisher import NCPublisher
    from swiss_ai_hub.core.nats.responder.NCResponder import NCResponder
    from swiss_ai_hub.core.nats.rpc.AgentConfigClient import AgentConfigClient
    from swiss_ai_hub.core.nats.rpc.ProcessConfigClient import ProcessConfigClient
    from swiss_ai_hub.core.nats.streams.StreamManager import StreamManager
    from swiss_ai_hub.core.nats.subscribers.agent.AgentJSSubscriber import AgentJSSubscriber
    from swiss_ai_hub.core.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
    from swiss_ai_hub.core.nats.subscribers.JSSubscriber import JSSubscriber
    from swiss_ai_hub.core.nats.subscribers.NCSubscriber import NCSubscriber
    from swiss_ai_hub.core.nats.subscribers.process.ProcessJSSubscriber import ProcessJSSubscriber
    from swiss_ai_hub.core.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
    from swiss_ai_hub.core.nats.topic_managers.agents.AgentClassTopicManager import AgentClassTopicManager
    from swiss_ai_hub.core.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
    from swiss_ai_hub.core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
    from swiss_ai_hub.core.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
    from swiss_ai_hub.core.nats.topic_managers.pipeline.PipelineInstanceTopicManager import (
        PipelineInstanceTopicManager,
    )
    from swiss_ai_hub.core.nats.topic_managers.process.ProcessClassTopicManager import ProcessClassTopicManager
    from swiss_ai_hub.core.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
    from swiss_ai_hub.core.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
    from swiss_ai_hub.core.nats.topic_managers.process.ProcessWalkthroughTopicManager import (
        ProcessWalkthroughTopicManager,
    )
    from swiss_ai_hub.core.nats.workflow.DispatchableWorkflow import DispatchableWorkflow
    from swiss_ai_hub.core.nats.workflow.visualizers.WorkflowVisualizer import WorkflowVisualizer

__all__ = [
    "AgentClassTopicManager",
    "AgentConfigClient",
    "AgentInstanceTopicManager",
    "AgentJSSubscriber",
    "AgentNCSubscriber",
    "AgentThreadTopicManager",
    "AgentTopicManager",
    "BaseDispatcher",
    "DispatchableWorkflow",
    "ExternalAgentEventDistributor",
    "ExternalProcessEventDistributor",
    "JSPoller",
    "JSPublisher",
    "JSSubscriber",
    "NCPublisher",
    "NCResponder",
    "NCSubscriber",
    "PipelineInstanceTopicManager",
    "ProcessClassTopicManager",
    "ProcessConfigClient",
    "ProcessInstanceTopicManager",
    "ProcessJSSubscriber",
    "ProcessNCSubscriber",
    "ProcessTopicManager",
    "ProcessWalkthroughTopicManager",
    "StreamManager",
    "WorkflowVisualizer",
    "use_nats",
]

_LAZY_IMPORTS = {
    "AgentClassTopicManager": "swiss_ai_hub.core.nats.topic_managers.agents.AgentClassTopicManager",
    "AgentConfigClient": "swiss_ai_hub.core.nats.rpc.AgentConfigClient",
    "AgentInstanceTopicManager": "swiss_ai_hub.core.nats.topic_managers.agents.AgentInstanceTopicManager",
    "AgentJSSubscriber": "swiss_ai_hub.core.nats.subscribers.agent.AgentJSSubscriber",
    "AgentNCSubscriber": "swiss_ai_hub.core.nats.subscribers.agent.AgentNCSubscriber",
    "AgentThreadTopicManager": "swiss_ai_hub.core.nats.topic_managers.agents.AgentThreadTopicManager",
    "AgentTopicManager": "swiss_ai_hub.core.nats.topic_managers.agents.AgentTopicManager",
    "BaseDispatcher": "swiss_ai_hub.core.nats.dispatcher.BaseDispatcher",
    "DispatchableWorkflow": "swiss_ai_hub.core.nats.workflow.DispatchableWorkflow",
    "ExternalAgentEventDistributor": "swiss_ai_hub.core.nats.distributor.ExternalAgentEventDistributor",
    "ExternalProcessEventDistributor": "swiss_ai_hub.core.nats.distributor.ExternalProcessEventDistributor",
    "JSPoller": "swiss_ai_hub.core.nats.polling.JSPoller",
    "JSPublisher": "swiss_ai_hub.core.nats.publishers.JSPublisher",
    "JSSubscriber": "swiss_ai_hub.core.nats.subscribers.JSSubscriber",
    "NCPublisher": "swiss_ai_hub.core.nats.publishers.NCPublisher",
    "NCResponder": "swiss_ai_hub.core.nats.responder.NCResponder",
    "NCSubscriber": "swiss_ai_hub.core.nats.subscribers.NCSubscriber",
    "PipelineInstanceTopicManager": "swiss_ai_hub.core.nats.topic_managers.pipeline.PipelineInstanceTopicManager",
    "ProcessClassTopicManager": "swiss_ai_hub.core.nats.topic_managers.process.ProcessClassTopicManager",
    "ProcessConfigClient": "swiss_ai_hub.core.nats.rpc.ProcessConfigClient",
    "ProcessInstanceTopicManager": "swiss_ai_hub.core.nats.topic_managers.process.ProcessInstanceTopicManager",
    "ProcessJSSubscriber": "swiss_ai_hub.core.nats.subscribers.process.ProcessJSSubscriber",
    "ProcessNCSubscriber": "swiss_ai_hub.core.nats.subscribers.process.ProcessNCSubscriber",
    "ProcessTopicManager": "swiss_ai_hub.core.nats.topic_managers.process.ProcessTopicManager",
    "ProcessWalkthroughTopicManager": "swiss_ai_hub.core.nats.topic_managers.process.ProcessWalkthroughTopicManager",
    "StreamManager": "swiss_ai_hub.core.nats.streams.StreamManager",
    "WorkflowVisualizer": "swiss_ai_hub.core.nats.workflow.visualizers.WorkflowVisualizer",
    "use_nats": "swiss_ai_hub.core.nats.dependencies.use_nats",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        return getattr(import_module(_LAZY_IMPORTS[name]), name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
