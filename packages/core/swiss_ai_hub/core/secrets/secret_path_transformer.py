from collections.abc import Callable
from copy import deepcopy
from typing import Annotated, Any


class SecretPathTransformer:
    """
    Applies a value transformation at dotted paths inside a configuration dict.

    Paths come from the announced form, where a repeater contributes its children without an index
    (``examples.api_key``), so a list met along a path fans out over every item. Missing keys are skipped:
    a submission omits fields it did not set, and a hidden group submits nothing at all.
    """

    @classmethod
    def transform(
        cls,
        config: Annotated[dict[str, Any], "Configuration as submitted or as stored"],
        paths: Annotated[set[str], "Dotted paths of the secret fields"],
        transform: Annotated[Callable[[Any], Any], "Applied to every value found at a path"],
    ) -> dict[str, Any]:
        result = deepcopy(config)
        for path in paths:
            cls._apply(result, path.split("."), transform)
        return result

    @classmethod
    def _apply(cls, node: Any, segments: list[str], transform: Callable[[Any], Any]) -> None:
        if isinstance(node, list):
            for item in node:
                cls._apply(item, segments, transform)
            return
        if not isinstance(node, dict) or segments[0] not in node:
            return
        key, rest = segments[0], segments[1:]
        if rest:
            cls._apply(node[key], rest, transform)
            return
        if isinstance(node[key], list):
            node[key] = [transform(item) for item in node[key]]
            return
        node[key] = transform(node[key])

    @classmethod
    def values_at(
        cls,
        config: Annotated[dict[str, Any], "Configuration to read from"],
        path: Annotated[str, "Dotted path"],
    ) -> list[Any]:
        """Every value at ``path`` in document order, one per repeater item when lists are crossed."""
        found: list[Any] = []
        cls._apply(deepcopy(config), path.split("."), lambda value: found.append(value) or value)
        return found
