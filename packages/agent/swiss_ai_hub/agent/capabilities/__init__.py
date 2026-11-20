from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.capabilities.attached_files.attached_files import READ_ATTACHED_FILES_TOOL, AttachedFiles
    from swiss_ai_hub.agent.capabilities.attached_files.attached_files_fields import AttachedFilesFields
    from swiss_ai_hub.agent.capabilities.capability import Capability
    from swiss_ai_hub.agent.capabilities.catalog import CapabilityCatalog
    from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
    from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
    from swiss_ai_hub.agent.capabilities.knowledge.knowledge import SEARCH_KNOWLEDGE_TOOL, Knowledge
    from swiss_ai_hub.agent.capabilities.knowledge.knowledge_fields import KnowledgeFields
    from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig
    from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_fields import KnowledgeToolFields
    from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_scope import KnowledgeToolScope
    from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_collection import (
        KnowledgeDocumentCollection,
    )
    from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
    from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
        KnowledgeDocumentRunScope,
    )
    from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope import KnowledgeDocumentScope
    from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_tools import (
        LIST_KNOWLEDGE_DOCUMENTS_TOOL,
        READ_KNOWLEDGE_DOCUMENT_TOOL,
        SEARCH_KNOWLEDGE_CONTENT_TOOL,
        KnowledgeDocumentTools,
    )
    from swiss_ai_hub.agent.capabilities.memory.memory import RECALL_MEMORY_TOOL, Memory
    from swiss_ai_hub.agent.capabilities.memory.memory_fields import MemoryFields
    from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig
    from swiss_ai_hub.agent.capabilities.record_extraction.extraction_call_form_request_event import (
        ExtractionCallFormRequestEvent,
    )
    from swiss_ai_hub.agent.capabilities.record_extraction.extraction_call_form_response_event import (
        ExtractionCallFormResponseEvent,
    )
    from swiss_ai_hub.agent.capabilities.record_extraction.extraction_history import ExtractionHistory
    from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import (
        EXTRACT_RECORDS_TOOL,
        RecordExtraction,
    )
    from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_config import RecordExtractionConfig
    from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
    from swiss_ai_hub.agent.capabilities.record_extraction.record_selection_tools import (
        SELECT_KNOWLEDGE_DOCUMENTS_TOOL,
        RecordSelectionTools,
    )
    from swiss_ai_hub.agent.capabilities.requested_features import RequestedFeatures
    from swiss_ai_hub.agent.capabilities.sandbox.sandbox_tools import SandboxTools
    from swiss_ai_hub.agent.capabilities.sandbox.sandbox_workspace import SandboxWorkspace
    from swiss_ai_hub.agent.capabilities.sandbox.user_files_tools import UserFilesTools
    from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy
    from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_rule import ToolApprovalRule
    from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
    from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop
    from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig
    from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields import ToolLoopFields
    from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
    from swiss_ai_hub.agent.capabilities.tool_loop.tool_set import ToolSet
    from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch import WebFetch
    from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_config import WebFetchConfig
    from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_fields import WebFetchFields

__all__ = [
    "EXTRACT_RECORDS_TOOL",
    "LIST_KNOWLEDGE_DOCUMENTS_TOOL",
    "READ_ATTACHED_FILES_TOOL",
    "READ_KNOWLEDGE_DOCUMENT_TOOL",
    "RECALL_MEMORY_TOOL",
    "SEARCH_KNOWLEDGE_CONTENT_TOOL",
    "SEARCH_KNOWLEDGE_TOOL",
    "SELECT_KNOWLEDGE_DOCUMENTS_TOOL",
    "AttachedFiles",
    "AttachedFilesFields",
    "Capability",
    "CapabilityCatalog",
    "Conversation",
    "ConversationFields",
    "ExtractionCallFormRequestEvent",
    "ExtractionCallFormResponseEvent",
    "ExtractionHistory",
    "Knowledge",
    "KnowledgeDocumentCollection",
    "KnowledgeDocumentConfig",
    "KnowledgeDocumentRunScope",
    "KnowledgeDocumentScope",
    "KnowledgeDocumentTools",
    "KnowledgeFields",
    "KnowledgeToolConfig",
    "KnowledgeToolFields",
    "KnowledgeToolScope",
    "Memory",
    "MemoryFields",
    "RecordExtraction",
    "RecordExtractionConfig",
    "RecordExtractionFields",
    "RecordSelectionTools",
    "RequestedFeatures",
    "SandboxTools",
    "SandboxWorkspace",
    "UserFilesTools",
    "ToolApprovalPolicy",
    "ToolApprovalRule",
    "ToolContext",
    "ToolLoop",
    "ToolLoopConfig",
    "ToolLoopFields",
    "ToolOptions",
    "ToolSet",
    "UserMemoryConfig",
    "WebFetch",
    "WebFetchConfig",
    "WebFetchFields",
]

