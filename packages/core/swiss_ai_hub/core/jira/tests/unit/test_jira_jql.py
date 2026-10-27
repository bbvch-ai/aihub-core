import pytest

from swiss_ai_hub.core.jira.jira_invalid_query_error import JiraInvalidQueryError
from swiss_ai_hub.core.jira.jira_jql import JiraJql
from swiss_ai_hub.core.jira.jira_version import JiraVersion


class TestStringLiteral:
    def test_a_plain_value_is_quoted(self):
        assert JiraJql.string_literal("2.4.0") == '"2.4.0"'

    def test_a_value_from_a_chat_message_cannot_widen_the_query(self):
        """Unescaped, the quote would close the value and ``OR project = HR`` would become part of the query."""
        literal = JiraJql.string_literal('1.0" OR project = HR OR fixVersion = "')

        assert literal == '"1.0\\" OR project = HR OR fixVersion = \\""'

    @pytest.mark.parametrize(
        ("value", "literal"),
        [("a\\b", '"a\\\\b"'), ("line\nbreak", '"line\\nbreak"'), ("tab\there", '"tab\\there"'), ("cr\r", '"cr\\r"')],
    )
    def test_backslashes_and_control_characters_are_escaped(self, value: str, literal: str):
        assert JiraJql.string_literal(value) == literal


class TestCompose:
    def test_projects_and_each_clause_are_joined_with_and(self):
        jql = JiraJql.compose(["ENG", "SD"], ['issuetype != "Sub-task"', 'fixVersion = "2.4.0"'])

        assert jql == 'project in ("ENG", "SD") AND (issuetype != "Sub-task") AND (fixVersion = "2.4.0")'

    def test_an_or_in_a_clause_stays_inside_its_parentheses(self):
        jql = JiraJql.compose(["ENG"], ['labels = "a" OR labels = "b"'])

        assert jql == 'project in ("ENG") AND (labels = "a" OR labels = "b")'

    def test_empty_clauses_are_skipped(self):
        assert JiraJql.compose(["ENG"], ["", "   "]) == 'project in ("ENG")'

    def test_order_by_is_refused_because_the_search_orders_itself(self):
        with pytest.raises(JiraInvalidQueryError, match="must not contain ORDER BY"):
            JiraJql.compose(["ENG"], ["status = Done order  by created"])


class TestFixVersionClause:
    def test_versions_are_matched_by_id(self):
        versions = [
            JiraVersion(id="10200", name="2.4.0", project="ENG"),
            JiraVersion(id="10305", name="2.4.0", project="SD"),
        ]

        assert JiraJql.fix_version_clause(versions) == "fixVersion in (10200, 10305)"

    def test_an_id_that_is_not_a_number_is_refused(self):
        versions = [JiraVersion(id="1) OR (project = HR", name="x", project="ENG")]

        with pytest.raises(ValueError):
            JiraJql.fix_version_clause(versions)

    def test_no_version_is_refused(self):
        with pytest.raises(ValueError, match="at least one version"):
            JiraJql.fix_version_clause([])
