"""Paths callers hand the sandbox stay inside the user's home, whatever the sandbox would resolve beyond it."""

import pytest

from swiss_ai_hub.core.infrastructure.open_terminal.open_terminal_error import OpenTerminalError
from swiss_ai_hub.core.infrastructure.open_terminal.sandbox_home_path import SandboxHomePath

pytestmark = pytest.mark.unit


def test_a_relative_path_lies_under_its_base() -> None:
    assert SandboxHomePath.of("out/chart.png", "conversations/t1") == "conversations/t1/out/chart.png"
    assert SandboxHomePath.of("reports/q1.pdf") == "reports/q1.pdf"


def test_a_tilde_path_lies_in_the_home() -> None:
    assert SandboxHomePath.of("~/notes.txt", "conversations/t1") == "notes.txt"
    assert SandboxHomePath.of("~") == "."


@pytest.mark.parametrize("path", ["/etc/passwd", "/proc/1/environ", "../../../etc", "~/../other", "a\0b", ".."])
def test_a_path_outside_the_home_is_refused(path: str) -> None:
    with pytest.raises(OpenTerminalError) as refused:
        SandboxHomePath.of(path)
    assert refused.value.status_code == 400


@pytest.mark.parametrize("name", ["", ".", "..", "a/b", "x\0y"])
def test_a_name_is_a_single_plain_segment(name: str) -> None:
    with pytest.raises(OpenTerminalError):
        SandboxHomePath.name(name)


def test_a_plain_name_is_kept() -> None:
    assert SandboxHomePath.name("Q1 report.pdf") == "Q1 report.pdf"


@pytest.mark.parametrize("path", [".ssh/id_rsa", "notes/.env", "~/.config", "conversations/t1/.attached_files.json"])
def test_a_hidden_path_is_outside_the_user_s_files(path: str) -> None:
    with pytest.raises(OpenTerminalError, match="hidden"):
        SandboxHomePath.shown(path)


def test_a_shown_path_is_kept() -> None:
    assert SandboxHomePath.shown("reports/q1.pdf") == "reports/q1.pdf"
    assert SandboxHomePath.shown(".") == "."
