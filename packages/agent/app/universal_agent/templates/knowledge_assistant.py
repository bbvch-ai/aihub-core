from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.universal_agent import UniversalAgent, UniversalAgentConfig
from swiss_ai_hub.agent.capabilities.attached_files.attached_files import READ_ATTACHED_FILES_TOOL
from swiss_ai_hub.agent.capabilities.knowledge.knowledge import SEARCH_KNOWLEDGE_TOOL
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_tools import (
    LIST_KNOWLEDGE_DOCUMENTS_TOOL,
    READ_KNOWLEDGE_DOCUMENT_TOOL,
    SEARCH_KNOWLEDGE_CONTENT_TOOL,
)
from swiss_ai_hub.agent.capabilities.memory.memory import RECALL_MEMORY_TOOL
from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import EXTRACT_RECORDS_TOOL
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_config import RecordExtractionConfig
from swiss_ai_hub.agent.capabilities.record_extraction.record_selection_tools import SELECT_KNOWLEDGE_DOCUMENTS_TOOL
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_rule import ToolApprovalRule
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig

# Everything but reading the organisation's documents, the user's attachments and their memory is switched off, so the
# profile never reaches for the sandbox even when the user has Code Interpreter on.
_KEPT_TOOLS = {
    SEARCH_KNOWLEDGE_TOOL,
    LIST_KNOWLEDGE_DOCUMENTS_TOOL,
    SEARCH_KNOWLEDGE_CONTENT_TOOL,
    READ_KNOWLEDGE_DOCUMENT_TOOL,
    SELECT_KNOWLEDGE_DOCUMENTS_TOOL,
    EXTRACT_RECORDS_TOOL,
    READ_ATTACHED_FILES_TOOL,
    RECALL_MEMORY_TOOL,
}


def build() -> UniversalAgentConfig:
    return UniversalAgentConfig(
        agent_id="knowledge-assistant",
        name=LocaleString(
            en="Knowledge Assistant",
            de="Wissensassistent",
            fr="Assistant de connaissances",
            it="Assistente della conoscenza",
        ),
        description=LocaleString(
            en=(
                "Answers from your organisation's documents and attached files only, searches as often as it "
                "needs, and cites what it used."
            ),
            de=(
                "Antwortet ausschliesslich aus den Dokumenten Ihrer Organisation und angehängten Dateien, sucht so "
                "oft wie nötig und nennt die verwendeten Quellen."
            ),
            fr=(
                "Répond uniquement à partir des documents de votre organisation et des fichiers joints, recherche "
                "autant que nécessaire et cite ce qu'il a utilisé."
            ),
            it=(
                "Risponde solo dai documenti della vostra organizzazione e dai file allegati, cerca quanto serve "
                "e cita ciò che ha usato."
            ),
        ),
        icon="mage:book",
        instructions=LocaleString(
            en=(
                "Answer only from what your tools return. Look into our knowledge before every answer: search it, "
                "find exact names and numbers in the documents' text, or read a whole document when the question is "
                "about one. Search again with other words when the first results do not cover the question. If the "
                "documents do not hold the answer, say so instead of answering from general knowledge."
            ),
            de=(
                "Antworte nur mit dem, was deine Werkzeuge liefern. Schau vor jeder Antwort in unser Wissen: "
                "durchsuche es, finde exakte Namen und Nummern im Text der Dokumente oder lies ein ganzes Dokument, "
                "wenn die Frage eines betrifft. Suche mit anderen Begriffen erneut, wenn die ersten Ergebnisse die "
                "Frage nicht abdecken. Enthalten die Dokumente die Antwort nicht, sage das, statt aus allgemeinem "
                "Wissen zu antworten."
            ),
            fr=(
                "Réponds uniquement à partir de ce que tes outils renvoient. Consulte nos connaissances avant chaque "
                "réponse : recherche-y, trouve des noms et des numéros exacts dans le texte des documents, ou lis un "
                "document entier quand la question porte sur lui. Recherche à nouveau avec d'autres termes si les "
                "premiers résultats ne couvrent pas la question. Si les documents ne contiennent pas la réponse, "
                "dis-le au lieu de répondre à partir de connaissances générales."
            ),
            it=(
                "Rispondi solo con ciò che restituiscono i tuoi strumenti. Consulta la nostra conoscenza prima di "
                "ogni risposta: cercala, trova nomi e numeri esatti nel testo dei documenti o leggi un documento "
                "intero quando la domanda riguarda quello. Cerca di nuovo con altre parole se i primi risultati non "
                "coprono la domanda. Se i documenti non contengono la risposta, dillo invece di rispondere con "
                "conoscenze generali."
            ),
        ),
        llm=LLMConfig(
            model_name="text-generation/Kimi-K2.6",
            default_parameter=LLMParameter(temperature=0.1, timeout=120.0),
        ),
        task_llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        knowledge_tool=KnowledgeToolConfig(every_readable_collection=True),
        knowledge_documents=KnowledgeDocumentConfig(enabled=True),
        record_extraction=RecordExtractionConfig(extraction_model_name="text-generation/gemma-4-31B-it"),
        user_memory=UserMemoryConfig(memory_llm="text-generation/gemma-4-31B-it"),
        org_memory=None,
        tool_loop=ToolLoopConfig(
            max_tool_calls=30,
            disabled_tools=[name for name in UniversalAgent.tools.names() if name not in _KEPT_TOOLS],
            # API and bot clients cannot answer a confirmation; a broad extraction asks the user anyway.
            approvals=[ToolApprovalRule(tool=EXTRACT_RECORDS_TOOL, policy=ToolApprovalPolicy.NEVER)],
        ),
    )
