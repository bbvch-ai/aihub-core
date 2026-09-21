import json
from unittest.mock import patch

import httpx
import pytest
from swiss_ai_hub.core.infrastructure.rclone import RcloneBackendType, RcloneSourceConfig

from swiss_ai_hub.pipeline.resources.rclone.rclone_client import RcloneClient

_RealClient = httpx.Client


def _client(handler) -> RcloneClient:
    """Routes the client's sync calls into an in-memory transport; the RC daemon is stood in by ``handler``."""
    client = RcloneClient(base_url="http://rclone:5572")
    transport = httpx.MockTransport(handler)

    def fake_client(**kwargs) -> httpx.Client:
        kwargs.pop("auth", None)
        return _RealClient(transport=transport, **kwargs)

    with patch("swiss_ai_hub.pipeline.resources.rclone.rclone_client.httpx.Client", fake_client):
        yield client


class TestUpsertRemote:
    def test_replaces_the_remote_with_obscured_passwords_and_without_prompting(self):
        seen: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["body"] = request.read()
            return httpx.Response(200, json={})

        for client in _client(handler):
            client.upsert_remote(
                RcloneSourceConfig(
                    name="rclone_hrdocs", backend_type=RcloneBackendType.SFTP, options={"host": "h", "pass": "p"}
                )
            )

        assert seen["url"] == "http://rclone:5572/config/create"
        body = json.loads(seen["body"])
        assert body["opt"] == {"obscure": True, "nonInteractive": True}
        assert body["name"] == "rclone_hrdocs"
        assert body["parameters"] == {"host": "h", "pass": "p"}

    def test_a_backend_asking_an_interactive_question_is_reported_as_needing_a_token(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"State": "*oauth", "Option": {"Name": "config_token"}})

        for client in _client(handler):
            with pytest.raises(ValueError, match="pre-obtained token"):
                client.upsert_remote(RcloneSourceConfig(name="r", backend_type=RcloneBackendType.ONEDRIVE, options={}))

    def test_an_rclone_error_surfaces_the_daemons_message_not_the_request(self):
        """rclone echoes the request under ``input`` in every error body, credentials included."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                500,
                json={
                    "error": "didn't find backend",
                    "input": {"name": "r", "parameters": {"secret_access_key": "TOPSECRET"}},
                    "status": 500,
                },
            )

        for client in _client(handler):
            with pytest.raises(RuntimeError, match="didn't find backend") as exc_info:
                client.upsert_remote(
                    RcloneSourceConfig(
                        name="r", backend_type=RcloneBackendType.S3, options={"secret_access_key": "TOPSECRET"}
                    )
                )
        assert "TOPSECRET" not in str(exc_info.value)

    def test_a_non_json_error_body_falls_back_to_the_status_phrase(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(502, text="<html>Bad Gateway</html>")

        for client in _client(handler):
            with pytest.raises(RuntimeError, match="HTTP 502: Bad Gateway"):
                client.delete_remote("r")


class TestGetAndDeleteRemote:
    def test_get_returns_none_for_an_unknown_remote(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={})

        for client in _client(handler):
            assert client.get_remote("nope") is None

    def test_delete_posts_the_name(self):
        seen: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["body"] = request.read()
            return httpx.Response(200, json={})

        for client in _client(handler):
            client.delete_remote("rclone_hrdocs")

        assert seen["url"].endswith("/config/delete")
        assert json.loads(seen["body"]) == {"name": "rclone_hrdocs"}

    def test_the_shared_drive_question_is_answered_with_no_and_the_remote_completes(self):
        requests: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            requests.append(body)
            if body["opt"].get("continue"):
                return httpx.Response(200, json={})
            return httpx.Response(200, json={"State": "teamdrive_ok", "Option": {"Name": "config_change_team_drive"}})

        for client in _client(handler):
            client.upsert_remote(
                RcloneSourceConfig(
                    name="r", backend_type=RcloneBackendType.DRIVE, options={"service_account_credentials": "{}"}
                )
            )

        assert [r["opt"].get("continue") for r in requests] == [None, True]
        assert requests[1]["opt"]["state"] == "teamdrive_ok"
        assert requests[1]["opt"]["result"] == "false"
        assert requests[1]["parameters"] == {"service_account_credentials": "{}"}

    def test_a_question_that_repeats_after_its_answer_is_reported_not_looped(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"State": "teamdrive_ok", "Option": {"Name": "config_change_team_drive"}})

        for client in _client(handler):
            with pytest.raises(ValueError, match="config_change_team_drive"):
                client.upsert_remote(RcloneSourceConfig(name="r", backend_type=RcloneBackendType.DRIVE, options={}))
