from datetime import date

from swiss_ai_hub.core.jira.jira_version import JiraVersion


class TestFromAnswer:
    def test_a_released_version_carries_its_date(self):
        answer = {"id": 10200, "name": "2.4.0", "released": True, "archived": False, "releaseDate": "2026-10-20"}

        version = JiraVersion.from_answer(answer, "ENG")

        assert version == JiraVersion(
            id="10200", name="2.4.0", project="ENG", released=True, archived=False, release_date=date(2026, 10, 20)
        )

    def test_a_version_without_flags_or_date_is_planned(self):
        version = JiraVersion.from_answer({"id": "10201", "name": "2026-Q3"}, "SD")

        assert (version.released, version.archived, version.release_date) == (False, False, None)
