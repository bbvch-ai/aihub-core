import asyncio
import logging
from collections import defaultdict
from typing import Any, ClassVar

from redis.asyncio import Redis

from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_reconciliation_report import LiteLLMReconciliationReport
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_user_admin_service import LiteLLMUserAdminService
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_user_limits import LiteLLMUserLimits

logger = logging.getLogger(__name__)


class LiteLLMUserReconciler:
    """
    Keeps LiteLLM's users in line with Keycloak. Users are disabled and removed in Keycloak, and nothing tells the Hub,
    so each run compares the two: users the Hub created get the limits its settings give them, a disabled user's keys
    are blocked until the user is enabled again, and a user Keycloak no longer has is deleted with their keys. LiteLLM
    users the Hub did not create are only reported.

    Changing what a user can do needs positive evidence: keys are blocked only for a user Keycloak lists as disabled,
    and a user is deleted only once Keycloak answers 404 for them, so a partial listing or an outage changes nothing.

    One run per interval across all API replicas: the run takes a Redis lease that expires after the interval. Like
    `CronScheduler`, it holds no state of its own and lifts into aihub-daemon (#1203) unchanged.
    """

    # LiteLLM's built-in admin, which its UI logs in as. It is never a Hub user, so reporting it on every run would
    # say nothing.
    LITELLM_ADMIN_USER_ID: ClassVar[str] = "default_user_id"
    _LEASE_KEY: ClassVar[str] = "litellm:user-reconciliation:lease"

    def __init__(self, *, redis: Redis, settings: LiteLLMProxySettings | None = None) -> None:
        self._redis = redis
        self._settings = settings or LiteLLMProxySettings()
        self.running: bool = False
        self.task: asyncio.Task | None = None

    def start(self) -> bool:
        """Synchronous like `CronScheduler.start`, and likewise needs a running event loop."""
        if self.running:
            logger.warning("LiteLLM user reconciliation is already running")
            return False
        self.running = True
        self.task = asyncio.create_task(self._reconciliation_loop())
        logger.info("LiteLLM user reconciliation started")
        return True

    async def stop(self) -> bool:
        if not self.running:
            logger.warning("LiteLLM user reconciliation is not running")
            return False
        self.running = False
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
        logger.info("LiteLLM user reconciliation stopped")
        return True

    async def reconcile(self) -> LiteLLMReconciliationReport:
        """
        One run, without the lease. Access is withdrawn for every user before any is restored or has their limits
        changed, so a user whose update LiteLLM rejects cannot keep a disabled or removed user's key working.
        """
        enabled_by_user_id = await KeycloakAdminService.get_enabled_by_user_id()
        if not enabled_by_user_id:
            raise RuntimeError("Keycloak listed no users; refusing to compare LiteLLM's users against an empty realm")

        exempt_user_ids = self._settings.user_reconcile_exempt_user_ids | {self.LITELLM_ADMIN_USER_ID}
        users = [user for user in await LiteLLMUserAdminService.list_users() if user["user_id"] not in exempt_user_ids]
        keys_by_user_id = self._keys_by_user_id(await LiteLLMUserAdminService.list_keys())
        report = LiteLLMReconciliationReport()

        for user_row in users:
            await self._withdraw_access(user_row, enabled_by_user_id, keys_by_user_id, report)
        limits = LiteLLMUserLimits.from_settings(self._settings)
        for user_row in users:
            if self._is_hub_user(user_row) and enabled_by_user_id.get(user_row["user_id"]):
                await self._restore_and_update(user_row, keys_by_user_id[user_row["user_id"]], limits, report)
        return report

    async def _reconciliation_loop(self) -> None:
        while self.running:
            try:
                await self.run_if_due()
            except Exception as error:
                logger.exception(f"LiteLLM user reconciliation failed: {error}")
            await asyncio.sleep(self._settings.USER_RECONCILE_INTERVAL_SECONDS)

    async def run_if_due(self) -> None:
        """Runs unless another replica, or this one, ran within the interval."""
        lease_milliseconds = int(self._settings.USER_RECONCILE_INTERVAL_SECONDS * 1000)
        if not await self._redis.set(self._LEASE_KEY, "held", nx=True, px=lease_milliseconds):
            return
        self._log(await self.reconcile())

    async def _withdraw_access(
        self,
        user_row: dict[str, Any],
        enabled_by_user_id: dict[str, bool],
        keys_by_user_id: defaultdict[str, list[dict[str, Any]]],
        report: LiteLLMReconciliationReport,
    ) -> None:
        user_id = user_row["user_id"]
        enabled = enabled_by_user_id.get(user_id)
        if enabled is None:
            await self._remove_if_gone(user_row, report)
        elif not enabled and self._is_hub_user(user_row) and self._has_usable_key(user_row, keys_by_user_id[user_id]):
            await LiteLLMUserAdminService.block_keys(user_row, keys_by_user_id[user_id])
            report.blocked_user_ids.append(user_id)

    async def _remove_if_gone(self, user_row: dict[str, Any], report: LiteLLMReconciliationReport) -> None:
        """A user missing from the listing may have signed up after it was taken, so Keycloak is asked again."""
        user_id = user_row["user_id"]
        if await KeycloakAdminService.user_exists(user_id):
            return
        report.users_without_hub_user.append(user_id)
        if self._is_hub_user(user_row):
            await LiteLLMUserAdminService.delete_user(user_id)
            report.deleted_user_ids.append(user_id)

    @staticmethod
    async def _restore_and_update(
        user_row: dict[str, Any],
        keys: list[dict[str, Any]],
        limits: LiteLLMUserLimits,
        report: LiteLLMReconciliationReport,
    ) -> None:
        user_id = user_row["user_id"]
        if LiteLLMUserAdminService.keys_blocked_by_hub(user_row):
            await LiteLLMUserAdminService.unblock_keys(user_row, keys)
            report.unblocked_user_ids.append(user_id)
        if await LiteLLMUserAdminService.update_limits(user_id, limits, LiteLLMUserLimits.from_user_row(user_row)):
            report.limits_updated_user_ids.append(user_id)

    @staticmethod
    def _has_usable_key(user_row: dict[str, Any], keys: list[dict[str, Any]]) -> bool:
        """Unmarked counts as usable too: a key minted after the mark was set would otherwise go unnoticed."""
        return not LiteLLMUserAdminService.keys_blocked_by_hub(user_row) or any(not key.get("blocked") for key in keys)

    @staticmethod
    def _is_hub_user(user_row: dict[str, Any]) -> bool:
        return user_row.get("user_role") == LiteLLMUserAdminService.HUB_USER_ROLE

    @staticmethod
    def _keys_by_user_id(keys: list[dict[str, Any]]) -> defaultdict[str, list[dict[str, Any]]]:
        keys_by_user_id: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        for key in keys:
            keys_by_user_id[key.get("user_id")].append(key)
        return keys_by_user_id

    @staticmethod
    def _log(report: LiteLLMReconciliationReport) -> None:
        logger.info("LiteLLM user reconciliation: %s", report.summary())
        if report.deleted_user_ids:
            logger.info("Deleted LiteLLM users that Keycloak no longer has: %s", ", ".join(report.deleted_user_ids))
        if report.blocked_user_ids:
            logger.info("Blocked the keys of users disabled in Keycloak: %s", ", ".join(report.blocked_user_ids))
        left_alone = [user_id for user_id in report.users_without_hub_user if user_id not in report.deleted_user_ids]
        if left_alone:
            logger.warning(
                "LiteLLM users without a Keycloak user, left alone because the Hub did not create them: %s",
                ", ".join(left_alone),
            )
