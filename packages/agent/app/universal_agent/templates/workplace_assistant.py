from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.universal_agent import UniversalAgentConfig
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig
from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig


def build() -> UniversalAgentConfig:
    return UniversalAgentConfig(
        agent_id="workplace-assistant",
        name=LocaleString(
            en="Workplace Assistant",
            de="Arbeitsplatz-Assistent",
            fr="Assistant de travail",
            it="Assistente di lavoro",
        ),
        description=LocaleString(
            en=(
                "Everyday assistant that searches your knowledge, reads attached files, remembers what matters "
                "to you and, with Code Interpreter on, works with files in your sandbox."
            ),
            de=(
                "Alltagsassistent, der Ihr Wissen durchsucht, angehängte Dateien liest, sich merkt, was Ihnen "
                "wichtig ist, und bei aktiviertem Code Interpreter mit Dateien in Ihrer Sandbox arbeitet."
            ),
            fr=(
                "Assistant du quotidien qui recherche dans vos connaissances, lit les fichiers joints, retient ce "
                "qui compte pour vous et, avec Code Interpreter activé, travaille sur les fichiers de votre bac à "
                "sable."
            ),
            it=(
                "Assistente quotidiano che cerca nella vostra conoscenza, legge i file allegati, ricorda ciò che "
                "conta per voi e, con Code Interpreter attivo, lavora con i file nella vostra sandbox."
            ),
        ),
        icon="mdi:briefcase-outline",
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.2, timeout=120.0),
        ),
        knowledge_tool=KnowledgeToolConfig(every_readable_collection=True),
        user_memory=UserMemoryConfig(memory_llm="text-generation/gemma-4-31B-it"),
        org_memory=None,
    )
