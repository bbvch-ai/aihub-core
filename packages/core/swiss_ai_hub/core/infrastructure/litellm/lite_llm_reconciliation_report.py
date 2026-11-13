from typing import Annotated

from pydantic import BaseModel, Field


class LiteLLMReconciliationReport(BaseModel):
    """What one reconciliation run of LiteLLM's users against Keycloak found and changed."""

    users_without_hub_user: Annotated[
        list[str],
        Field(
            description="LiteLLM users with no Keycloak user, whatever their role. Users the Hub created are deleted "
            "too; the others are only reported."
        ),
    ] = []
    deleted_user_ids: Annotated[list[str], Field(description="Users the Hub created and Keycloak no longer has.")] = []
    blocked_user_ids: Annotated[
        list[str], Field(description="Users disabled in Keycloak whose keys were blocked.")
    ] = []
    unblocked_user_ids: Annotated[
        list[str], Field(description="Users enabled again in Keycloak whose keys the Hub had blocked.")
    ] = []
    limits_updated_user_ids: Annotated[list[str], Field(description="Users whose limits were changed.")] = []
    keycloak_state_by_user_id_without_row: Annotated[
        dict[str, str],
        Field(
            description="Users who own LiteLLM keys but have no LiteLLM user, with their state in Keycloak. The keys "
            "carry no limits and are never blocked, so an operator has to remove them."
        ),
    ] = {}

    def summary(self) -> str:
        return (
            f"{len(self.users_without_hub_user)} without a Keycloak user ({len(self.deleted_user_ids)} deleted), "
            f"{len(self.blocked_user_ids)} blocked, {len(self.unblocked_user_ids)} unblocked, "
            f"{len(self.limits_updated_user_ids)} with updated limits, "
            f"{len(self.keycloak_state_by_user_id_without_row)} with keys but no LiteLLM user"
        )
