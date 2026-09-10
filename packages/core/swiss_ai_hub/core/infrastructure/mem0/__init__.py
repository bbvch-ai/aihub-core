import os

# mem0 reads MEM0_TELEMETRY once, at import time of mem0.memory.telemetry, and defaults it to
# True — which builds a PostHog client against us.i.posthog.com and reports collection name,
# store/model class names and host details on every memory init. Deployments set the variable
# explicitly, but this package initialises before any of our modules can import mem0, so the
# default also holds for ad-hoc runs, playground scripts and tests. setdefault leaves an
# explicit operator opt-in untouched.
os.environ.setdefault("MEM0_TELEMETRY", "False")
