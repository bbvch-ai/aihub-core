class OrgMemoryNamespaceResolver:
    """Resolves the effective org-memory namespace(s) for a run against the agent's configured allow-list."""

    @staticmethod
    def resolve_for_write(event_override: str | None, default: str | None, allowed: list[str]) -> str | None:
        """
        Returns the singular namespace to write under. Event override wins over default. Raises if the
        effective value is outside `allowed` when the allow-list is non-empty.
        """
        effective = event_override if event_override is not None else default
        if allowed and (effective is None or effective not in allowed):
            raise ValueError(
                f"Effective write namespace {effective!r} is not in the configured allow-list: {sorted(allowed)}"
            )
        return effective

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
