class ModelRefPath:
    """Turns a model reference written relative to the declaring form into the dotted path from the form root.

    A sub-form such as `LLMParameter` is nested at a different depth in every config that uses it, so it can only
    name its model relative to itself; the frontend (`$root.<path>`) and the API (a lookup in the submitted config)
    both need the absolute path.
    """

    PARENT = "../"

    @staticmethod
    def resolve(relative_path: str, id_prefix: str) -> str:
        """`../model_name` under `llm.default_parameter.` resolves to `llm.model_name`; a path without `../`
        is taken from the declaring form, so `llm.model_name` at the root stays as it is."""
        segments = [segment for segment in id_prefix.split(".") if segment]
        path = relative_path
        while path.startswith(ModelRefPath.PARENT):
            if not segments:
                raise ValueError(f"Model reference '{relative_path}' climbs above the form root from '{id_prefix}'.")
            segments.pop()
            path = path.removeprefix(ModelRefPath.PARENT)
        return ".".join([*segments, path])
