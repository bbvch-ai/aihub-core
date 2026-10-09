from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.universal_agent import UniversalAgent, UniversalAgentConfig
from swiss_ai_hub.agent.capabilities.attached_files.attached_files import READ_ATTACHED_FILES_TOOL
from swiss_ai_hub.agent.capabilities.knowledge.knowledge import SEARCH_KNOWLEDGE_TOOL
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig
from swiss_ai_hub.agent.capabilities.memory.memory import RECALL_MEMORY_TOOL
from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig

# Everything but reading the organisation's documents, the user's attachments and their memory is switched off, so the
# profile never reaches for the sandbox even when the user has Code Interpreter on.
_KEPT_TOOLS = {SEARCH_KNOWLEDGE_TOOL, READ_ATTACHED_FILES_TOOL, RECALL_MEMORY_TOOL}


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
        icon="mage:book-open",
        instructions=LocaleString(
            en=(
                "Answer only from what your tools return. Search our knowledge before every answer, and search "
                "again with other words when the first results do not cover the question. If the documents do not "
                "hold the answer, say so instead of answering from general knowledge."
            ),
            de=(
                "Antworte nur mit dem, was deine Werkzeuge liefern. Durchsuche vor jeder Antwort unser Wissen und "
                "suche mit anderen Begriffen erneut, wenn die ersten Ergebnisse die Frage nicht abdecken. Enthalten "
                "die Dokumente die Antwort nicht, sage das, statt aus allgemeinem Wissen zu antworten."
            ),
            fr=(
                "Réponds uniquement à partir de ce que tes outils renvoient. Recherche dans nos connaissances avant "
                "chaque réponse, et recherche à nouveau avec d'autres termes si les premiers résultats ne couvrent "
                "pas la question. Si les documents ne contiennent pas la réponse, dis-le au lieu de répondre à "
                "partir de connaissances générales."
            ),
            it=(
                "Rispondi solo con ciò che restituiscono i tuoi strumenti. Cerca nella nostra conoscenza prima di "
                "ogni risposta e cerca di nuovo con altre parole se i primi risultati non coprono la domanda. Se i "
                "documenti non contengono la risposta, dillo invece di rispondere con conoscenze generali."
            ),
        ),
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.1, timeout=120.0),
        ),
        knowledge_tool=KnowledgeToolConfig(every_readable_collection=True),
        user_memory=UserMemoryConfig(memory_llm="text-generation/gemma-4-31B-it"),
        org_memory=None,
        tool_loop=ToolLoopConfig(
            disabled_tools=[name for name in UniversalAgent.tools.names() if name not in _KEPT_TOOLS],
        ),
    )
