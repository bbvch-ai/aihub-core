"""The patched sandbox's file API reaches only the requesting user's own home, links resolved.

Runs against a sandbox built from this directory, so it needs one running:
    docker build -t open-terminal-office:test infra/deployment/docker/open-terminal
    docker run -d --rm --name ot-test -e OPEN_TERMINAL_MULTI_USER=true -e OPEN_TERMINAL_API_KEY=test-key \
        -p 127.0.0.1:18200:8000 open-terminal-office:test
    OPEN_TERMINAL_TEST_URL=http://127.0.0.1:18200 OPEN_TERMINAL_TEST_KEY=test-key \
        uv run pytest infra/deployment/docker/open-terminal -v
"""

import os
import uuid

import httpx
import pytest

URL = os.environ.get("OPEN_TERMINAL_TEST_URL", "")
KEY = os.environ.get("OPEN_TERMINAL_TEST_KEY", "")

pytestmark = pytest.mark.skipif(not URL, reason="needs a running patched sandbox, see the module docstring")


def _user(name: str) -> httpx.Client:
    user_id = f"{name}{uuid.uuid4().hex[:4]}-{uuid.uuid4()}"
    return httpx.Client(base_url=URL, headers={"Authorization": f"Bearer {KEY}", "X-User-Id": user_id}, timeout=30)


def _run(user: httpx.Client, command: str) -> str:
    result = user.post("/execute", params={"wait": 10}, json={"command": command}).json()
    return "".join(chunk["data"] for chunk in result["output"])


@pytest.fixture
def victim() -> httpx.Client:
    victim = _user("vict")
    assert victim.post("/files/write", json={"path": "secret.txt", "content": "private"}).is_success
    return victim


@pytest.fixture
def victim_file(victim: httpx.Client) -> str:
    return f"{victim.get('/files/list').json()['dir']}/secret.txt"


def test_a_link_into_another_home_is_refused(victim_file: str) -> None:
    attacker = _user("attk")
    _run(attacker, f"ln -s {victim_file} link.txt")

    for endpoint in ("/files/read", "/files/view"):
        response = attacker.get(endpoint, params={"path": "link.txt"})
        assert response.status_code == 403, endpoint
        assert b"private" not in response.content


def test_writing_through_a_link_into_another_home_is_refused(victim: httpx.Client, victim_file: str) -> None:
    attacker = _user("attk")
    _run(attacker, f"ln -s {victim_file} link.txt")

    assert not attacker.post("/files/write", json={"path": "link.txt", "content": "overwritten"}).is_success
    assert victim.get("/files/view", params={"path": "secret.txt"}).content == b"private"


def test_searching_through_a_link_into_another_home_is_refused(victim_file: str) -> None:
    attacker = _user("attk")
    _run(attacker, f"ln -s {victim_file} link.txt")
    _run(attacker, f"ln -s {victim_file.rsplit('/', 1)[0]} victimdir")

    grep = attacker.get("/files/grep", params={"query": "private", "path": "link.txt"})
    assert grep.status_code == 403 and b"private" not in grep.content
    glob = attacker.get("/files/glob", params={"pattern": "*", "path": "victimdir"})
    assert glob.status_code == 403
    own = attacker.get("/files/glob", params={"pattern": "*", "path": "."})
    assert "secret.txt" not in own.text


def test_searching_the_server_environment_is_refused() -> None:
    attacker = _user("attk")

    assert attacker.get("/files/grep", params={"query": "OPEN_TERMINAL", "path": "/proc/1/environ"}).status_code == 403
    assert attacker.get("/files/glob", params={"pattern": "*", "path": "/proc/1"}).status_code == 403


def test_the_server_environment_with_the_api_key_is_unreachable() -> None:
    attacker = _user("attk")

    for path in ("/proc/1/environ", "/etc/passwd", "/tmp"):
        assert attacker.get("/files/view", params={"path": path}).status_code in (403, 404), path


def test_the_user_still_works_freely_in_their_own_home() -> None:
    user = _user("ownr")
    assert user.post("/files/write", json={"path": "work/notes.txt", "content": "mine"}).is_success
    _run(user, "ln -s work/notes.txt shortcut.txt")

    assert user.get("/files/view", params={"path": "work/notes.txt"}).content == b"mine"
    assert user.get("/files/view", params={"path": "shortcut.txt"}).content == b"mine"
    assert {entry["name"] for entry in user.get("/files/list").json()["entries"]} >= {"work", "shortcut.txt"}


def test_shell_commands_still_see_the_system() -> None:
    user = _user("shel")

    assert "root:" in _run(user, "head -1 /etc/passwd")
