from typing import ClassVar

import httpx
from cachetools import TTLCache

from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings


class LiteLLMCustomerService:
    """
    Books every LLM call to the acting tenant as its LiteLLM customer, so LiteLLM's Customer Usage view shows tokens
    and cost per tenant (ADR 2026_11_09_acting_tenant_as_litellm_customer).

    The user's key keeps carrying the user; the tenant cannot ride on it, because one key serves a user in all their
    tenants. LiteLLM reads the customer from this header before the `user` field, which the OpenAI-compatible API
    sets to the user's id: a call for a user acting outside any tenant therefore names the `no-tenant` customer
    rather than nothing, or LiteLLM would make that user a customer of their own.
    """

    CUSTOMER_HEADER: ClassVar[str] = "x-litellm-customer-id"
    # Also stamped by LiteLLM's `tenant_attribution` hook on calls that name no customer (pipelines, MinerU). Readable
    # as it is, so it needs no alias.
    NO_TENANT_CUSTOMER_ID: ClassVar[str] = "no-tenant"

    _aliases: ClassVar[TTLCache] = TTLCache(maxsize=1024, ttl=21600)

    @staticmethod
    async def header_for(user: UserIdentity | None) -> dict[str, str]:
        """
        The header that books a call to `user`'s acting tenant, after making sure LiteLLM knows the tenant's name.

        LiteLLM creates a customer it has not seen on its first spend, but without an alias, and its usage view would
        then list the tenant by its id. The alias is cached per process like the user's key, and set again when the
        tenant is renamed.
        """
        tenant = user.acting_within_tenant if user else None
        if tenant is None:
            return {LiteLLMCustomerService.CUSTOMER_HEADER: LiteLLMCustomerService.NO_TENANT_CUSTOMER_ID}

        if LiteLLMCustomerService._aliases.get(tenant.id) != tenant.name:
            await LiteLLMCustomerService._ensure_customer(LiteLLMProxySettings().httpx_aclient, tenant)
            LiteLLMCustomerService._aliases[tenant.id] = tenant.name
        return {LiteLLMCustomerService.CUSTOMER_HEADER: tenant.id}

    @staticmethod
    async def _ensure_customer(client: httpx.AsyncClient, tenant: TenantIdentity) -> None:
        customer = await LiteLLMCustomerService._customer_info(client, tenant)
        if customer is None:
            customer = await LiteLLMCustomerService._create_customer(client, tenant)
            if customer is None:
                return

        if customer.get("alias") != tenant.name:
            update_response = await client.post("/customer/update", json={"user_id": tenant.id, "alias": tenant.name})
            update_response.raise_for_status()

    @staticmethod
    async def _customer_info(client: httpx.AsyncClient, tenant: TenantIdentity) -> dict | None:
        info_response = await client.get("/customer/info", params={"end_user_id": tenant.id})
        if info_response.status_code == 404:
            return None
        info_response.raise_for_status()
        return info_response.json()

    @staticmethod
    async def _create_customer(client: httpx.AsyncClient, tenant: TenantIdentity) -> dict | None:
        """
        A concurrent first call for the same tenant may create the customer first, and LiteLLM answers that with a
        400, so a failure is accepted whenever the customer exists afterwards. That customer is returned, since the
        other caller may have named it before a rename; None means this call created it with the current name.
        """
        new_response = await client.post("/customer/new", json={"user_id": tenant.id, "alias": tenant.name})
        if not new_response.is_error:
            return None
        customer = await LiteLLMCustomerService._customer_info(client, tenant)
        if customer is None:
            new_response.raise_for_status()
        return customer
