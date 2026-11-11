"""LiteLLM pre-call hook that books every call without a customer to the `no-tenant` customer.

The Hub sends the acting tenant as the LiteLLM customer (`x-litellm-customer-id`) on every call it makes for a user,
so LiteLLM's Customer Usage view shows spend per tenant. Callers that act for no user send nothing: pipelines, scheduled
runs, the memory writer, and MinerU, which reaches LiteLLM with the master key from its own container. LiteLLM writes a
customer's daily spend only when a request names one, so those calls would be in the instance total but on no customer
line, and the tenants' lines could never add up to the total. Booking them to one customer of their own makes them a
line next to the tenants.

Bind-mounted into the upstream LiteLLM image like `custom_callbacks.py`, so it depends on the stdlib and LiteLLM only.
"""

try:
    from litellm.integrations.custom_logger import CustomLogger
except ImportError:
    # litellm is absent outside its own image (the unit tests import this by path).
    CustomLogger = object

# The same id `LiteLLMCustomerService.NO_TENANT_CUSTOMER_ID` sends from the Hub.
NO_TENANT_CUSTOMER_ID = "no-tenant"

# LiteLLM copies the resolved customer into whichever of these the route uses, and reads it back from there when it
# writes the spend log and the customer's daily spend.
_METADATA_FIELDS = ("metadata", "litellm_metadata")
_END_USER_FIELD = "user_api_key_end_user_id"


class TenantAttribution(CustomLogger):
    """Fills in the customer only where LiteLLM resolved none, so a customer a caller named always wins."""

    async def async_pre_call_hook(self, user_api_key_dict, cache, data: dict, call_type: str) -> dict:
        if getattr(user_api_key_dict, "end_user_id", None):
            return data

        user_api_key_dict.end_user_id = NO_TENANT_CUSTOMER_ID
        for field in _METADATA_FIELDS:
            metadata = data.get(field)
            if isinstance(metadata, dict) and not metadata.get(_END_USER_FIELD):
                metadata[_END_USER_FIELD] = NO_TENANT_CUSTOMER_ID
        return data


tenant_attribution_instance = TenantAttribution()
