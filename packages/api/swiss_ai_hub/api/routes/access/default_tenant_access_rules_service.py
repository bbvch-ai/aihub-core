import logging

import httpx
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.infrastructure import TenantDefaultAccessSettings, trace_fn

from swiss_ai_hub.api.routes.access.access_capability_service import AccessCapabilityService
from swiss_ai_hub.api.routes.access.model_roster_unavailable_error import ModelRosterUnavailableError

logger = logging.getLogger(__name__)

# Everything a tenant needs to be usable apart from models. The ceiling caps every rule family, so a
# model-only ceiling would leave the tenant unable to reach agents, knowledge, processes or the admin UI.
_NON_MODEL_RULES: tuple[str, ...] = (
    "aihub.admin.agent.>",
    # Both forms are needed: ``knowledge.>`` covers every existing database, while the bare root is what
    # *creating* one is guarded on — a database that does not exist yet cannot be named by a rule, and a
    # ``.>`` rule never matches its own root. Mirrors the ``AIHubKnowledgeAdmin`` seed in
    # ``initialize_db._DEFAULT_ROLE_DEFINITIONS``, which carries both for the same reason.
    "aihub.admin.knowledge",
    "aihub.admin.knowledge.>",
    "aihub.admin.process.>",
    "aihub.admin.service.>",
    "aihub.user.memory.>",
)


class DefaultTenantAccessRulesService:
    """Derives the access ceiling a newly created tenant starts with.

    Derived from the live LiteLLM roster rather than a hardcoded list because CPU and GPU deployments
    serve entirely different models — a fixed list would leave a GPU tenant with no chat model at all.
    """

    @staticmethod
    @trace_fn
    async def derive() -> list[str]:
        settings = TenantDefaultAccessSettings()
        excluded = set(settings.excluded_models_list)

        try:
            models_by_capability = await AccessCapabilityService.available_models_by_capability()
        except (httpx.HTTPError, KeyError, ValueError) as roster_error:
            # A transport failure is the obvious case, but the fetch also indexes ``["data"]`` and
            # ``["model_name"]``, so a 200 carrying an unexpected body raises KeyError or ValueError
            # (JSONDecodeError subclasses it). Those are roster problems too, and letting them past here
            # costs the caller its actionable 503 — or, at startup, the whole API.
            raise ModelRosterUnavailableError(
                f"Could not read the model roster from the model gateway: {roster_error!r}"
            ) from roster_error

        if not models_by_capability:
            raise ModelRosterUnavailableError("The model gateway reported an empty model roster.")

        DefaultTenantAccessRulesService._warn_about_unmatched_exclusions(excluded, models_by_capability)

        rules = list(_NON_MODEL_RULES)
        for capability in sorted(models_by_capability):
            rules.extend(
                DefaultTenantAccessRulesService._rules_for_capability(
                    capability, sorted(models_by_capability[capability]), excluded
                )
            )
        return rules

    @staticmethod
    def _rules_for_capability(capability: str, names: list[str], excluded: set[str]) -> list[str]:
        """A capability with nothing excluded collapses to one wildcard, so models added to it later reach
        new tenants on their own. Only a capability holding an exclusion has to enumerate its survivors,
        which also makes each of its models an individually toggleable row in the access editor."""
        survivors = [name for name in names if f"{capability}/{name}" not in excluded]
        if len(survivors) == len(names):
            return [f"{AccessChecker.USER_PREFIX}model.{capability}.>"]

        logger.info(
            "Tenant default ceiling: enumerating %d of %d models for capability '%s'",
            len(survivors),
            len(names),
            capability,
        )
        return [AccessChecker.model_user_rule(capability, name) for name in survivors]

    @staticmethod
    def _warn_about_unmatched_exclusions(excluded: set[str], models_by_capability: dict[str, list[str]]) -> None:
        """An exclusion the roster does not serve is legitimate — a CPU instance never serves a GPU-only
        model — so it must not fail the derivation. It is still worth surfacing, because the same symptom
        appears when a model was renamed and the exclusion has quietly stopped applying."""
        served = {f"{capability}/{name}" for capability, names in models_by_capability.items() for name in names}
        for unmatched in sorted(excluded - served):
            logger.warning(
                "Tenant default ceiling: excluded model '%s' is not served by this instance; ignoring it", unmatched
            )
