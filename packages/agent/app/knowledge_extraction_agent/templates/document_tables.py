from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.knowledge_extraction_agent import KnowledgeExtractionAgentConfig
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_config import RecordExtractionConfig
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig


def build() -> KnowledgeExtractionAgentConfig:
    return KnowledgeExtractionAgentConfig(
        agent_id="document-tables",
        name=LocaleString(
            en="Document Tables",
            de="Dokumenttabellen",
            fr="Tableaux de documents",
            it="Tabelle dai documenti",
        ),
        description=LocaleString(
            en=(
                "Collects records from many documents into one table, such as every hardware position on a "
                "supplier's invoices, and names the file of every row."
            ),
            de=(
                "Sammelt Datensätze aus vielen Dokumenten in einer Tabelle, etwa jede Hardware-Position auf den "
                "Rechnungen eines Lieferanten, und nennt zu jeder Zeile die Datei."
            ),
            fr=(
                "Rassemble des enregistrements de nombreux documents dans un tableau, comme chaque position matérielle "
                "sur les factures d'un fournisseur, et nomme le fichier de chaque ligne."
            ),
            it=(
                "Raccoglie record da molti documenti in un'unica tabella, come ogni posizione hardware sulle fatture "
                "di un fornitore, e indica il file di ogni riga."
            ),
        ),
        icon="mdi:table-search",
        llm=LLMConfig(
            model_name="text-generation/Kimi-K2.6",
            default_parameter=LLMParameter(temperature=0.1, timeout=120.0),
        ),
        task_llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        knowledge_documents=KnowledgeDocumentConfig(enabled=True, narrow_references=True),
        record_extraction=RecordExtractionConfig(extraction_model_name="text-generation/gemma-4-31B-it"),
        tool_loop=ToolLoopConfig(max_iterations=15, max_tool_calls=30),
    )
