import re


def exact_match_pattern(names: list[str]) -> str:
    """
    Convert a list of exact names into a single regex pattern with alternation.
    Examples:
        >>> exact_match_pattern(["Invoices", "Contracts", "Legal"])
        '^(Invoices|Contracts|Legal)$'

        >>> exact_match_pattern(["Customer_A", "Customer_B"])
        '^(Customer_A|Customer_B)$'

        >>> exact_match_pattern(["Special.Folder", "Test[1]"])
        '^(Special\\\\.Folder|Test\\\\[1\\\\])$'
    """
    if not names:
        return ""
    escaped_names = [re.escape(name) for name in names]
    return f"^({'|'.join(escaped_names)})$"


def extension_pattern(extensions: list[str]) -> str:
    """
    Convert a list of file extensions into a regex pattern.
    Examples:
        >>> extension_pattern([".pdf", ".docx", ".xlsx"])
        '\\\\.(pdf|docx|xlsx)$'

        >>> extension_pattern(["pdf", "doc", "docx"])
        '\\\\.(pdf|doc|docx)$'

        >>> extension_pattern([".PDF", ".Doc"])
        '\\\\.(pdf|doc)$'
    """
    if not extensions:
        return ""
    # Remove leading dots and convert to lowercase for case-insensitive matching
    clean_exts = [ext.lstrip(".").lower() for ext in extensions]
    return f"\\.({'|'.join(clean_exts)})$"


def contains_pattern(substring: str) -> str:
    """
    Create a pattern that matches if the substring appears anywhere.
    Examples:
        >>> contains_pattern("archive")
        '.*archive.*'

        >>> contains_pattern("draft")
        '.*draft.*'

        >>> contains_pattern("test[1]")
        '.*test\\\\[1\\\\].*'
    """
    return f".*{re.escape(substring)}.*"


def starts_with_pattern(prefix: str) -> str:
    """
    Create a pattern that matches names starting with the given prefix.

    Examples:
        >>> starts_with_pattern("Customer_")
        '^Customer_.*'

        >>> starts_with_pattern("backup")
        '^backup.*'

        >>> starts_with_pattern("~$")
        '^~\\\\$.*'
    """
    return f"^{re.escape(prefix)}.*"


def ends_with_pattern(suffix: str) -> str:
    """
    Create a pattern that matches names ending with the given suffix.
    Examples:
        >>> ends_with_pattern("_old")
        '.*_old$'

        >>> ends_with_pattern(".tmp")
        '.*\\\\.tmp$'
    """
    return f".*{re.escape(suffix)}$"


def combine_patterns(*patterns: str) -> list[str]:
    """
    Combine multiple patterns into a list, filtering out empty ones.

    Examples:
        >>> combine_patterns(
        ...     exact_match_pattern(["A", "B"]),
        ...     starts_with_pattern("temp")
        ... )
        ['^(A|B)$', '^temp.*']

        >>> combine_patterns("", "pattern1", "", "pattern2")
        ['pattern1', 'pattern2']
    """
    return [p for p in patterns if p]
