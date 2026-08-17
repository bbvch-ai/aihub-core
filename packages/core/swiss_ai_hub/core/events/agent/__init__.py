from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.events.agent.aitl.agent_in_the_loop import AgentInTheLoop
    from swiss_ai_hub.core.events.agent.aitl.exception.agent_in_the_loop_exception_event import (
        AgentInTheLoopExceptionEvent,
    )
    from swiss_ai_hub.core.events.agent.aitl.request.agent_in_the_loop_request_event import AgentInTheLoopRequestEvent
    from swiss_ai_hub.core.events.agent.aitl.response.agent_in_the_loop_response_event import (
        AgentInTheLoopResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.bitl.bot_in_the_loop import BotInTheLoop
    from swiss_ai_hub.core.events.agent.bitl.request.bot_in_the_loop_request_event import (
        BotInTheLoopRequestEvent,
        SlackConfig,
        TeamsConfig,
    )
    from swiss_ai_hub.core.events.agent.bitl.response.bot_in_the_loop_response_event import (
        BotInTheLoopResponderInfo,
        BotInTheLoopResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.common.language_event import LanguageEvent
    from swiss_ai_hub.core.events.agent.common.limit_chat_history_event import LimitChatHistoryEvent
    from swiss_ai_hub.core.events.agent.common.standalone_question_condenser_event import (
        StandaloneQuestionCondenserEvent,
    )
    from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
    from swiss_ai_hub.core.events.agent.control.exception.exception_event import ExceptionEvent
    from swiss_ai_hub.core.events.agent.control.start.rag_start_event import RAGStartEvent
    from swiss_ai_hub.core.events.agent.control.start.scheduled_start_event import ScheduledStartEvent
    from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
    from swiss_ai_hub.core.events.agent.control.stop.rag_failure_reason import RAGFailureReason
    from swiss_ai_hub.core.events.agent.control.stop.rag_failure_stop_event import RAGFailureStopEvent
    from swiss_ai_hub.core.events.agent.control.stop.rag_stop_event import RAGStopEvent
    from swiss_ai_hub.core.events.agent.control.stop.rag_success_stop_event import RAGSuccessStopEvent
    from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
    from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
    from swiss_ai_hub.core.events.agent.cost.cost_event import CostEvent
    from swiss_ai_hub.core.events.agent.cost.llm_cost_event import LLMCostEvent
    from swiss_ai_hub.core.events.agent.discovery.agent_class_discovery_response_event import (
        AgentClassDiscoveryResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.discovery.agent_config_specs import AgentConfigSpecs
    from swiss_ai_hub.core.events.agent.discovery.agent_config_specs_entity import AgentConfigSpecsEntity
    from swiss_ai_hub.core.events.agent.display.chunk_event import ChunkEvent
    from swiss_ai_hub.core.events.agent.display.conversation_title_event import ConversationTitleEvent
    from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
    from swiss_ai_hub.core.events.agent.display.follow_up_questions_event import FollowUpQuestionsEvent
    from swiss_ai_hub.core.events.agent.display.thought_event import ThoughtEvent
    from swiss_ai_hub.core.events.agent.guard.agent_suitability_accept_event import AgentSuitabilityAcceptEvent
    from swiss_ai_hub.core.events.agent.guard.agent_suitability_reject_event import AgentSuitabilityRejectEvent
    from swiss_ai_hub.core.events.agent.guard.context_insufficient_reject_event import ContextInsufficientRejectEvent
    from swiss_ai_hub.core.events.agent.guard.context_sufficient_accept_event import ContextSufficientAcceptEvent
    from swiss_ai_hub.core.events.agent.guard.expert_reject_event import ExpertRejectEvent
    from swiss_ai_hub.core.events.agent.guard.few_shot_accept_event import FewShotAcceptEvent
    from swiss_ai_hub.core.events.agent.guard.few_shot_reject_event import FewShotRejectEvent
    from swiss_ai_hub.core.events.agent.guard.guard_accept_event import GuardAcceptEvent
    from swiss_ai_hub.core.events.agent.guard.guard_rejection_event import GuardRejectionEvent
    from swiss_ai_hub.core.events.agent.guard.sensitive_info_accept_event import SensitiveInfoAcceptEvent
    from swiss_ai_hub.core.events.agent.guard.sensitive_info_reject_event import SensitiveInfoRejectEvent
    from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop import HumanInTheLoop
    from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_chat import HumanInTheLoopChat
    from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_confirmation import HumanInTheLoopConfirmation
    from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_input import HumanInTheLoopInput
    from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_chat_request_event import (
        HumanInTheLoopChatRequestEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_confirmation_request_event import (
        HumanInTheLoopConfirmationRequestEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_input_request_event import (
        HumanInTheLoopInputRequestEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_request_event import HumanInTheLoopRequestEvent
    from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_chat_response_event import (
        HumanInTheLoopChatResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_confirmation_response_event import (
        HumanInTheLoopConfirmationResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_input_response_event import (
        HumanInTheLoopInputResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_response_event import (
        HumanInTheLoopResponseEvent,
    )
    from swiss_ai_hub.core.events.agent.imap.drafted_reply_ref import DraftedReplyRef
    from swiss_ai_hub.core.events.agent.imap.mail_attachment_ref import MailAttachmentRef
    from swiss_ai_hub.core.events.agent.imap.mail_batch_drafted_event import MailBatchDraftedEvent
    from swiss_ai_hub.core.events.agent.imap.mail_fetched_event import MailFetchedEvent
    from swiss_ai_hub.core.events.agent.imap.mail_message_ref import MailMessageRef
    from swiss_ai_hub.core.events.agent.imap.mail_moved_event import MailMovedEvent
    from swiss_ai_hub.core.events.agent.imap.unread_mail_listed_event import UnreadMailListedEvent
    from swiss_ai_hub.core.events.agent.imap.unread_mail_summary import UnreadMailSummary
    from swiss_ai_hub.core.events.agent.memory.history.add_memory_to_chat_history_event import (
        AddMemoryToChatHistoryEvent,
    )
    from swiss_ai_hub.core.events.agent.memory.history.add_organization_memory_to_chat_history_event import (
        AddOrganizationMemoryToChatHistoryEvent,
    )
    from swiss_ai_hub.core.events.agent.memory.history.add_user_memory_to_chat_history_event import (
        AddUserMemoryToChatHistoryEvent,
    )
    from swiss_ai_hub.core.events.agent.memory.request.memory_storage_requested_event import (
        MemoryStorageRequestedEvent,
    )
    from swiss_ai_hub.core.events.agent.memory.request.store_user_memory_requested_event import (
        StoreUserMemoryRequestedEvent,
    )
    from swiss_ai_hub.core.events.agent.memory.retrieve.base_retrieve_memory_event import BaseRetrieveMemoryEvent
    from swiss_ai_hub.core.events.agent.memory.retrieve.retrieve_organization_memory_event import (
        RetrieveOrganizationMemoryEvent,
    )
    from swiss_ai_hub.core.events.agent.memory.retrieve.retrieve_user_memory_event import RetrieveUserMemoryEvent
    from swiss_ai_hub.core.events.agent.memory.store.base_store_memory_event import BaseStoreMemoryEvent
    from swiss_ai_hub.core.events.agent.memory.store.store_organization_memory_event import StoreOrganizationMemoryEvent
    from swiss_ai_hub.core.events.agent.memory.store.store_user_memory_event import StoreUserMemoryEvent
    from swiss_ai_hub.core.events.agent.router.route_options import RouteOptions
    from swiss_ai_hub.core.events.agent.router.router_event import RouterEvent
    from swiss_ai_hub.core.events.agent.self_awareness.meta_question_detected_event import MetaQuestionDetectedEvent
    from swiss_ai_hub.core.events.agent.self_awareness.not_a_meta_question_event import NotAMetaQuestionEvent
    from swiss_ai_hub.core.events.agent.semantic.agent.agent_event import AgentEvent
    from swiss_ai_hub.core.events.agent.semantic.chain.chain_event import ChainEvent
    from swiss_ai_hub.core.events.agent.semantic.embedding.embedding import Embedding
    from swiss_ai_hub.core.events.agent.semantic.embedding.embedding_event import EmbeddingEvent
    from swiss_ai_hub.core.events.agent.semantic.guard.guard_event import GuardEvent
    from swiss_ai_hub.core.events.agent.semantic.llm.llm_event import LLMEvent
    from swiss_ai_hub.core.events.agent.semantic.llm.llm_stop_event import LLMStopEvent
    from swiss_ai_hub.core.events.agent.semantic.llm.message import AudioContent, ImageContent, Message, TextContent
    from swiss_ai_hub.core.events.agent.semantic.reranker.reranker_event import RerankerEvent
    from swiss_ai_hub.core.events.agent.semantic.retriever.retriever_event import RetrieverEvent
    from swiss_ai_hub.core.events.agent.semantic.semantic_event import SemanticEvent
    from swiss_ai_hub.core.events.agent.semantic.tool.tool_event import ToolEvent
    from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
    from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile

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
    "ConversationTitleEvent",
    "CostEvent",
    "DisplayEvent",
    "Embedding",
    "EmbeddingEvent",
    "ExceptionEvent",
    "ExpertRejectEvent",
    "FewShotAcceptEvent",
    "FewShotRejectEvent",
    "FollowUpQuestionsEvent",
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
    "DraftedReplyRef",
    "MailAttachmentRef",
    "MailBatchDraftedEvent",
    "MailFetchedEvent",
    "MailMessageRef",
    "MailMovedEvent",
    "Message",
    "MetaQuestionDetectedEvent",
    "NotAMetaQuestionEvent",
    "RAGFailureReason",
    "RAGFailureStopEvent",
    "RAGStartEvent",
    "RAGStopEvent",
    "RAGSuccessStopEvent",
    "RerankerEvent",
    "RetrieveOrganizationMemoryEvent",
    "RetrieveUserMemoryEvent",
    "RetrieverEvent",
    "RouteOptions",
    "RouterEvent",
    "ScheduledStartEvent",
    "SemanticEvent",
    "SensitiveInfoAcceptEvent",
    "SensitiveInfoRejectEvent",
    "SlackConfig",
    "StandaloneQuestionCondenserEvent",
    "StartEvent",
    "StopEvent",
    "StoreOrganizationMemoryEvent",
    "StoreUserMemoryEvent",
    "StoreUserMemoryRequestedEvent",
    "MemoryStorageRequestedEvent",
    "TeamsConfig",
    "TextContent",
    "ThoughtEvent",
    "ToolEvent",
    "UnreadMailListedEvent",
    "UnreadMailSummary",
    "UserMessageEvent",
    "UserUploadedFile",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AddMemoryToChatHistoryEvent": "swiss_ai_hub.core.events.agent.memory.history.add_memory_to_chat_history_event",
    "AddOrganizationMemoryToChatHistoryEvent": "swiss_ai_hub.core.events.agent.memory.history.add_organization_memory_to_chat_history_event",
    "AddUserMemoryToChatHistoryEvent": "swiss_ai_hub.core.events.agent.memory.history.add_user_memory_to_chat_history_event",
    "AgentClassDiscoveryResponseEvent": "swiss_ai_hub.core.events.agent.discovery.agent_class_discovery_response_event",
    "AgentConfigSpecs": "swiss_ai_hub.core.events.agent.discovery.agent_config_specs",
    "AgentConfigSpecsEntity": "swiss_ai_hub.core.events.agent.discovery.agent_config_specs_entity",
    "AgentEvent": "swiss_ai_hub.core.events.agent.semantic.agent.agent_event",
    "AgentInTheLoop": "swiss_ai_hub.core.events.agent.aitl.agent_in_the_loop",
    "AgentInTheLoopExceptionEvent": "swiss_ai_hub.core.events.agent.aitl.exception.agent_in_the_loop_exception_event",
    "AgentInTheLoopRequestEvent": "swiss_ai_hub.core.events.agent.aitl.request.agent_in_the_loop_request_event",
    "AgentInTheLoopResponseEvent": "swiss_ai_hub.core.events.agent.aitl.response.agent_in_the_loop_response_event",
    "AgentSuitabilityAcceptEvent": "swiss_ai_hub.core.events.agent.guard.agent_suitability_accept_event",
    "AgentSuitabilityRejectEvent": "swiss_ai_hub.core.events.agent.guard.agent_suitability_reject_event",
    "AudioContent": "swiss_ai_hub.core.events.agent.semantic.llm.message",
    "BaseRetrieveMemoryEvent": "swiss_ai_hub.core.events.agent.memory.retrieve.base_retrieve_memory_event",
    "BaseStoreMemoryEvent": "swiss_ai_hub.core.events.agent.memory.store.base_store_memory_event",
    "BotInTheLoop": "swiss_ai_hub.core.events.agent.bitl.bot_in_the_loop",
    "BotInTheLoopRequestEvent": "swiss_ai_hub.core.events.agent.bitl.request.bot_in_the_loop_request_event",
    "BotInTheLoopResponderInfo": "swiss_ai_hub.core.events.agent.bitl.response.bot_in_the_loop_response_event",
    "BotInTheLoopResponseEvent": "swiss_ai_hub.core.events.agent.bitl.response.bot_in_the_loop_response_event",
    "ChainEvent": "swiss_ai_hub.core.events.agent.semantic.chain.chain_event",
    "ChunkEvent": "swiss_ai_hub.core.events.agent.display.chunk_event",
    "ConversationTitleEvent": "swiss_ai_hub.core.events.agent.display.conversation_title_event",
    "ContextInsufficientRejectEvent": "swiss_ai_hub.core.events.agent.guard.context_insufficient_reject_event",
    "ContextSufficientAcceptEvent": "swiss_ai_hub.core.events.agent.guard.context_sufficient_accept_event",
    "ControlAndDisplayEvent": "swiss_ai_hub.core.events.agent.control_and_display_event",
    "ControlEvent": "swiss_ai_hub.core.events.agent.control.control_event",
    "CostEvent": "swiss_ai_hub.core.events.agent.cost.cost_event",
    "DisplayEvent": "swiss_ai_hub.core.events.agent.display.display_event",
    "Embedding": "swiss_ai_hub.core.events.agent.semantic.embedding.embedding",
    "EmbeddingEvent": "swiss_ai_hub.core.events.agent.semantic.embedding.embedding_event",
    "ExceptionEvent": "swiss_ai_hub.core.events.agent.control.exception.exception_event",
    "ExpertRejectEvent": "swiss_ai_hub.core.events.agent.guard.expert_reject_event",
    "FewShotAcceptEvent": "swiss_ai_hub.core.events.agent.guard.few_shot_accept_event",
    "FewShotRejectEvent": "swiss_ai_hub.core.events.agent.guard.few_shot_reject_event",
    "FollowUpQuestionsEvent": "swiss_ai_hub.core.events.agent.display.follow_up_questions_event",
    "GuardAcceptEvent": "swiss_ai_hub.core.events.agent.guard.guard_accept_event",
    "GuardEvent": "swiss_ai_hub.core.events.agent.semantic.guard.guard_event",
    "GuardRejectionEvent": "swiss_ai_hub.core.events.agent.guard.guard_rejection_event",
    "HumanInTheLoop": "swiss_ai_hub.core.events.agent.hitl.human_in_the_loop",
    "HumanInTheLoopChat": "swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_chat",
    "HumanInTheLoopChatRequestEvent": "swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_chat_request_event",
    "HumanInTheLoopChatResponseEvent": "swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_chat_response_event",
    "HumanInTheLoopConfirmation": "swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_confirmation",
    "HumanInTheLoopConfirmationRequestEvent": "swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_confirmation_request_event",
    "HumanInTheLoopConfirmationResponseEvent": "swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_confirmation_response_event",
    "HumanInTheLoopInput": "swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_input",
    "HumanInTheLoopInputRequestEvent": "swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_input_request_event",
    "HumanInTheLoopInputResponseEvent": "swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_input_response_event",
    "HumanInTheLoopRequestEvent": "swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_request_event",
    "HumanInTheLoopResponseEvent": "swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_response_event",
    "ImageContent": "swiss_ai_hub.core.events.agent.semantic.llm.message",
    "LLMCostEvent": "swiss_ai_hub.core.events.agent.cost.llm_cost_event",
    "LLMEvent": "swiss_ai_hub.core.events.agent.semantic.llm.llm_event",
    "LLMStopEvent": "swiss_ai_hub.core.events.agent.semantic.llm.llm_stop_event",
    "LanguageEvent": "swiss_ai_hub.core.events.agent.common.language_event",
    "LimitChatHistoryEvent": "swiss_ai_hub.core.events.agent.common.limit_chat_history_event",
    "DraftedReplyRef": "swiss_ai_hub.core.events.agent.imap.drafted_reply_ref",
    "MailAttachmentRef": "swiss_ai_hub.core.events.agent.imap.mail_attachment_ref",
    "MailBatchDraftedEvent": "swiss_ai_hub.core.events.agent.imap.mail_batch_drafted_event",
    "MailFetchedEvent": "swiss_ai_hub.core.events.agent.imap.mail_fetched_event",
    "MailMessageRef": "swiss_ai_hub.core.events.agent.imap.mail_message_ref",
    "MailMovedEvent": "swiss_ai_hub.core.events.agent.imap.mail_moved_event",
    "Message": "swiss_ai_hub.core.events.agent.semantic.llm.message",
    "MetaQuestionDetectedEvent": "swiss_ai_hub.core.events.agent.self_awareness.meta_question_detected_event",
    "NotAMetaQuestionEvent": "swiss_ai_hub.core.events.agent.self_awareness.not_a_meta_question_event",
    "RAGFailureReason": "swiss_ai_hub.core.events.agent.control.stop.rag_failure_reason",
    "RAGFailureStopEvent": "swiss_ai_hub.core.events.agent.control.stop.rag_failure_stop_event",
    "RAGStartEvent": "swiss_ai_hub.core.events.agent.control.start.rag_start_event",
    "RAGStopEvent": "swiss_ai_hub.core.events.agent.control.stop.rag_stop_event",
    "RAGSuccessStopEvent": "swiss_ai_hub.core.events.agent.control.stop.rag_success_stop_event",
    "RerankerEvent": "swiss_ai_hub.core.events.agent.semantic.reranker.reranker_event",
    "RetrieveOrganizationMemoryEvent": "swiss_ai_hub.core.events.agent.memory.retrieve.retrieve_organization_memory_event",
    "RetrieveUserMemoryEvent": "swiss_ai_hub.core.events.agent.memory.retrieve.retrieve_user_memory_event",
    "RetrieverEvent": "swiss_ai_hub.core.events.agent.semantic.retriever.retriever_event",
    "RouteOptions": "swiss_ai_hub.core.events.agent.router.route_options",
    "RouterEvent": "swiss_ai_hub.core.events.agent.router.router_event",
    "ScheduledStartEvent": "swiss_ai_hub.core.events.agent.control.start.scheduled_start_event",
    "SemanticEvent": "swiss_ai_hub.core.events.agent.semantic.semantic_event",
    "SensitiveInfoAcceptEvent": "swiss_ai_hub.core.events.agent.guard.sensitive_info_accept_event",
    "SensitiveInfoRejectEvent": "swiss_ai_hub.core.events.agent.guard.sensitive_info_reject_event",
    "SlackConfig": "swiss_ai_hub.core.events.agent.bitl.request.bot_in_the_loop_request_event",
    "StandaloneQuestionCondenserEvent": "swiss_ai_hub.core.events.agent.common.standalone_question_condenser_event",
    "StartEvent": "swiss_ai_hub.core.events.agent.control.start.start_event",
    "StopEvent": "swiss_ai_hub.core.events.agent.control.stop.stop_event",
    "StoreOrganizationMemoryEvent": "swiss_ai_hub.core.events.agent.memory.store.store_organization_memory_event",
    "StoreUserMemoryEvent": "swiss_ai_hub.core.events.agent.memory.store.store_user_memory_event",
    "StoreUserMemoryRequestedEvent": (
        "swiss_ai_hub.core.events.agent.memory.request.store_user_memory_requested_event"
    ),
    "MemoryStorageRequestedEvent": "swiss_ai_hub.core.events.agent.memory.request.memory_storage_requested_event",
    "TeamsConfig": "swiss_ai_hub.core.events.agent.bitl.request.bot_in_the_loop_request_event",
    "TextContent": "swiss_ai_hub.core.events.agent.semantic.llm.message",
    "ThoughtEvent": "swiss_ai_hub.core.events.agent.display.thought_event",
    "ToolEvent": "swiss_ai_hub.core.events.agent.semantic.tool.tool_event",
    "UnreadMailListedEvent": "swiss_ai_hub.core.events.agent.imap.unread_mail_listed_event",
    "UnreadMailSummary": "swiss_ai_hub.core.events.agent.imap.unread_mail_summary",
    "UserMessageEvent": "swiss_ai_hub.core.events.agent.user.user_message_event",
    "UserUploadedFile": "swiss_ai_hub.core.events.agent.user.user_uploaded_file",
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
