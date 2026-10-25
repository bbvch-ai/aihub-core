from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from fastapi import HTTPException
from mongoengine import DoesNotExist
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity

from swiss_ai_hub.api.routes.thread.dto.thread_dto import ThreadDTO
from swiss_ai_hub.api.routes.thread.thread_access import ThreadAccess
from swiss_ai_hub.api.routes.thread.thread_service import ThreadService
from swiss_ai_hub.api.routes.user.dto.minimal_user_dto import MinimalUserDTO

MEMBER_ID = "member-user"
OUTSIDER_ID = "outsider-user"
BROAD_USER_RULES = ["aihub.user.>"]
BROAD_TENANT_RULES = ["aihub.admin.>"]
FROM_USER = "swiss_ai_hub.api.routes.thread.thread_access.AccessChecker.from_user"


def _user(user_id: str, *, tenant_id: str = "tenant-a", is_sys_admin: bool = False) -> UserIdentity:
    return UserIdentity(
        id=user_id,
        name=user_id,
        email=f"{user_id}@example.com",
        roles=["AIHubUser"],
        acting_within_tenant=TenantIdentity(id=tenant_id, name=tenant_id, access_rules=BROAD_TENANT_RULES),
        is_sys_admin=is_sys_admin,
    )


def _thread(*, process_class: str | None = None, process_id: str | None = None) -> ThreadDTO:
    return ThreadDTO(
        id=str(ObjectId()),
        name="chat",
        users=[MinimalUserDTO(id=MEMBER_ID, name="member", email="member@example.com")],
        agents=[],
        created_at="2026-10-25T00:00:00",
        process_class=process_class,
        process_id=process_id,
    )


def _checker(user_rules: list[str], tenant_rules: list[str] = BROAD_TENANT_RULES) -> AccessChecker:
    return AccessChecker(user_rules, tenant_access_rules=tenant_rules)


class TestCanView:
    def test_member_can_view(self):
        with patch(FROM_USER, return_value=_checker([])):
            assert ThreadAccess.can_view(_thread(), _user(MEMBER_ID))

    def test_non_member_with_broad_rules_cannot_view_a_thread_without_process(self):
        """A missing process must not turn into a `process.None.None` permission that `aihub.user.>` matches."""
        with patch(FROM_USER, return_value=_checker(BROAD_USER_RULES)):
            assert not ThreadAccess.can_view(_thread(), _user(OUTSIDER_ID))

    def test_non_member_of_another_tenant_cannot_view_a_thread_without_process(self):
        with patch(FROM_USER, return_value=_checker(BROAD_USER_RULES)):
            assert not ThreadAccess.can_view(_thread(), _user(OUTSIDER_ID, tenant_id="tenant-b"))

    def test_sys_admin_can_view_a_thread_without_process(self):
        assert ThreadAccess.can_view(_thread(), _user(OUTSIDER_ID, is_sys_admin=True))

    def test_non_member_with_access_to_the_process_can_view_its_thread(self):
        thread = _thread(process_class="InvoiceProcess", process_id="p1")
        with patch(FROM_USER, return_value=_checker(["aihub.user.process.InvoiceProcess.p1"])):
            assert ThreadAccess.can_view(thread, _user(OUTSIDER_ID))

    def test_non_member_without_access_to_the_process_cannot_view_its_thread(self):
        thread = _thread(process_class="InvoiceProcess", process_id="p1")
        with patch(FROM_USER, return_value=_checker(["aihub.user.process.InvoiceProcess.p2"])):
            assert not ThreadAccess.can_view(thread, _user(OUTSIDER_ID))

    def test_ensure_can_view_answers_403(self):
        with patch(FROM_USER, return_value=_checker(BROAD_USER_RULES)), pytest.raises(HTTPException) as raised:
            ThreadAccess.ensure_can_view(_thread(), _user(OUTSIDER_ID))
        assert raised.value.status_code == 403


class TestEnsureCanPost:
    def test_member_can_post(self):
        ThreadAccess.ensure_can_post(_thread(), _user(MEMBER_ID))

    def test_non_member_with_process_access_cannot_post(self):
        thread = _thread(process_class="InvoiceProcess", process_id="p1")
        with pytest.raises(HTTPException) as raised:
            ThreadAccess.ensure_can_post(thread, _user(OUTSIDER_ID))
        assert raised.value.status_code == 403


class TestGetOrCreateThreadToPostIn:
    AGENT = AgentInstanceRef(agent_class="RAGAgent", agent_id="default")

    @pytest.mark.asyncio
    async def test_existing_thread_of_someone_else_is_refused(self):
        with (
            patch.object(ThreadService, "get_thread_by_id", new=AsyncMock(return_value=_thread())),
            patch.object(ThreadEntity, "create_thread") as create_thread,
            pytest.raises(HTTPException) as raised,
        ):
            await ThreadService.get_or_create_thread_to_post_in(str(ObjectId()), _user(OUTSIDER_ID), self.AGENT, t=None)
        assert raised.value.status_code == 403
        create_thread.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_thread_is_started_for_the_caller(self):
        thread_id = str(ObjectId())
        created = _thread()
        with (
            patch.object(ThreadService, "get_thread_by_id", new=AsyncMock(side_effect=[DoesNotExist(), created])),
            patch.object(ThreadEntity, "create_thread") as create_thread,
        ):
            thread = await ThreadService.get_or_create_thread_to_post_in(
                thread_id, _user(MEMBER_ID), self.AGENT, t=None
            )

        assert thread is created
        assert create_thread.call_args.kwargs["thread_id"] == ObjectId(thread_id)
        assert [user.user_id for user in create_thread.call_args.kwargs["users"]] == [MEMBER_ID]

    @pytest.mark.asyncio
    async def test_scheduled_run_thread_id_is_not_handed_to_a_client(self):
        scheduled_thread_id = str(ThreadEntity.scheduled_thread_id(self.AGENT))
        with (
            patch.object(ThreadService, "get_thread_by_id", new=AsyncMock(side_effect=DoesNotExist())),
            patch.object(ThreadEntity, "create_thread") as create_thread,
            pytest.raises(HTTPException) as raised,
        ):
            await ThreadService.get_or_create_thread_to_post_in(
                scheduled_thread_id, _user(MEMBER_ID), self.AGENT, t=None
            )
        assert raised.value.status_code == 409
        create_thread.assert_not_called()
