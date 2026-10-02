from datetime import UTC, datetime

import pytest
import yaml
from pydantic import ValidationError
from swiss_ai_hub.core.persistence import NamespaceEntity

from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile


def _record(**overrides) -> StructuredRecordFile:
    fields = {
        "namespace": "ABC",
        "path_segments": ["ABC-1"],
        "frontmatter": {"title": "Login fails", "url": "https://jira.test/browse/ABC-1", "status": "Open"},
        "body": "The login page fails.",
    }
    return StructuredRecordFile(**{**fields, **overrides})


class TestRender:
    def test_the_same_record_renders_to_the_same_bytes_whatever_the_field_order(self):
        """The destination skips unchanged files by hash, so rendering must not depend on how fields were built."""
        reordered = _record(
            frontmatter={"status": "Open", "url": "https://jira.test/browse/ABC-1", "title": "Login fails"}
        )

        assert _record().render() == reordered.render()

    def test_the_frontmatter_leads_and_the_body_follows(self):
        text = _record().render().decode()

        header, body = text.removeprefix("---\n").split("---\n\n", 1)
        assert yaml.safe_load(header) == {
            "status": "Open",
            "title": "Login fails",
            "url": "https://jira.test/browse/ABC-1",
        }
        assert body == "The login page fails.\n"

    def test_unset_fields_are_left_out_and_no_fields_means_no_frontmatter(self):
        assert b"assignee" not in _record(frontmatter={"title": "T", "assignee": None}).render()
        assert _record(frontmatter={}).render() == b"The login page fails.\n"

    def test_lists_and_non_latin_text_survive_as_written(self):
        text = _record(frontmatter={"title": "Übersicht", "labels": ["auth", "ui"]}).render().decode()

        assert "title: Übersicht" in text
        assert yaml.safe_load(text.split("---\n")[1])["labels"] == ["auth", "ui"]

    def test_a_date_must_arrive_as_an_iso_string(self):
        """A datetime would render in YAML's own spelling, not the ISO-8601 the metadata reader expects."""
        with pytest.raises(ValidationError):
            _record(frontmatter={"updated": datetime(2026, 9, 1, tzinfo=UTC)})


class TestObjectKey:
    def test_the_namespace_folder_is_named_exactly_like_its_namespace(self):
        record = _record(namespace="HR docs/2026", path_segments=["Policy"])

        assert record.namespace == NamespaceEntity.sanitize_namespace_name("HR docs/2026")
        assert record.object_key == "HR_docs_2026/Policy.md"

    def test_folders_below_the_namespace_keep_their_order(self):
        record = _record(namespace="DOC", path_segments=["Handbook", "Onboarding", "First day"])

        assert record.object_key == "DOC/Handbook/Onboarding/First day.md"

    def test_a_slash_or_control_character_in_a_title_cannot_add_a_folder(self):
        record = _record(path_segments=["Q1/Q2 plan\\draft\x00"])

        assert record.object_key == "ABC/Q1_Q2 plan_draft_.md"

    def test_a_listing_builds_exactly_the_key_the_record_is_written_under(self):
        """A listed key that differs from the written one would make the removal delete that record for good."""
        written = _record(namespace="My Project", path_segments=["Q1/Q2 plan"])

        assert StructuredRecordFile.object_key_for("My Project", ["Q1/Q2 plan"]) == written.object_key
        assert written.object_key == "My_Project/Q1_Q2 plan.md"

    def test_an_overlong_title_is_capped(self):
        record = _record(path_segments=["x" * 500])

        assert record.object_key == f"ABC/{'x' * 120}.md"

    @pytest.mark.parametrize("namespace", ["", "   "])
    def test_a_record_without_a_namespace_is_rejected(self, namespace: str):
        """Root-level objects are never ingested, so such a record would silently go missing."""
        with pytest.raises(ValidationError, match="namespace"):
            _record(namespace=namespace)

    @pytest.mark.parametrize("segments", [[], [""], ["   "], [".."], ["Folder", "."]])
    def test_an_empty_or_relative_path_is_rejected(self, segments: list[str]):
        with pytest.raises(ValidationError):
            _record(path_segments=segments)
