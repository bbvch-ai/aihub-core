import time
from datetime import date

import pytest
from swiss_ai_hub.core.jira import JiraVersion

from swiss_ai_hub.agent.agents.release_notes_agent.release_version_matcher import ReleaseVersionMatcher
from swiss_ai_hub.agent.agents.release_notes_agent.version_match_outcome import VersionMatchOutcome


def _versions(*names: str, project: str = "ENG") -> list[JiraVersion]:
    return [JiraVersion(id=str(10000 + index), name=name, project=project) for index, name in enumerate(names)]


@pytest.mark.parametrize(
    "message",
    [
        "Release notes for 2.0",
        "release notes for “2.0”, please",
        'notes for "2.0"',
        "What changed in 2.0?",
        "what changed in 2.0.",
        "notes for v2.0",
        "notes for ２.０",
        "2.0",
    ],
)
def test_a_message_naming_one_version_finds_it(message: str):
    match = ReleaseVersionMatcher.match(message, _versions("1.0", "2.0", "2026-Q3"))

    assert match.outcome is VersionMatchOutcome.FOUND
    assert match.name == "2.0"


def test_names_are_matched_whatever_their_case():
    match = ReleaseVersionMatcher.match("release notes for 2026-q3 BETA", _versions("2026-Q3 Beta"))

    assert match.outcome is VersionMatchOutcome.FOUND
    assert match.name == "2026-Q3 Beta"


def test_chat_clients_curly_apostrophes_still_match_a_straight_one():
    match = ReleaseVersionMatcher.match("notes for Spring ’26", _versions("Spring '26"))

    assert match.outcome is VersionMatchOutcome.FOUND


def test_a_shorter_version_is_not_found_inside_a_longer_one():
    versions = _versions("2.4", "2.4.0")

    assert ReleaseVersionMatcher.match("notes for 2.4.0", versions).name == "2.4.0"
    assert ReleaseVersionMatcher.match("notes for 2.4", versions).name == "2.4"
    assert ReleaseVersionMatcher.match("notes for 2.4.", versions).name == "2.4"


def test_a_name_inside_a_longer_name_does_not_count_as_a_second_release():
    match = ReleaseVersionMatcher.match("notes for 2.0 Beta", _versions("2.0", "2.0 Beta"))

    assert match.outcome is VersionMatchOutcome.FOUND
    assert match.name == "2.0 Beta"


def test_a_name_shared_by_two_projects_is_one_release_of_both():
    versions = [*_versions("2.0", project="ENG"), *_versions("2.0", project="SD")]

    match = ReleaseVersionMatcher.match("notes for 2.0", versions)

    assert match.outcome is VersionMatchOutcome.FOUND
    assert [version.project for version in match.versions] == ["ENG", "SD"]


def test_several_names_are_reported_in_the_order_the_message_names_them():
    match = ReleaseVersionMatcher.match("compare 2.0 with 1.0", _versions("1.0", "2.0"))

    assert match.outcome is VersionMatchOutcome.SEVERAL
    assert match.names == ["2.0", "1.0"]


def test_an_unknown_version_suggests_the_closest_names():
    match = ReleaseVersionMatcher.match("release notes for 2.4", _versions("1.0", "2.4.0", "2026-Q3"))

    assert match.outcome is VersionMatchOutcome.UNKNOWN
    assert match.requested == "2.4"
    assert match.suggestions[0] == "2.4.0"


def test_a_long_word_without_a_digit_does_not_stall_the_reply():
    """Only a word with a digit can name a version; a pasted run of letters once backtracked quadratically."""
    started = time.perf_counter()

    match = ReleaseVersionMatcher.match("notes for " + "x" * 200_000, _versions("1.0"))

    assert match.outcome is VersionMatchOutcome.MISSING
    assert time.perf_counter() - started < 5


