from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.imap import EmailClassificationSettings, ImapClientConfig, MailCategory

from swiss_ai_hub.agent.agents.email_classification_agent import EmailClassificationAgentConfig

_CATEGORIES = [
    MailCategory(
        category="information_request",
        imap_folder="Triage/Information",
        description=(
            "The sender is asking for information we can simply provide — pricing, opening hours, documentation, "
            "where to find something. Answering needs no action beyond telling them."
        ),
    ),
    MailCategory(
        category="support_request",
        imap_folder="Triage/Support",
        description=(
            "Something is broken or blocked for the sender and resolving it requires an action from our team, not "
            "just an explanation."
        ),
    ),
    MailCategory(
        category="invoice",
        imap_folder="Triage/Invoices",
        description=("A bill, invoice, receipt, payment reminder or dunning notice, whether in the body or attached."),
    ),
]


def build() -> EmailClassificationAgentConfig:
    """A shared mailbox that sorts itself into three folders.

    The first two categories are deliberately adjacent: `Information` and `Support` cannot be told apart from their
    folder names, only from their descriptions. That is the premise of the whole blueprint, so a template whose
    categories were mutually obvious would demonstrate nothing.

    The mailbox fields are left empty on purpose — see `templates/__init__.py`.
    """
    return EmailClassificationAgentConfig(
        agent_id="shared-mailbox-triage",
        name=LocaleString(
            en="Shared Mailbox Triage",
            de="Sortierung eines gemeinsamen Postfachs",
            fr="Tri d'une boîte partagée",
            it="Smistamento casella condivisa",
        ),
        description=LocaleString(
            en="Sorts unread mail in a shared mailbox into folders for information requests, support and invoices.",
            de="Sortiert ungelesene E-Mails eines gemeinsamen Postfachs in Ordner für Auskünfte, Support und "
            "Rechnungen.",
            fr="Trie les messages non lus d'une boîte partagée en dossiers demandes d'information, support et "
            "factures.",
            it="Smista la posta non letta di una casella condivisa in cartelle per informazioni, supporto e fatture.",
        ),
        icon="mage:folder-check",
        imap=ImapClientConfig(host="", username="", password=""),
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.0, timeout=60.0),
        ),
        classification=EmailClassificationSettings(
            categories=_CATEGORIES,
            fallback_folder="Triage/Uncategorised",
        ),
    )
