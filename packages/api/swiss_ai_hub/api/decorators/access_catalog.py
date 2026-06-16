import functools
from collections.abc import Callable
from typing import Annotated, Self, TypeVar

from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString

F = TypeVar("F", bound=Callable[..., Self])

# Attribute set on the route an annotated builder method registers; read by AccessCapabilityService.
ACCESS_CATALOG_ENTRY_ATTRIBUTE = "__access_catalog_entry__"


class AccessCatalogEntryMeta(BaseModel):
    """Human-readable label/description for an endpoint's entry in the access-capability catalog.

    Deliberately carries NO access rule: the rule is derived from the endpoint's own
    ``user_with_permission`` guard (the single source of truth), so the two cannot diverge.
    """

    label: Annotated[LocaleString, Field(description="Short action label for the capability.")]
    description: Annotated[LocaleString, Field(description="What holding the capability lets the user do.")]

    @classmethod
    def from_i18n_path(cls, i18n_path: str) -> "AccessCatalogEntryMeta":
        return cls(
            label=ApiLocaleString.from_i18n_path(f"{i18n_path}.label"),
            description=ApiLocaleString.from_i18n_path(f"{i18n_path}.description"),
        )


def access_catalog_entry(i18n_path: str) -> Callable[[F], F]:
    """Surface a controller's fluent route-builder method as an entry in the access-capability catalog.

    This does NOT enforce access — the endpoint's own ``user_with_permission`` guard does, and that guard
    *is* the catalog's rule (the single source of truth, never restated here). The decorator only labels
    the route so it appears as a grantable capability in the role / tenant-ceiling editors.

    Sits on the builder method (next to its ``summary``/``description``), not the inner route. The wrapper
    lets the method register its route, then tags that route with the catalog metadata. ``i18n_path`` is a
    base that resolves ``{i18n_path}.label`` and ``{i18n_path}.description``.
    """
    meta = AccessCatalogEntryMeta.from_i18n_path(i18n_path)

    def decorator(builder_method: F) -> F:
        @functools.wraps(builder_method)
        def wrapper(self, *args, **kwargs):
            registered_before = len(self.router.routes)
            result = builder_method(self, *args, **kwargs)
            # Fluent builder methods register exactly one route; every route this method added is tagged
            # with the same metadata, so annotating a method that registers two routes labels both alike.
            for route in self.router.routes[registered_before:]:
                if isinstance(route, APIRoute):
                    setattr(route, ACCESS_CATALOG_ENTRY_ATTRIBUTE, meta)
            return result

        return wrapper

    return decorator
