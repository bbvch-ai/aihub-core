class NamespaceScopeRule:
    """The explicit-namespace-scope rule of a Milvus retriever, shared by the config model and the form element.

    Kept apart from the model validator because the API validates saves against a model rebuilt from the JSON
    Schema, which carries no Python validators; the form element applies this rule there instead, so a save is
    refused with the same message a run would otherwise abort with.
    """

    @staticmethod
    def error(index_namespaces: list[str], all_namespaces: bool) -> str | None:
        """The reason the scope is not explicit, or ``None`` when it is."""
        if all_namespaces and index_namespaces:
            return "Either name the namespaces to search or enable all_namespaces, not both."
        if not all_namespaces and not index_namespaces:
            return "Select at least one namespace to search, or enable all_namespaces."
        return None