_ATTACHED_FILES_MODULE = "swiss_ai_hub.agent.capabilities.attached_files.attached_files"
_KNOWLEDGE_MODULE = "swiss_ai_hub.agent.capabilities.knowledge.knowledge"
_KNOWLEDGE_DOCUMENT_TOOLS_MODULE = "swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_tools"
_MEMORY_MODULE = "swiss_ai_hub.agent.capabilities.memory.memory"
_RECORD_EXTRACTION_MODULE = "swiss_ai_hub.agent.capabilities.record_extraction.record_extraction"
_RECORD_SELECTION_TOOLS_MODULE = "swiss_ai_hub.agent.capabilities.record_extraction.record_selection_tools"

_LAZY_IMPORTS: dict[str, str] = {
    "EXTRACT_RECORDS_TOOL": _RECORD_EXTRACTION_MODULE,
    "LIST_KNOWLEDGE_DOCUMENTS_TOOL": _KNOWLEDGE_DOCUMENT_TOOLS_MODULE,
    "READ_ATTACHED_FILES_TOOL": _ATTACHED_FILES_MODULE,
    "READ_KNOWLEDGE_DOCUMENT_TOOL": _KNOWLEDGE_DOCUMENT_TOOLS_MODULE,
    "RECALL_MEMORY_TOOL": _MEMORY_MODULE,
    "SEARCH_KNOWLEDGE_CONTENT_TOOL": _KNOWLEDGE_DOCUMENT_TOOLS_MODULE,
    "SEARCH_KNOWLEDGE_TOOL": _KNOWLEDGE_MODULE,
    "SELECT_KNOWLEDGE_DOCUMENTS_TOOL": _RECORD_SELECTION_TOOLS_MODULE,
    "AttachedFiles": _ATTACHED_FILES_MODULE,
    "AttachedFilesFields": "swiss_ai_hub.agent.capabilities.attached_files.attached_files_fields",
    "Capability": "swiss_ai_hub.agent.capabilities.capability",
    "CapabilityCatalog": "swiss_ai_hub.agent.capabilities.catalog",
    "Conversation": "swiss_ai_hub.agent.capabilities.conversation.conversation",
    "ConversationFields": "swiss_ai_hub.agent.capabilities.conversation.conversation_fields",
    "ExtractionCallFormRequestEvent": (
        "swiss_ai_hub.agent.capabilities.record_extraction.extraction_call_form_request_event"
    ),
    "ExtractionCallFormResponseEvent": (
        "swiss_ai_hub.agent.capabilities.record_extraction.extraction_call_form_response_event"
    ),
    "ExtractionHistory": "swiss_ai_hub.agent.capabilities.record_extraction.extraction_history",
    "Knowledge": _KNOWLEDGE_MODULE,
    "KnowledgeDocumentCollection": (
        "swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_collection"
    ),
    "KnowledgeDocumentConfig": "swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config",
    "KnowledgeDocumentRunScope": "swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope",
    "KnowledgeDocumentScope": "swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope",
    "KnowledgeDocumentTools": _KNOWLEDGE_DOCUMENT_TOOLS_MODULE,
    "KnowledgeFields": "swiss_ai_hub.agent.capabilities.knowledge.knowledge_fields",
    "KnowledgeToolConfig": "swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config",
    "KnowledgeToolFields": "swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_fields",
    "KnowledgeToolScope": "swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_scope",
    "Memory": _MEMORY_MODULE,
    "MemoryFields": "swiss_ai_hub.agent.capabilities.memory.memory_fields",
    "RecordExtraction": _RECORD_EXTRACTION_MODULE,
    "RecordExtractionConfig": "swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_config",
    "RecordExtractionFields": "swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields",
    "RecordSelectionTools": _RECORD_SELECTION_TOOLS_MODULE,
    "RequestedFeatures": "swiss_ai_hub.agent.capabilities.requested_features",
    "SandboxTools": "swiss_ai_hub.agent.capabilities.sandbox.sandbox_tools",
    "SandboxWorkspace": "swiss_ai_hub.agent.capabilities.sandbox.sandbox_workspace",
    "UserFilesTools": "swiss_ai_hub.agent.capabilities.sandbox.user_files_tools",
    "ToolApprovalPolicy": "swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy",
    "ToolApprovalRule": "swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_rule",
    "ToolContext": "swiss_ai_hub.agent.capabilities.tool_loop.tool_context",
    "ToolLoop": "swiss_ai_hub.agent.capabilities.tool_loop.tool_loop",
    "ToolLoopConfig": "swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config",
    "ToolLoopFields": "swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields",
    "ToolOptions": "swiss_ai_hub.agent.capabilities.tool_loop.tool_options",
    "ToolSet": "swiss_ai_hub.agent.capabilities.tool_loop.tool_set",
    "UserMemoryConfig": "swiss_ai_hub.agent.capabilities.memory.user_memory_config",
    "WebFetch": "swiss_ai_hub.agent.capabilities.web_fetch.web_fetch",
    "WebFetchConfig": "swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_config",
    "WebFetchFields": "swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_fields",
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
