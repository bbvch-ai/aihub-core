import re


def paths_pattern(file_paths: list[str]) -> list[str]:
    """
    Match exact full paths from base_path.

    Examples:
        >>> paths_pattern(["docs/Invoices/report.pdf", "legal/Contracts/doc.docx"])
        ['^(docs/Invoices/report\\\\.pdf|legal/Contracts/doc\\\\.docx)$']

        >>> paths_pattern(["Customer_A/file.txt"])
        ['^(Customer_A/file\\\\.txt)$']
    """
    if not file_paths:
        return []
    escaped = [re.escape(path) for path in file_paths]
    return [f"^({'|'.join(escaped)})$"]


def folders_pattern(folder_names: list[str]) -> list[str]:
    """
    Match paths that contain any of the given folder names as path components.

    Examples:
        >>> folders_pattern(["Invoices", "Contracts", "Legal"])
        ['.*(^|/)(Invoices|Contracts|Legal)(/|$).*']

        This matches:
        - "Invoices/file.pdf"
        - "docs/Invoices/file.pdf"
        - "Invoices/2024/file.pdf"

        But not:
        - "MyInvoices/file.pdf" (Invoices is part of a larger name)
    """
    if not folder_names:
        return []
    escaped = [re.escape(name) for name in folder_names]
    return [f"(^|/)({'|'.join(escaped)})(/|$)"]


def extensions_pattern(exts: list[str]) -> list[str]:
    """
    Match file extensions.

    Examples:
        >>> extensions_pattern([".pdf", ".docx", ".xlsx"])
        ['\\\\.(pdf|docx|xlsx)$']

        >>> extensions_pattern(["pdf", "doc", "docx"])
        ['\\\\.(pdf|doc|docx)$']

        >>> extensions_pattern([".PDF", ".Doc"])
        ['\\\\.(pdf|doc)$']
    """
    if not exts:
        return []
    clean = [ext.lstrip(".").lower() for ext in exts]
    return [f"\\.({'|'.join(clean)})$"]


def contains_pattern(substrings: list[str]) -> list[str]:
    """
    Match if any substring appears anywhere in the path.

    Examples:
        >>> contains_pattern(["archive", "backup"])
        ['.*(archive|backup).*']

        >>> contains_pattern(["draft"])
        ['.*draft.*']

        >>> contains_pattern(["test[1]"])
        ['.*test\\\\[1\\\\].*']
    """
    if not substrings:
        return []
    escaped = [re.escape(s) for s in substrings]
    return [f".*({'|'.join(escaped)}).*"]


def starts_with_pattern(prefixes: list[str]) -> list[str]:
    """
    Match paths starting with any of the given prefixes.

    Examples:
        >>> starts_with_pattern(["docs/", "legal/"])
        ['^(docs/|legal/).*']

        >>> starts_with_pattern(["backup", "temp"])
        ['^(backup|temp).*']

        >>> starts_with_pattern(["~$"])
        ['^(~\\\\$).*']
    """
    if not prefixes:
        return []
    escaped = [re.escape(p) for p in prefixes]
    return [f"^({'|'.join(escaped)}).*"]


def suffixes_pattern(suffixes_list: list[str]) -> list[str]:
    """
    Match paths ending with any suffix (for non-extension endings like '_old', '_backup').

    Examples:
        >>> suffixes_pattern(["_old", "_backup"])
        ['.*((_old)|(_backup))$']

        >>> suffixes_pattern(["/draft"])
        ['.*(/draft)$']
    """
    if not suffixes_list:
        return []
    escaped = [re.escape(s) for s in suffixes_list]
    return [f".*({'|'.join(escaped)})$"]
