# ruff: noqa: E402
"""Seed a ready-to-demo McpReactAgent profile straight into MongoDB.

Writes an agent profile into the ``agent_configs`` collection so the MCP user-token demo can run
without clicking through the Admin UI. Pair it with ``dummy_mcp_server.py`` and the
``app/mcp_react_agent`` runner. Re-running it replaces the existing profile.
"""

import os
from pathlib import Path


def _load_dotenv() -> None:
    """Load the repo .env so MongoSettings/AIHubSettings resolve as the running services do."""
    path = Path(__file__).resolve()
    while path != path.parent and not (path / ".env").exists():
        path = path.parent
    env_file = path / ".env"
    if not env_file.exists():
        raise FileNotFoundError("No .env at the repo root — copy .env.dev to .env first.")
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_dotenv()

from mongoengine import connect

from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.mcp import McpClientConfig
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument

from swiss_ai_hub.agent.agents.mcp_react_agent import McpReactAgentConfig

AGENT_CLASS = "McpReactAgent"
AGENT_ID = "mcp-react-demo"


def main() -> None:
    settings = AIHubSettings()
    connect(
        db=settings.MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )

    config = McpReactAgentConfig(
        agent_id=AGENT_ID,
        name=LocaleString(en="MCP React Demo"),
        description=LocaleString(en="Demo profile for the MCP user-token passthrough."),
        icon="mage:robot",
        mcp=McpClientConfig(
            name="demo-tools",
            url="http://127.0.0.1:9090/mcp",
            auth_mode="user_token",
        ),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
    )

    AgentConfigEntityDocument.delete_if_exists_for_class_and_id(AGENT_CLASS, AGENT_ID)
    AgentConfigEntityDocument.from_agent_config(config, agent_class=AGENT_CLASS).save()

    print(f"Seeded agent profile '{AGENT_CLASS}/{AGENT_ID}' into db '{settings.MONGO_MAIN_DB_NAME}'.")
    print(f"Call it from the API with model '{AGENT_CLASS}/{AGENT_ID}'.")


if __name__ == "__main__":
    main()