def test_a_long_paste_after_the_request_does_not_stall_the_reply():
    """Matched in full, a pasted changelog naming many known versions took seconds on the event loop."""
    names = [f"{number // 100}.{(number // 10) % 10}.{number % 10}" for number in range(500)]
    paste = "\n".join(f"- fixed in {name}" for name in names * 24)
    message = f"Release notes for 4.9.9, the old changelog is below\n{paste}"
    started = time.perf_counter()

    match = ReleaseVersionMatcher.match(message, _versions(*names))

    assert time.perf_counter() - started < 1
    assert match.outcome is VersionMatchOutcome.SEVERAL
    assert match.names[0] == "4.9.9"


def test_a_version_named_only_after_the_start_of_a_long_message_is_not_found():
    filler = "x " * (ReleaseVersionMatcher.SEARCHED_CHARS // 2)

    match = ReleaseVersionMatcher.match(f"{filler}notes for 1.0", _versions("1.0"))

    assert match.outcome is VersionMatchOutcome.MISSING


def test_a_version_cut_at_the_limit_is_not_read_as_a_shorter_one():
    message = "x" * (ReleaseVersionMatcher.SEARCHED_CHARS - 4) + " 2.4.0 please"

    match = ReleaseVersionMatcher.match(message, _versions("2.4", "2.4.0"))

    assert match.outcome is VersionMatchOutcome.MISSING


def test_a_version_is_not_found_inside_a_longer_number():
    match = ReleaseVersionMatcher.match("notes for 11.0", _versions("1.0"))

    assert match.outcome is VersionMatchOutcome.UNKNOWN
    assert match.requested == "11.0"


def test_an_unknown_version_with_no_close_name_offers_the_recent_ones():
    match = ReleaseVersionMatcher.match("notes for 9.9.9", _versions("Alpha", "Beta"))

    assert match.outcome is VersionMatchOutcome.UNKNOWN
    assert match.requested == "9.9.9"
    assert match.suggestions == []
    assert match.recent == ["Beta", "Alpha"]


def test_a_message_without_a_version_offers_the_newest_live_versions():
    versions = [
        JiraVersion(id="1", name="1.0", project="ENG", released=True, archived=True, release_date=date(2025, 1, 1)),
        JiraVersion(id="2", name="1.1", project="ENG", released=True, release_date=date(2025, 6, 1)),
        JiraVersion(id="3", name="2.0", project="ENG", released=True, release_date=date(2026, 3, 1)),
        JiraVersion(id="4", name="2.1", project="ENG"),
        JiraVersion(id="5", name="3.0", project="ENG"),
    ]

    match = ReleaseVersionMatcher.match("write the release notes", versions)

    assert match.outcome is VersionMatchOutcome.MISSING
    assert match.recent == ["3.0", "2.1", "2.0", "1.1"]


def test_the_recent_versions_are_at_most_five_distinct_names():
    versions = [*_versions(*(f"1.{minor}" for minor in range(8))), *_versions("1.7", project="SD")]

    match = ReleaseVersionMatcher.match("release notes please", versions)

    assert match.recent == ["1.7", "1.6", "1.5", "1.4", "1.3"]


def test_projects_without_versions_leave_nothing_to_offer():
    match = ReleaseVersionMatcher.match("release notes please", [])

    assert match.outcome is VersionMatchOutcome.MISSING
    assert match.recent == []


def test_versions_of_several_projects_are_offered_newest_first():
    """As listed on the Cloud test site: no release dates, ENG's versions before SD's."""
    versions = [
        JiraVersion(id="10000", name="1.0", project="ENG", released=True),
        JiraVersion(id="10001", name="1.1", project="ENG"),
        JiraVersion(id="10004", name="2.0", project="ENG"),
        JiraVersion(id="10002", name="2026-Q3", project="SD", released=True),
        JiraVersion(id="10003", name="1.0", project="SD"),
    ]

    assert ReleaseVersionMatcher.match("release notes please", versions).recent == ["2.0", "1.0", "2026-Q3", "1.1"]
