"""Tests for quality_validator module."""

from aihub_lib.generative_ai.document.refinement.quality_validator import (
    QualityValidationResult,
    RepetitionIssue,
    _detect_phrase_repetition,
    _detect_repetition_bugs,
    validate_document_quality,
)


class TestValidateDocumentQuality:
    """Tests for validate_document_quality function."""

    def test_short_document_skipped(self) -> None:
        """Test that very short documents skip validation."""
        text = "Short text"
        result = validate_document_quality(text)

        assert result.is_valid is True
        assert result.validation_skipped is True
        assert result.has_repetition_bug is False
        assert len(result.repetition_issues) == 0

    def test_normal_document_passes(self) -> None:
        """Test that normal documents pass validation."""
        # Create a document with varied content (each paragraph is unique)
        paragraphs = [
            f"This is paragraph number {i}. It discusses topic {i * 7 % 13} in detail. "
            f"The content here is specific to section {i} of the document."
            for i in range(50)
        ]
        text = "\n\n".join(paragraphs)

        result = validate_document_quality(text)

        assert result.is_valid is True
        assert result.validation_skipped is False
        assert result.has_repetition_bug is False

    def test_repeated_lines_detected(self) -> None:
        """Test that excessive line repetition is detected (like the eMail info@ bug)."""
        # Simulate the actual Docling bug with repeated email lines
        repeated_line = "eMail info@example.com"
        normal_content = "This is the introduction to the document.\n\n"
        normal_content += "Some more content here.\n\n"

        # Add the repeated pattern many times (simulating parsing bug)
        repeated_section = "\n".join([repeated_line] * 100)

        text = normal_content + repeated_section

        result = validate_document_quality(text)

        assert result.is_valid is False
        assert result.has_repetition_bug is True
        assert len(result.repetition_issues) > 0
        assert "eMail" in result.repetition_issues[0].pattern

    def test_moderate_repetition_allowed(self) -> None:
        """Test that moderate repetition (like headers/footers) is allowed."""
        # Some documents legitimately have repeated content (page headers)
        header = "Company Name - Confidential"
        paragraphs = []
        for i in range(10):
            paragraphs.append(header)  # Header appears 10 times
            paragraphs.append(f"Page {i} content with substantial unique text here. " * 5)

        text = "\n\n".join(paragraphs)

        result = validate_document_quality(text)

        # 10 repetitions of a short header shouldn't trigger the bug detector
        assert result.is_valid is True

    def test_returns_proper_result_type(self) -> None:
        """Test that the function returns proper Pydantic models."""
        text = "A" * 1000  # Enough to not skip validation

        result = validate_document_quality(text)

        assert isinstance(result, QualityValidationResult)
        assert isinstance(result.repetition_issues, list)
        for issue in result.repetition_issues:
            assert isinstance(issue, RepetitionIssue)


class TestDetectRepetitionBugs:
    """Tests for _detect_repetition_bugs function."""

    def test_no_repetition(self) -> None:
        """Test detection with no repetitive content."""
        text = "This is a unique sentence. Another different sentence. More varied content."

        issues = _detect_repetition_bugs(text)

        assert len(issues) == 0

    def test_line_repetition_detected(self) -> None:
        """Test that repeated lines are detected."""
        repeated = "This exact line repeats\n" * 50
        text = "Normal start\n" + repeated + "Normal end"

        issues = _detect_repetition_bugs(text)

        assert len(issues) > 0
        assert issues[0].count >= 20

    def test_short_patterns_ignored(self) -> None:
        """Test that very short repeated patterns are ignored."""
        # "a " repeated many times - too short to be meaningful
        text = "a " * 200 + "Some normal content here. " * 20

        issues = _detect_repetition_bugs(text)

        # Short patterns shouldn't be flagged (they might be spacing/formatting)
        line_issues = [i for i in issues if len(i.pattern.strip()) < 10]
        assert len(line_issues) == 0


class TestDetectPhraseRepetition:
    """Tests for _detect_phrase_repetition function."""

    def test_paragraph_separated_repetition(self) -> None:
        """Test detection of phrases repeated across paragraphs."""
        # Pattern that appears in separate paragraphs (like the eMail bug)
        phrase = "eMail info@ repeated text here"
        text = "\n\n".join([phrase] * 50)

        issues = _detect_phrase_repetition(text)

        assert len(issues) > 0

    def test_unique_text_no_issues(self) -> None:
        """Test that varied text produces no phrase issues."""
        # Each paragraph is completely unique
        paragraphs = [
            f"Paragraph {i} contains entirely different information about subject {i * 3}." for i in range(30)
        ]
        text = "\n\n".join(paragraphs)

        issues = _detect_phrase_repetition(text)

        assert len(issues) == 0

    def test_ratio_threshold_respected(self) -> None:
        """Test that patterns must consume significant portion of text."""
        # Small amount of repetition in large document with unique paragraphs
        unique_paragraphs = [
            f"This is unique paragraph {i} with completely different content about topic {i}." for i in range(50)
        ]
        # Add a few repeated paragraphs (but not enough to trigger threshold)
        repeated_para = "This paragraph appears a few times."
        paragraphs = unique_paragraphs + [repeated_para] * 10  # Only 10 repetitions

        text = "\n\n".join(paragraphs)

        issues = _detect_phrase_repetition(text)

        # Low count and low ratio repetition shouldn't be flagged
        assert len(issues) == 0


class TestRealWorldScenarios:
    """Tests based on real-world parsing bug scenarios."""

    def test_email_repetition_bug(self) -> None:
        """Test detection of the actual eMail info@ bug from logs."""
        # Recreate the actual bug pattern from the pipeline logs
        email_pattern = "eMail info@\n\n"
        text = "Inhaltsverzeichnis\n\n"
        text += "1 Ersatzteilliste\n\n"
        text += "Hinweis für Ersatzteilbestellungen\n\n"
        text += email_pattern * 100  # The bug caused hundreds of repetitions
        text += "Normal content after the bug.\n"

        result = validate_document_quality(text)

        assert result.is_valid is False
        assert result.has_repetition_bug is True
        assert "Parsing bug detected" in result.message

    def test_image_description_repetition(self) -> None:
        """Test detection of repeated image descriptions (another bug pattern)."""
        # Sometimes Docling repeats image alt-text excessively
        img_desc = "![Das Bild zeigt einen gelben Brückenkran](image.png)"
        text = "\n\n".join([img_desc] * 40)

        result = validate_document_quality(text)

        assert result.is_valid is False
        assert result.has_repetition_bug is True

    def test_legitimate_list_not_flagged(self) -> None:
        """Test that legitimate repeated structures (like forms) aren't flagged."""
        # Some documents have legitimate repetitive structures
        # Key: Each item line is UNIQUE (Item 0, Item 1, etc.)
        items = []
        for i in range(15):
            items.append(f"Item {i}: Product name here")
            items.append(f"Quantity for item {i}: 5 units")
            items.append(f"Price for item {i}: $10.00")

        text = "\n".join(items)

        result = validate_document_quality(text)

        # This is a form with repeated structure but different content - should pass
        # The line-based detection should see each line as unique
        assert result.is_valid is True
