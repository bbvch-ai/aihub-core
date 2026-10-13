class MalformedFrontmatterError(ValueError):
    """A markdown file opens with a frontmatter block that is not a YAML mapping.

    Raised rather than applying whatever could be read: the caller then ingests the file exactly as it was written, so
    a broken block is never half-applied as metadata.
    """
