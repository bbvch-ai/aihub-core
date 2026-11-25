from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import InputNumber, InputText, Password
from swiss_ai_hub.core.form.constraints import Ge, Gt
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class ExternalAccessFilterConfig(Form):
    """Lets another system decide, per asking user, which documents a RAG agent may retrieve.

    Some organizations keep document permissions in a system of their own and must not copy them into the AI Hub.
    With this set, the agent asks that system's resolver which values of one metadata key the user may see and
    retrieves only chunks carrying one of them. Left unset, retrieval behaves as before.
    """

    metadata_key: Annotated[
        str | InputText,
        Field(description="The chunk metadata key the resolver's values are matched against, e.g. lcdm_knowledge_code."),
    ]
    resolver_url: Annotated[
        str | InputText,
        Field(
            description="Called with GET, the API key as bearer and the asking user in X-AIHub-User-Email and "
            "X-AIHub-Tenant; answers {\"values\": [...]}. The resolver maps the user to its own model."
        ),
    ]
    api_key: Annotated[
        str | Password,
        Field(
            description="Proves to the resolver that the AI Hub is asking. The user is named by the AI Hub, which "
            "verified them; chat clients forward no user token the resolver could check instead."
        ),
    ] = ""
    timeout_seconds: Annotated[
        float | InputNumber,
        Field(description="How long to wait for the resolver; a slower answer counts as no access."),
        Gt(0),
    ] = 5.0
    cache_ttl_seconds: Annotated[
        int | InputNumber,
        Field(description="How long a user's answer is reused; a revoked permission takes effect after at most this."),
        Ge(0),
    ] = 60

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            metadata_key=InputText(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.external_access_filter.metadata_key.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.external_access_filter.metadata_key.help"),
            ),
            resolver_url=InputText(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.external_access_filter.resolver_url.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.external_access_filter.resolver_url.help"),
            ),
            api_key=Password(
                label=AgentLocaleString.from_i18n_path("agent.rag_agent.config.external_access_filter.api_key.label"),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.external_access_filter.api_key.help"),
            ),
            timeout_seconds=InputNumber(
                label=AgentLocaleString.from_i18n_path(
                    "agent.rag_agent.config.external_access_filter.timeout_seconds.label"
                ),
                help=AgentLocaleString.from_i18n_path("agent.rag_agent.config.external_access_filter.timeout_seconds.help"),
                min=1,
                max=60,
                step=1,
            ),
            cache_ttl_seconds=InputNumber(
                label=AgentLocaleString.from_i18n_path(
                    "agent.rag_agent.config.external_access_filter.cache_ttl_seconds.label"
                ),
                help=AgentLocaleString.from_i18n_path(
                    "agent.rag_agent.config.external_access_filter.cache_ttl_seconds.help"
                ),
                min=0,
                max=3600,
                step=10,
            ),
        )
