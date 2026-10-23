from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.jira import JiraConnectionConfig

from swiss_ai_hub.agent.agents.release_notes_agent import ReleaseNotesAgentConfig
from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage


def build() -> ReleaseNotesAgentConfig:
    """Release notes for customers, in English and German, without ticket keys.

    Customers cannot open the team's Jira, so the keys are off, and sub-tasks are left out because they repeat their
    parent's change in pieces. The Jira connection and the projects are left empty on purpose — see
    `templates/__init__.py`.
    """
    return ReleaseNotesAgentConfig(
        agent_id="customer-release-notes",
        name=LocaleString(
            en="Customer Release Notes",
            de="Versionshinweise für Kunden",
            fr="Notes de version pour les clients",
            it="Note di rilascio per i clienti",
        ),
        description=LocaleString(
            en="Writes the release notes of a Jira fix version for customers, in English and German.",
            de="Schreibt die Versionshinweise einer Jira-Lösungsversion für Kunden, auf Englisch und Deutsch.",
            fr="Rédige les notes de version d'une version corrigée Jira pour les clients, en anglais et en allemand.",
            it="Scrive le note di rilascio di una versione di correzione Jira per i clienti, in inglese e tedesco.",
        ),
        icon="mdi:text-box-check-outline",
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.2, timeout=120.0),
        ),
        jira=JiraConnectionConfig(),
        project_keys=None,
        extra_jql="issuetype not in subTaskIssueTypes()",
        language=ReleaseLanguage.EN,
        translate_into=[ReleaseLanguage.DE],
        audience="customers who use the product and do not know how it is built",
        show_ticket_keys=False,
    )
