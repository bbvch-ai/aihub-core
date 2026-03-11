from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.events.agent.aitl.AgentInTheLoop import AgentInTheLoop
    from swiss_ai_hub.core.events.agent.aitl.exception.AgentInTheLoopExceptionEvent import AgentInTheLoopExceptionEvent
    from swiss_ai_hub.core.events.agent.aitl.request.AgentInTheLoopRequestEvent import AgentInTheLoopRequestEvent
    from swiss_ai_hub.core.events.agent.aitl.response.AgentInTheLoopResponseEvent import AgentInTheLoopResponseEvent
    from swiss_ai_hub.core.events.agent.bitl.BotInTheLoop import BotInTheLoop
    from swiss_ai_hub.core.events.agent.bitl.request.BotInTheLoopRequestEvent import (
        BotInTheLoopRequestEvent,
        SlackConfig,
        TeamsConfig,
    )
    from swiss_ai_hub.core.events.agent.bitl.response.BotInTheLoopResponseEvent import (
        BotInTheLoopResponderInfo,
        BotInTheLoopResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.common.LanguageEvent import LanguageEvent
    from swiss_ai_hub.core.events.agent.common.LimitChatHistoryEvent import LimitChatHistoryEvent
    from swiss_ai_hub.core.events.agent.common.StandaloneQuestionCondenserEvent import StandaloneQuestionCondenserEvent
    from swiss_ai_hub.core.events.agent.control.ControlEvent import ControlEvent
    from swiss_ai_hub.core.events.agent.control.exception.ExceptionEvent import ExceptionEvent
    from swiss_ai_hub.core.events.agent.control.start.StartEvent import StartEvent
    from swiss_ai_hub.core.events.agent.control.stop.StopEvent import StopEvent
    from swiss_ai_hub.core.events.agent.ControlAndDisplayEvent import ControlAndDisplayEvent
    from swiss_ai_hub.core.events.agent.cost.CostEvent import CostEvent
    from swiss_ai_hub.core.events.agent.cost.LLMCostEvent import LLMCostEvent
    from swiss_ai_hub.core.events.agent.discovery.AgentClassDiscoveryResponseEvent import (
        AgentClassDiscoveryResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.discovery.AgentConfigSpecs import AgentConfigSpecs
    from swiss_ai_hub.core.events.agent.discovery.AgentConfigSpecsEntity import AgentConfigSpecsEntity
    from swiss_ai_hub.core.events.agent.display.ChunkEvent import ChunkEvent
    from swiss_ai_hub.core.events.agent.display.DisplayEvent import DisplayEvent
    from swiss_ai_hub.core.events.agent.display.ThoughtEvent import ThoughtEvent
    from swiss_ai_hub.core.events.agent.guard.AgentSuitabilityAcceptEvent import AgentSuitabilityAcceptEvent
    from swiss_ai_hub.core.events.agent.guard.AgentSuitabilityRejectEvent import AgentSuitabilityRejectEvent
    from swiss_ai_hub.core.events.agent.guard.ContextInsufficientRejectEvent import ContextInsufficientRejectEvent
    from swiss_ai_hub.core.events.agent.guard.ContextSufficientAcceptEvent import ContextSufficientAcceptEvent
    from swiss_ai_hub.core.events.agent.guard.ExpertRejectEvent import ExpertRejectEvent
    from swiss_ai_hub.core.events.agent.guard.FewShotAcceptEvent import FewShotAcceptEvent
    from swiss_ai_hub.core.events.agent.guard.FewShotRejectEvent import FewShotRejectEvent
    from swiss_ai_hub.core.events.agent.guard.GuardAcceptEvent import GuardAcceptEvent
    from swiss_ai_hub.core.events.agent.guard.GuardRejectionEvent import GuardRejectionEvent
    from swiss_ai_hub.core.events.agent.guard.SensitiveInfoAcceptEvent import SensitiveInfoAcceptEvent
    from swiss_ai_hub.core.events.agent.guard.SensitiveInfoRejectEvent import SensitiveInfoRejectEvent
    from swiss_ai_hub.core.events.agent.hitl.HumanInTheLoop import HumanInTheLoop
    from swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopChat import HumanInTheLoopChat
    from swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopConfirmation import HumanInTheLoopConfirmation
    from swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopInput import HumanInTheLoopInput
    from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopChatRequestEvent import (
        HumanInTheLoopChatRequestEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopConfirmationRequestEvent import (
        HumanInTheLoopConfirmationRequestEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopInputRequestEvent import (
        HumanInTheLoopInputRequestEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopRequestEvent import HumanInTheLoopRequestEvent
    from swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopChatResponseEvent import (
        HumanInTheLoopChatResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopConfirmationResponseEvent import (
        HumanInTheLoopConfirmationResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopInputResponseEvent import (
        HumanInTheLoopInputResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopResponseEvent import HumanInTheLoopResponseEvent
    from swiss_ai_hub.core.events.agent.memory.history.AddMemoryToChatHistoryEvent import AddMemoryToChatHistoryEvent
    from swiss_ai_hub.core.events.agent.memory.history.AddOrganizationMemoryToChatHistoryEvent import (
        AddOrganizationMemoryToChatHistoryEvent,
    )
    from swiss_ai_hub.core.events.agent.memory.history.AddUserMemoryToChatHistoryEvent import (
        AddUserMemoryToChatHistoryEvent,
    )
    from swiss_ai_hub.core.events.agent.memory.retrieve.BaseRetrieveMemoryEvent import BaseRetrieveMemoryEvent
    from swiss_ai_hub.core.events.agent.memory.retrieve.RetrieveOrganizationMemoryEvent import (
        RetrieveOrganizationMemoryEvent,
    )
    from swiss_ai_hub.core.events.agent.memory.retrieve.RetrieveUserMemoryEvent import RetrieveUserMemoryEvent
    from swiss_ai_hub.core.events.agent.memory.store.BaseStoreMemoryEvent import BaseStoreMemoryEvent
    from swiss_ai_hub.core.events.agent.memory.store.StoreOrganizationMemoryEvent import StoreOrganizationMemoryEvent
    from swiss_ai_hub.core.events.agent.memory.store.StoreUserMemoryEvent import StoreUserMemoryEvent
    from swiss_ai_hub.core.events.agent.router.RouteOptions import RouteOptions
    from swiss_ai_hub.core.events.agent.router.RouterEvent import RouterEvent
    from swiss_ai_hub.core.events.agent.semantic.agent.AgentEvent import AgentEvent
    from swiss_ai_hub.core.events.agent.semantic.chain.ChainEvent import ChainEvent
    from swiss_ai_hub.core.events.agent.semantic.embedding.Embedding import Embedding
    from swiss_ai_hub.core.events.agent.semantic.embedding.EmbeddingEvent import EmbeddingEvent
    from swiss_ai_hub.core.events.agent.semantic.guard.GuardEvent import GuardEvent
    from swiss_ai_hub.core.events.agent.semantic.llm.LLMEvent import LLMEvent
    from swiss_ai_hub.core.events.agent.semantic.llm.LLMStopEvent import LLMStopEvent
    from swiss_ai_hub.core.events.agent.semantic.llm.Message import AudioContent, ImageContent, Message, TextContent
    from swiss_ai_hub.core.events.agent.semantic.reranker.RerankerEvent import RerankerEvent
    from swiss_ai_hub.core.events.agent.semantic.retriever.RetrieverEvent import RetrieverEvent
    from swiss_ai_hub.core.events.agent.semantic.SemanticEvent import SemanticEvent
    from swiss_ai_hub.core.events.agent.semantic.tool.ToolEvent import ToolEvent
    from swiss_ai_hub.core.events.agent.user.UserMessageEvent import UserMessageEvent
    from swiss_ai_hub.core.events.agent.user.UserUploadedFile import UserUploadedFile

__all__ = [
    "AddMemoryToChatHistoryEvent",
    "AddOrganizationMemoryToChatHistoryEvent",
    "AddUserMemoryToChatHistoryEvent",
    "AgentClassDiscoveryResponseEvent",
    "AgentConfigSpecs",
    "AgentConfigSpecsEntity",
    "AgentEvent",
    "AgentInTheLoop",
    "AgentInTheLoopExceptionEvent",
    "AgentInTheLoopRequestEvent",
    "AgentInTheLoopResponseEvent",
    "AgentSuitabilityAcceptEvent",
    "AgentSuitabilityRejectEvent",
    "AudioContent",
    "BaseRetrieveMemoryEvent",
    "BaseStoreMemoryEvent",
    "BotInTheLoop",
    "BotInTheLoopRequestEvent",
    "BotInTheLoopResponderInfo",
    "BotInTheLoopResponseEvent",
    "ChainEvent",
    "ChunkEvent",
    "ContextInsufficientRejectEvent",
    "ContextSufficientAcceptEvent",
    "ControlAndDisplayEvent",
    "ControlEvent",
    "CostEvent",
    "DisplayEvent",
    "Embedding",
    "EmbeddingEvent",
    "ExceptionEvent",
    "ExpertRejectEvent",
    "FewShotAcceptEvent",
    "FewShotRejectEvent",
    "GuardAcceptEvent",
    "GuardEvent",
    "GuardRejectionEvent",
    "HumanInTheLoop",
    "HumanInTheLoopChat",
    "HumanInTheLoopChatRequestEvent",
    "HumanInTheLoopChatResponseEvent",
    "HumanInTheLoopConfirmation",
    "HumanInTheLoopConfirmationRequestEvent",
    "HumanInTheLoopConfirmationResponseEvent",
    "HumanInTheLoopInput",
    "HumanInTheLoopInputRequestEvent",
    "HumanInTheLoopInputResponseEvent",
    "HumanInTheLoopRequestEvent",
    "HumanInTheLoopResponseEvent",
    "ImageContent",
    "LLMCostEvent",
    "LLMEvent",
    "LLMStopEvent",
    "LanguageEvent",
    "LimitChatHistoryEvent",
    "Message",
    "RerankerEvent",
    "RetrieveOrganizationMemoryEvent",
    "RetrieveUserMemoryEvent",
    "RetrieverEvent",
    "RouteOptions",
    "RouterEvent",
    "SemanticEvent",
    "SensitiveInfoAcceptEvent",
    "SensitiveInfoRejectEvent",
    "SlackConfig",
    "StandaloneQuestionCondenserEvent",
    "StartEvent",
    "StopEvent",
    "StoreOrganizationMemoryEvent",
    "StoreUserMemoryEvent",
    "TeamsConfig",
    "TextContent",
    "ThoughtEvent",
    "ToolEvent",
    "UserMessageEvent",
    "UserUploadedFile",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AddMemoryToChatHistoryEvent": "swiss_ai_hub.core.events.agent.memory.history.AddMemoryToChatHistoryEvent",
    "AddOrganizationMemoryToChatHistoryEvent": "swiss_ai_hub.core.events.agent.memory.history.AddOrganizationMemoryToChatHistoryEvent",
    "AddUserMemoryToChatHistoryEvent": "swiss_ai_hub.core.events.agent.memory.history.AddUserMemoryToChatHistoryEvent",
    "AgentClassDiscoveryResponseEvent": "swiss_ai_hub.core.events.agent.discovery.AgentClassDiscoveryResponseEvent",
    "AgentConfigSpecs": "swiss_ai_hub.core.events.agent.discovery.AgentConfigSpecs",
    "AgentConfigSpecsEntity": "swiss_ai_hub.core.events.agent.discovery.AgentConfigSpecsEntity",
    "AgentEvent": "swiss_ai_hub.core.events.agent.semantic.agent.AgentEvent",
    "AgentInTheLoop": "swiss_ai_hub.core.events.agent.aitl.AgentInTheLoop",
    "AgentInTheLoopExceptionEvent": "swiss_ai_hub.core.events.agent.aitl.exception.AgentInTheLoopExceptionEvent",
    "AgentInTheLoopRequestEvent": "swiss_ai_hub.core.events.agent.aitl.request.AgentInTheLoopRequestEvent",
    "AgentInTheLoopResponseEvent": "swiss_ai_hub.core.events.agent.aitl.response.AgentInTheLoopResponseEvent",
    "AgentSuitabilityAcceptEvent": "swiss_ai_hub.core.events.agent.guard.AgentSuitabilityAcceptEvent",
    "AgentSuitabilityRejectEvent": "swiss_ai_hub.core.events.agent.guard.AgentSuitabilityRejectEvent",
    "AudioContent": "swiss_ai_hub.core.events.agent.semantic.llm.Message",
    "BaseRetrieveMemoryEvent": "swiss_ai_hub.core.events.agent.memory.retrieve.BaseRetrieveMemoryEvent",
    "BaseStoreMemoryEvent": "swiss_ai_hub.core.events.agent.memory.store.BaseStoreMemoryEvent",
    "BotInTheLoop": "swiss_ai_hub.core.events.agent.bitl.BotInTheLoop",
    "BotInTheLoopRequestEvent": "swiss_ai_hub.core.events.agent.bitl.request.BotInTheLoopRequestEvent",
    "BotInTheLoopResponderInfo": "swiss_ai_hub.core.events.agent.bitl.response.BotInTheLoopResponseEvent",
    "BotInTheLoopResponseEvent": "swiss_ai_hub.core.events.agent.bitl.response.BotInTheLoopResponseEvent",
    "ChainEvent": "swiss_ai_hub.core.events.agent.semantic.chain.ChainEvent",
    "ChunkEvent": "swiss_ai_hub.core.events.agent.display.ChunkEvent",
    "ContextInsufficientRejectEvent": "swiss_ai_hub.core.events.agent.guard.ContextInsufficientRejectEvent",
    "ContextSufficientAcceptEvent": "swiss_ai_hub.core.events.agent.guard.ContextSufficientAcceptEvent",
    "ControlAndDisplayEvent": "swiss_ai_hub.core.events.agent.ControlAndDisplayEvent",
    "ControlEvent": "swiss_ai_hub.core.events.agent.control.ControlEvent",
    "CostEvent": "swiss_ai_hub.core.events.agent.cost.CostEvent",
    "DisplayEvent": "swiss_ai_hub.core.events.agent.display.DisplayEvent",
    "Embedding": "swiss_ai_hub.core.events.agent.semantic.embedding.Embedding",
    "EmbeddingEvent": "swiss_ai_hub.core.events.agent.semantic.embedding.EmbeddingEvent",
    "ExceptionEvent": "swiss_ai_hub.core.events.agent.control.exception.ExceptionEvent",
    "ExpertRejectEvent": "swiss_ai_hub.core.events.agent.guard.ExpertRejectEvent",
    "FewShotAcceptEvent": "swiss_ai_hub.core.events.agent.guard.FewShotAcceptEvent",
    "FewShotRejectEvent": "swiss_ai_hub.core.events.agent.guard.FewShotRejectEvent",
    "GuardAcceptEvent": "swiss_ai_hub.core.events.agent.guard.GuardAcceptEvent",
    "GuardEvent": "swiss_ai_hub.core.events.agent.semantic.guard.GuardEvent",
    "GuardRejectionEvent": "swiss_ai_hub.core.events.agent.guard.GuardRejectionEvent",
    "HumanInTheLoop": "swiss_ai_hub.core.events.agent.hitl.HumanInTheLoop",
    "HumanInTheLoopChat": "swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopChat",
    "HumanInTheLoopChatRequestEvent": "swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopChatRequestEvent",
    "HumanInTheLoopChatResponseEvent": "swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopChatResponseEvent",
    "HumanInTheLoopConfirmation": "swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopConfirmation",
    "HumanInTheLoopConfirmationRequestEvent": "swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopConfirmationRequestEvent",
    "HumanInTheLoopConfirmationResponseEvent": "swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopConfirmationResponseEvent",
    "HumanInTheLoopInput": "swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopInput",
    "HumanInTheLoopInputRequestEvent": "swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopInputRequestEvent",
    "HumanInTheLoopInputResponseEvent": "swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopInputResponseEvent",
    "HumanInTheLoopRequestEvent": "swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopRequestEvent",
    "HumanInTheLoopResponseEvent": "swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopResponseEvent",
    "ImageContent": "swiss_ai_hub.core.events.agent.semantic.llm.Message",
    "LLMCostEvent": "swiss_ai_hub.core.events.agent.cost.LLMCostEvent",
    "LLMEvent": "swiss_ai_hub.core.events.agent.semantic.llm.LLMEvent",
    "LLMStopEvent": "swiss_ai_hub.core.events.agent.semantic.llm.LLMStopEvent",
    "LanguageEvent": "swiss_ai_hub.core.events.agent.common.LanguageEvent",
    "LimitChatHistoryEvent": "swiss_ai_hub.core.events.agent.common.LimitChatHistoryEvent",
    "Message": "swiss_ai_hub.core.events.agent.semantic.llm.Message",
    "RerankerEvent": "swiss_ai_hub.core.events.agent.semantic.reranker.RerankerEvent",
    "RetrieveOrganizationMemoryEvent": "swiss_ai_hub.core.events.agent.memory.retrieve.RetrieveOrganizationMemoryEvent",
    "RetrieveUserMemoryEvent": "swiss_ai_hub.core.events.agent.memory.retrieve.RetrieveUserMemoryEvent",
    "RetrieverEvent": "swiss_ai_hub.core.events.agent.semantic.retriever.RetrieverEvent",
    "RouteOptions": "swiss_ai_hub.core.events.agent.router.RouteOptions",
    "RouterEvent": "swiss_ai_hub.core.events.agent.router.RouterEvent",
    "SemanticEvent": "swiss_ai_hub.core.events.agent.semantic.SemanticEvent",
    "SensitiveInfoAcceptEvent": "swiss_ai_hub.core.events.agent.guard.SensitiveInfoAcceptEvent",
    "SensitiveInfoRejectEvent": "swiss_ai_hub.core.events.agent.guard.SensitiveInfoRejectEvent",
    "SlackConfig": "swiss_ai_hub.core.events.agent.bitl.request.BotInTheLoopRequestEvent",
    "StandaloneQuestionCondenserEvent": "swiss_ai_hub.core.events.agent.common.StandaloneQuestionCondenserEvent",
    "StartEvent": "swiss_ai_hub.core.events.agent.control.start.StartEvent",
    "StopEvent": "swiss_ai_hub.core.events.agent.control.stop.StopEvent",
    "StoreOrganizationMemoryEvent": "swiss_ai_hub.core.events.agent.memory.store.StoreOrganizationMemoryEvent",
    "StoreUserMemoryEvent": "swiss_ai_hub.core.events.agent.memory.store.StoreUserMemoryEvent",
    "TeamsConfig": "swiss_ai_hub.core.events.agent.bitl.request.BotInTheLoopRequestEvent",
    "TextContent": "swiss_ai_hub.core.events.agent.semantic.llm.Message",
    "ThoughtEvent": "swiss_ai_hub.core.events.agent.display.ThoughtEvent",
    "ToolEvent": "swiss_ai_hub.core.events.agent.semantic.tool.ToolEvent",
    "UserMessageEvent": "swiss_ai_hub.core.events.agent.user.UserMessageEvent",
    "UserUploadedFile": "swiss_ai_hub.core.events.agent.user.UserUploadedFile",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
