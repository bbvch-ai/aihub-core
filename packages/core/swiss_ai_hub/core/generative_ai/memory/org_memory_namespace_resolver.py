class OrgMemoryNamespaceResolver:
    """Resolves the effective org-memory namespace(s) for a run against the agent's configured allow-list."""

    @staticmethod
    def resolve_for_search(requested: list[str], configured: list[str]) -> list[str] | None:
        """
        Returns the list of namespaces to search across. Empty `requested` falls back to the configured
        set (or unscoped if configured is empty). Raises if any requested entry is outside `configured`
        when configured is non-empty.
        """
        if not requested:
            return list(configured) if configured else None
        if configured:
            outside = [ns for ns in requested if ns not in configured]
            if outside:
                raise ValueError(
                    f"Requested org_memory_namespaces {sorted(outside)} are not in the configured allow-list: "
                    f"{sorted(configured)}"
                )
        return list(requested)
