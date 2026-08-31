"""Unit tests for the mem0 anonymous-telemetry default (issue #1635).

mem0 reads `MEM0_TELEMETRY` once, when `mem0.memory.telemetry` is imported, and defaults it to True —
which builds a PostHog client against us.i.posthog.com. The `swiss_ai_hub.core.infrastructure.mem0`
package flips that default before mem0 can be imported, so both cases have to run in a fresh
interpreter to observe the real import order.
"""

import subprocess
import sys

PROBE = (
    "import swiss_ai_hub.core.infrastructure.mem0.mem0_service;"
    "import mem0.memory.telemetry as t;"
    "print(t.MEM0_TELEMETRY, t.client_telemetry.posthog is None)"
)


def _probe(env_value: str | None) -> str:
    env = {"PATH": "/usr/bin:/bin", "HOME": "/tmp"}
    if env_value is not None:
        env["MEM0_TELEMETRY"] = env_value
    result = subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True, env=env, check=True)
    return result.stdout.strip().splitlines()[-1]


def test_telemetry_off_without_env_var():
    """Importing our mem0 package must leave mem0 with telemetry off and no PostHog client."""
    assert _probe(None) == "False True"


def test_explicit_opt_in_is_preserved():
    """The default must not override an operator who deliberately turns telemetry back on."""
    assert _probe("True") == "True False"
