import json
import re
from pathlib import Path
from typing import Any

import pytest

from swiss_ai_hub.core.jira.jira_ticket import JiraTicket

_RECORDED = Path(__file__).parent / "recorded"


def _recorded(name: str) -> dict[str, Any]:
    """Search hits recorded from Jira Cloud and Data Center 11.3 with the fields a ticket search asks for; only the
    site names were replaced."""
    return json.loads((_RECORDED / f"{name}.json").read_text())


class TestDescription:
    @pytest.mark.parametrize("edition", ["cloud", "data_center"])
    def test_rich_text_comes_back_as_readable_markdown(self, edition: str):
        description = JiraTicket.from_search_hit(_recorded(f"{edition}_rich_formatting")).description

        assert description.startswith("## Steps to reproduce\n\n1. Open the login page")
        assert "2. Enter a valid user and a **wrong** password\n   1. Wait for the error message" in description
        assert "| Browser | Firefox 131 |" in description
        assert "```\nint attempts = 0;" in description
        assert "[the handbook](https://example.com/handbook)" in description

    @pytest.mark.parametrize("edition", ["cloud", "data_center"])
    def test_no_markup_or_rich_text_json_reaches_the_text(self, edition: str):
        description = JiraTicket.from_search_hit(_recorded(f"{edition}_rich_formatting")).description

        assert not re.search(r"</?[a-z][^>]*>", description)
        assert '"type"' not in description
        assert "h2." not in description

    def test_the_wiki_text_stands_in_when_jira_rendered_nothing(self):
        hit = _recorded("data_center_rich_formatting")
        del hit["renderedFields"]

        assert JiraTicket.from_search_hit(hit).description.startswith("h2. Steps to reproduce")

    def test_no_description_gives_an_empty_text(self):
        hit = _recorded("cloud_metadata")
        hit["fields"]["description"] = None
        hit["renderedFields"]["description"] = None

        assert JiraTicket.from_search_hit(hit).description == ""


class TestFields:
    @pytest.mark.parametrize("edition", ["cloud", "data_center"])
    def test_type_status_labels_components_and_fix_versions_are_names(self, edition: str):
        ticket = JiraTicket.from_search_hit(_recorded(f"{edition}_metadata"))

        assert (ticket.issue_type, ticket.status) == ("Story", "In Progress")
        assert ticket.components == ["API", "Frontend"]
        assert ticket.fix_versions == ["1.0"]
        assert "release-1" in ticket.labels
        assert ticket.labels == sorted(ticket.labels)

    def test_the_link_keeps_a_data_center_context_path(self):
        ticket = JiraTicket.from_search_hit(_recorded("data_center_metadata"))

        assert (ticket.key, ticket.project, ticket.url) == ("ENG-9", "ENG", "https://jira.acme.ch/jira/browse/ENG-9")

    def test_the_link_points_at_the_cloud_site(self):
        ticket = JiraTicket.from_search_hit(_recorded("cloud_metadata"))

        assert ticket.url == "https://acme.atlassian.net/browse/ENG-20"

    def test_the_search_asks_for_no_field_naming_a_person(self):
        assert not {"reporter", "assignee", "creator"} & set(JiraTicket.FIELDS)
