from typing import Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_customer_service import LiteLLMCustomerService
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService


class LiteLLMCredentials(BaseModel):
    """
    What a call needs to reach LiteLLM for a user: their key, which carries the user and their budget, and the header
    that books the call to their acting tenant.

    Fetched together because a call with the key but without the header still succeeds and is silently booked to
    `no-tenant`.
    """

    api_key: Annotated[
        str | None, Field(repr=False, description="The user's key; None falls back to the master key")
    ] = None
    headers: Annotated[dict[str, str], Field(description="The customer header of the acting tenant")]

    @classmethod
    async def for_user(cls, user: UserIdentity | None) -> Self:
        api_key = await LiteLLMService.api_key_for_user(user) if user else None
        return cls(api_key=api_key, headers=await LiteLLMCustomerService.header_for(user))
