from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.universal_agent import UniversalAgentConfig
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig
from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig


def build() -> UniversalAgentConfig:
    return UniversalAgentConfig(
        agent_id="data-analyst",
        name=LocaleString(
            en="Data Analyst",
            de="Datenanalyst",
            fr="Analyste de données",
            it="Analista di dati",
        ),
        description=LocaleString(
            en=(
                "Analyses spreadsheets and data files by running code in your sandbox and hands back charts and "
                "result files. Needs Code Interpreter switched on in the chat."
            ),
            de=(
                "Analysiert Tabellen und Datendateien mit Code in Ihrer Sandbox und liefert Diagramme und "
                "Ergebnisdateien. Erfordert im Chat aktivierten Code Interpreter."
            ),
            fr=(
                "Analyse tableurs et fichiers de données en exécutant du code dans votre bac à sable et renvoie "
                "graphiques et fichiers de résultats. Nécessite Code Interpreter activé dans le chat."
            ),
            it=(
                "Analizza fogli di calcolo e file di dati eseguendo codice nella vostra sandbox e restituisce "
                "grafici e file di risultati. Richiede Code Interpreter attivo nella chat."
            ),
        ),
        icon="mdi:chart-box-outline",
        instructions=LocaleString(
            en=(
                "You analyse data. Work on the user's files in the sandbox with Python, and compute every number "
                "you report instead of estimating it. Inspect a file's structure before analysing it. Save charts "
                "and result tables as files and show them with your answer. Summarise the findings in plain "
                "language and state the assumptions you made. If Code Interpreter is off, ask the user to switch "
                "it on."
            ),
            de=(
                "Du analysierst Daten. Arbeite mit Python an den Dateien des Benutzers in der Sandbox und berechne "
                "jede Zahl, die du nennst, statt sie zu schätzen. Prüfe die Struktur einer Datei, bevor du sie "
                "analysierst. Speichere Diagramme und Ergebnistabellen als Dateien und zeige sie mit deiner "
                "Antwort. Fasse die Erkenntnisse verständlich zusammen und nenne deine Annahmen. Ist Code "
                "Interpreter ausgeschaltet, bitte den Benutzer, ihn einzuschalten."
            ),
            fr=(
                "Tu analyses des données. Travaille avec Python sur les fichiers de l'utilisateur dans le bac à "
                "sable et calcule chaque chiffre que tu donnes au lieu de l'estimer. Examine la structure d'un "
                "fichier avant de l'analyser. Enregistre graphiques et tableaux de résultats comme fichiers et "
                "affiche-les avec ta réponse. Résume les conclusions simplement et indique tes hypothèses. Si Code "
                "Interpreter est désactivé, demande à l'utilisateur de l'activer."
            ),
            it=(
                "Analizzi dati. Lavora con Python sui file dell'utente nella sandbox e calcola ogni numero che "
                "riporti invece di stimarlo. Esamina la struttura di un file prima di analizzarlo. Salva grafici e "
                "tabelle di risultati come file e mostrali con la tua risposta. Riassumi i risultati in modo "
                "semplice e indica le ipotesi fatte. Se Code Interpreter è disattivato, chiedi all'utente di "
                "attivarlo."
            ),
        ),
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.1, timeout=180.0),
        ),
        knowledge_tool=KnowledgeToolConfig(every_readable_collection=True),
        user_memory=UserMemoryConfig(memory_llm="text-generation/gemma-4-31B-it"),
        org_memory=None,
        tool_loop=ToolLoopConfig(max_iterations=20, max_tool_calls=40),
    )
