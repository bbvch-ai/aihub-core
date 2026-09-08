from typing import Annotated

from pydantic import Field, computed_field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class TenantDefaultAccessSettings(EnvironmentSettings):
    """
    Policy for the access ceiling a newly created tenant starts with.

    The access-rule grammar is additive only — there is no way to express "every model except X" —
    so a curated ceiling has to enumerate the survivors. Holding the *exclusions* here rather than
    an allow list keeps this configuration hardware-independent: CPU and GPU deployments serve
    entirely different model rosters, and the exclusion is the same policy on both.

    Read once, when a tenant is created. Afterwards the tenant's stored rules are the only
    authority, so re-granting an excluded model later is an ordinary access-rule edit.
    """

    model_config = EnvironmentSettings.create_settings_config("AIHUB_TENANT_DEFAULT_ACCESS_")

    EXCLUDED_MODELS: Annotated[
        str,
        Field(
            description=(
                "Comma-separated models withheld from a new tenant's default ceiling, each as "
                "``capability/name`` exactly as LiteLLM reports it (e.g. "
                "``text-generation/Apertus-70B-Instruct-2509``). Matched against the live roster verbatim, "
                "so a renamed or removed model silently matches nothing and the capability falls back to a "
                "plain wildcard."
            ),
        ),
    ] = "text-generation/Apertus-70B-Instruct-2509"

    @computed_field
    @property
    def excluded_models_list(self) -> list[str]:
        """Returns the excluded models as a list."""
        return [model.strip() for model in self.EXCLUDED_MODELS.split(",") if model.strip()]
