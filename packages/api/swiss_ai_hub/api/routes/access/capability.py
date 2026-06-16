import functools
from collections.abc import Callable
from typing import Annotated, Self, TypeVar

from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString

F = TypeVar("F", bound=Callable[..., "Self"])

# Attribute set on the route an annotated builder method registers; read by AccessCapabilityService.
CAPABILITY_ATTRIBUTE = "__capability__"


class CapabilityMeta(BaseModel):
    """Human-readable label/description for an endpoint's access capability.

    Deliberately carries NO access rule: the rule is derived from the endpoint's own
    ``user_with_permission`` guard (the single source of truth), so the two cannot diverge.
    """

    label: Annotated[LocaleString, Field(description="Short action label for the capability.")]
    description: Annotated[LocaleString, Field(description="What holding the capability lets the user do.")]

    @classmethod
    def from_i18n_base(cls, i18n_base: str) -> "CapabilityMeta":
        return cls(
            label=ApiLocaleString.from_i18n_path(f"{i18n_base}.label"),
            description=ApiLocaleString.from_i18n_path(f"{i18n_base}.description"),
        )


def capability(i18n_base: str) -> Callable[[F], F]:
    """Annotate a controller's fluent route-builder method as a grantable capability.

    Sits on the builder method (next to its ``summary``/``description``), not the inner route. The
    wrapper lets the method register its route, then tags that route with the capability metadata.
    ``i18n_base`` resolves ``{base}.label`` and ``{base}.description``; the access rule is taken from
    the endpoint's ``user_with_permission`` guard at catalog-build time, never restated here.
    """
    meta = CapabilityMeta.from_i18n_base(i18n_base)

    def decorator(builder_method: F) -> F:
        @functools.wraps(builder_method)
        def wrapper(self, *args, **kwargs):
            registered_before = len(self.router.routes)
            result = builder_method(self, *args, **kwargs)
            for route in self.router.routes[registered_before:]:
                if isinstance(route, APIRoute):
                    setattr(route, CAPABILITY_ATTRIBUTE, meta)
            return result

        return wrapper

    return decorator
