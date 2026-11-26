from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.events import EventSpecs
from swiss_ai_hub.core.events.process import HumanInSpecs
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence.process.process_class_entity import HumanInSpecsEntity
from swiss_ai_hub.core.processes import ProcessConfig
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
from swiss_ai_hub.api.routes.process.human_work_request_assignment import HumanWorkRequestAssignment
from swiss_ai_hub.api.routes.process.process_service import ProcessService
from swiss_ai_hub.api.runners.simulation.process.events.human_b_work import HumanBWork
from swiss_ai_hub.api.runners.simulation.process.events.human_start_work import HumanStartEvent

_PROCESS_MODULE = "swiss_ai_hub.api.routes.process.process_service"
PROCESS_CLASS = "ReviewProcess"
PROCESS_ID = "review"
WALKTHROUGH_ID = "0123456789abcdef01234567"
REQUEST_ID = "request-1"


def _human_input(event_class: type, route: str, *, is_process_start: bool) -> HumanInSpecsEntity:
    return HumanInSpecsEntity.from_specs(
        HumanInSpecs(
            name=LocaleString(en=event_class.event_name_from_class()),
            description=LocaleString(en="description"),
            route=route,
            method="POST",
            is_process_start=is_process_start,
            event_specs=EventSpecs.from_event_class(event_class),
        )
    )


def _class_entity() -> Mock:
    class_entity = Mock()
    class_entity.human_inputs = [
        _human_input(HumanStartEvent, "/start", is_process_start=True),
        _human_input(HumanBWork, "/review", is_process_start=False),
    ]
    return class_entity


def _open_request(**assignees: list[str]) -> dict:
    return {
        "event_id": REQUEST_ID,
        "event_data": {"forms": [{"_event_name": HumanBWork.event_name_from_class()}], **assignees},
    }


async def _submit_open_form(open_requests: list[dict], route: str = "/review", method: str = "POST") -> AsyncMock:
    distributor = Mock()
    distributor.distribute_event = AsyncMock()
    with (
        patch(f"{_PROCESS_MODULE}.ProcessClassEntity.get_by_process_class", return_value=_class_entity()),
        patch(
            f"{_PROCESS_MODULE}.PersistedProcessEventEntity.get_open_human_work_requests", return_value=open_requests
        ),
    ):
        await ProcessService.submit_process_open_form(
            process_class=PROCESS_CLASS,
            process_id=PROCESS_ID,
            process_walkthrough_id=WALKTHROUGH_ID,
            route=route,
            method=method,
            raw_event_data={"payload": "approved"},
            external_process_event_distributor=distributor,
            user=fake_user(),
            t=ApiLocaleHandler(),
        )
    return distributor.distribute_event


class TestHumanWorkRequestAssignment:
    def test_assigned_by_user_id(self):
        assert HumanWorkRequestAssignment.is_assigned_to({"user_ids": [fake_user().id]}, fake_user())

    def test_assigned_by_email_ignoring_case(self):
        assert HumanWorkRequestAssignment.is_assigned_to({"user_emails": [fake_user().email.upper()]}, fake_user())

    def test_assigned_by_tenant_role(self):
        assert HumanWorkRequestAssignment.is_assigned_to({"user_roles": fake_user().roles}, fake_user())

    def test_someone_else_is_not_assigned(self):
        work_request = {"user_ids": ["other"], "user_emails": ["other@example.com"], "user_roles": ["OtherRole"]}

        assert not HumanWorkRequestAssignment.is_assigned_to(work_request, fake_user())

    def test_a_request_naming_nobody_is_assigned_to_nobody(self):
        assert not HumanWorkRequestAssignment.is_assigned_to({}, fake_user())


class TestSubmitOpenForm:
    @pytest.mark.asyncio
    async def test_the_assignee_completes_the_task(self):
        distribute = await _submit_open_form([_open_request(user_ids=[fake_user().id])])

        distribute.assert_awaited_once()
        submitted_event = distribute.await_args.args[0].event
        assert submitted_event.in_response_to == REQUEST_ID
        assert submitted_event.event_name == HumanBWork.event_name_from_class()

    @pytest.mark.asyncio
    async def test_a_user_who_is_not_assigned_is_rejected(self):
        with pytest.raises(HTTPException) as raised:
            await _submit_open_form([_open_request(user_ids=["someone-else"])])

        assert raised.value.status_code == 403

    @pytest.mark.asyncio
    async def test_the_assigned_request_is_answered_when_several_are_open(self):
        others = {**_open_request(user_ids=["someone-else"]), "event_id": "not-mine"}

        distribute = await _submit_open_form([others, _open_request(user_roles=fake_user().roles)])

        assert distribute.await_args.args[0].event.in_response_to == REQUEST_ID

    @pytest.mark.asyncio
    async def test_no_open_request_for_the_form_is_not_found(self):
        with pytest.raises(HTTPException) as raised:
            await _submit_open_form([])

        assert raised.value.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("route", "method"), [("/elsewhere", "POST"), ("/review", "PUT"), ("/start", "POST")])
    async def test_a_route_and_method_no_open_step_declares_is_not_found(self, route: str, method: str):
        with pytest.raises(HTTPException) as raised:
            await _submit_open_form([_open_request(user_ids=[fake_user().id])], route=route, method=method)

        assert raised.value.status_code == 404


class TestSubmitStartForm:
    @pytest.mark.asyncio
    async def test_a_step_that_does_not_start_the_process_cannot_start_it(self):
        distributor = Mock()
        distributor.distribute_event = AsyncMock()
        with (
            patch(f"{_PROCESS_MODULE}.ProcessClassEntity.get_by_process_class", return_value=_class_entity()),
            pytest.raises(HTTPException) as raised,
        ):
            await ProcessService.submit_process_start_form(
                process_class=PROCESS_CLASS,
                process_id=PROCESS_ID,
                route="/review",
                method="POST",
                raw_event_data={"payload": "x"},
                external_process_event_distributor=distributor,
                user=fake_user(),
                t=ApiLocaleHandler(),
                process_config=Mock(spec=ProcessConfig),
            )

        assert raised.value.status_code == 404
        distributor.distribute_event.assert_not_awaited()


class TestOpenForms:
    @pytest.mark.asyncio
    async def test_only_tasks_assigned_to_the_user_are_listed(self):
        with (
            patch(f"{_PROCESS_MODULE}.ProcessClassEntity.get_by_process_class", return_value=_class_entity()),
            patch(
                f"{_PROCESS_MODULE}.PersistedProcessEventEntity.get_open_human_work_requests",
                return_value=[_open_request(user_ids=["someone-else"])],
            ),
        ):
            forms = await ProcessService.get_process_open_forms(
                PROCESS_CLASS, PROCESS_ID, WALKTHROUGH_ID, fake_user(), ApiLocaleHandler()
            )

        assert forms == []

    @pytest.mark.asyncio
    async def test_an_assigned_task_is_listed(self):
        with (
            patch(f"{_PROCESS_MODULE}.ProcessClassEntity.get_by_process_class", return_value=_class_entity()),
            patch(
                f"{_PROCESS_MODULE}.PersistedProcessEventEntity.get_open_human_work_requests",
                return_value=[_open_request(user_emails=[fake_user().email])],
            ),
        ):
            forms = await ProcessService.get_process_open_forms(
                PROCESS_CLASS, PROCESS_ID, WALKTHROUGH_ID, fake_user(), ApiLocaleHandler()
            )

        assert [form.route for form in forms] == ["/review"]
