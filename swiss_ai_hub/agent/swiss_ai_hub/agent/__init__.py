"""Swiss AI Hub - Agent SDK."""

__version__ = "0.270.1"


def hello_agent() -> str:
    from swiss_ai_hub.core import hello_core

    return f"Hello from swiss_ai_hub.agent v{__version__}, core says: {hello_core()}"
