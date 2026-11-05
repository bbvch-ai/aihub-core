"""Profile templates offered in the Admin UI's Templates tab.

The Jira connection must stay empty in every template. `Form.to_template_data` filters on `get_configurable_fields()`,
which walks top-level fields only, so the whole `jira` group is dumped into the template, broadcast in the discovery
event and rendered in the Admin UI. A URL, an e-mail or a token set here would travel with it.
"""

from swiss_ai_hub.agent.agents.release_notes_agent import ReleaseNotesAgentConfig


def get_all_templates() -> list[ReleaseNotesAgentConfig]:
    from .customer_release_notes import build as build_customer_release_notes

    return [
        build_customer_release_notes(),
    ]
