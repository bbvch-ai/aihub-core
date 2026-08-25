"""Profile templates offered in the Admin UI's Templates tab.

Mailbox credentials must stay empty in every template. `Form.to_template_data` filters on
`get_configurable_fields()`, which walks top-level fields only — `imap` is a configurable group, so the whole nested
dict is dumped into the template, broadcast in the discovery event and rendered in the Admin UI. A host, username or
password set here would travel with it. The value a template carries is the category taxonomy, not the connection.
"""

from swiss_ai_hub.agent.agents.email_classification_agent import EmailClassificationAgentConfig


def get_all_templates() -> list[EmailClassificationAgentConfig]:
    from .shared_mailbox_triage import build as build_shared_mailbox_triage

    return [
        build_shared_mailbox_triage(),
    ]
