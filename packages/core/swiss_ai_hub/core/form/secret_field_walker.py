from typing import TYPE_CHECKING, Annotated

from swiss_ai_hub.core.form.elements.group import Group
from swiss_ai_hub.core.form.elements.password import Password
from swiss_ai_hub.core.form.elements.repeater import Repeater

if TYPE_CHECKING:
    from swiss_ai_hub.core.form.base.formkit_element import FormkitElement


class SecretFieldWalker:
    """
    Derives which configuration fields are secrets from the announced form.

    The form is the one description of a configuration that every boundary sees — the API validates against
    the announced schema, not the Python class — so the ``Password`` element is the signal, and no side ever
    hardcodes a field name. Paths are dotted; a repeater contributes its children without an index, matching
    how ``SecretPathTransformer`` fans out over list items.
    """

    @classmethod
    def secret_paths(
        cls, elements: Annotated[list["FormkitElement"], "Announced form elements, typically the top level"]
    ) -> set[str]:
        return cls._collect(elements, prefix="")

    @classmethod
    def _collect(cls, elements: list["FormkitElement"], prefix: str) -> set[str]:
        paths: set[str] = set()
        for element in elements:
            if isinstance(element, Group | Repeater):
                paths |= cls._collect(element.children, prefix=f"{prefix}{element.name}.")
            elif isinstance(element, Password):
                paths.add(f"{prefix}{element.name}")
        return paths
