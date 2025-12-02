"""Document quality validation for detecting parsing bugs.

Detects severe parsing failures that require document re-parsing, such as:
- Excessive text repetition (parsing loops)
- Abnormal character distributions (severe encoding failures)

This is NOT for normal OCR mistakes which are handled by text refinement.
"""

import logging
import re
from collections import Counter
from typing import Annotated

from pydantic import BaseModel, Field

_logger = logging.getLogger(__name__)

# Thresholds for detecting parsing bugs (tuned to catch severe issues only)
_MIN_TEXT_LENGTH_FOR_VALIDATION = 500  # Don't validate very short documents
_REPETITION_PATTERN_MIN_LENGTH = 10  # Minimum pattern length to consider
_REPETITION_COUNT_THRESHOLD = 20  # Pattern must repeat this many times to be a bug
_REPETITION_RATIO_THRESHOLD = 0.3  # Repeated content must be >30% of total text


class RepetitionIssue(BaseModel):
    """Details about a detected repetition pattern."""

    pattern: Annotated[str, Field(description="The repeated text pattern (truncated)")]
    count: Annotated[int, Field(description="Number of times the pattern repeats")]
    total_chars: Annotated[int, Field(description="Total characters consumed by repetitions")]
    ratio: Annotated[float, Field(description="Ratio of document consumed by this pattern")]


class QualityValidationResult(BaseModel):
    """Result of document quality validation."""

    is_valid: Annotated[bool, Field(description="True if document passed validation")]
    has_repetition_bug: Annotated[bool, Field(description="True if excessive repetition detected")]
    repetition_issues: Annotated[list[RepetitionIssue], Field(description="Detected repetition patterns")]
    validation_skipped: Annotated[bool, Field(description="True if document too short to validate")]
    message: Annotated[str, Field(description="Human-readable validation summary")]


def validate_document_quality(text: str) -> QualityValidationResult:
    """Validate document text for severe parsing bugs.

    This function detects parsing failures that produce garbage output,
    such as infinite loops in the parser producing repeated text.

    It does NOT flag normal OCR errors like:
    - Misrecognized characters (rn → m, l → 1)
    - Broken words across lines
    - Minor encoding issues

    These are handled by the text refinement step.

    Returns validation result indicating if document needs re-parsing.
    """
    if len(text) < _MIN_TEXT_LENGTH_FOR_VALIDATION:
        return QualityValidationResult(
            is_valid=True,
            has_repetition_bug=False,
            repetition_issues=[],
            validation_skipped=True,
            message="Document too short for quality validation",
        )

    repetition_issues = _detect_repetition_bugs(text)
    has_repetition_bug = len(repetition_issues) > 0

    if has_repetition_bug:
        patterns_summary = ", ".join(f"'{issue.pattern[:30]}...' ({issue.count}x)" for issue in repetition_issues[:3])
        message = (
            f"Parsing bug detected: excessive repetition of {len(repetition_issues)} pattern(s): {patterns_summary}"
        )
    else:
        message = "Document passed quality validation"

    return QualityValidationResult(
        is_valid=not has_repetition_bug,
        has_repetition_bug=has_repetition_bug,
        repetition_issues=repetition_issues,
        validation_skipped=False,
        message=message,
    )


def _detect_repetition_bugs(text: str) -> list[RepetitionIssue]:
    """Detect excessive text repetition indicating parsing bugs.

    Uses multiple strategies to find repeated patterns:
    1. Line-based repetition (same line repeated many times)
    2. Phrase-based repetition (same phrase/sentence repeated)

    Only flags patterns that:
    - Repeat many times (>20 by default)
    - Consume significant portion of document (>30%)
    """
    issues: list[RepetitionIssue] = []

    # Strategy 1: Line-based repetition detection
    lines = text.split("\n")
    line_counts = Counter(line.strip() for line in lines if len(line.strip()) >= _REPETITION_PATTERN_MIN_LENGTH)

    for line, count in line_counts.most_common(10):
        if count < _REPETITION_COUNT_THRESHOLD:
            continue

        total_chars = len(line) * count
        ratio = total_chars / len(text)

        if ratio >= _REPETITION_RATIO_THRESHOLD:
            _logger.warning(f"Repetition bug detected: line '{line[:50]}...' repeated {count} times ({ratio:.1%})")
            issues.append(
                RepetitionIssue(
                    pattern=line[:100],  # Truncate for storage
                    count=count,
                    total_chars=total_chars,
                    ratio=ratio,
                )
            )

    # Strategy 2: Phrase-based repetition (for patterns not on separate lines)
    # Look for repeated sequences that might span multiple lines
    phrase_issues = _detect_phrase_repetition(text)
    issues.extend(phrase_issues)

    return issues


def _detect_phrase_repetition(text: str) -> list[RepetitionIssue]:
    """Detect repeated phrases that may span lines.

    This catches patterns like "eMail info@\\n\\neMail info@" that appear
    as separate paragraphs but are clearly parsing artifacts.

    Key insight: We look for EXACT repeated blocks (paragraphs/sentences),
    not arbitrary substrings. This avoids false positives from common phrases.
    """
    issues: list[RepetitionIssue] = []

    # Split by paragraph breaks to find repeated paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # Count exact paragraph repetitions
    para_counts = Counter(paragraphs)

    for para, count in para_counts.most_common(10):
        if len(para) < _REPETITION_PATTERN_MIN_LENGTH:
            continue
        if count < _REPETITION_COUNT_THRESHOLD:
            continue

        total_chars = len(para) * count
        ratio = total_chars / len(text)

        if ratio >= _REPETITION_RATIO_THRESHOLD:
            _logger.warning(f"Repetition bug detected: paragraph '{para[:50]}...' repeated {count} times ({ratio:.1%})")
            issues.append(
                RepetitionIssue(
                    pattern=para[:100],
                    count=count,
                    total_chars=total_chars,
                    ratio=ratio,
                )
            )

    # Also check for repeated sentences within paragraphs
    # Split by sentence endings
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentence_counts = Counter(s.strip() for s in sentences if len(s.strip()) >= _REPETITION_PATTERN_MIN_LENGTH)

    for sentence, count in sentence_counts.most_common(10):
        if count < _REPETITION_COUNT_THRESHOLD:
            continue

        total_chars = len(sentence) * count
        ratio = total_chars / len(text)

        # Check if this is already covered by paragraph detection
        already_found = any(sentence in issue.pattern or issue.pattern in sentence for issue in issues)
        if already_found:
            continue

        if ratio >= _REPETITION_RATIO_THRESHOLD:
            _logger.warning(
                f"Repetition bug detected: sentence '{sentence[:50]}...' repeated {count} times ({ratio:.1%})"
            )
            issues.append(
                RepetitionIssue(
                    pattern=sentence[:100],
                    count=count,
                    total_chars=total_chars,
                    ratio=ratio,
                )
            )

    return issues
