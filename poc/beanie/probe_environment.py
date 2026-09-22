"""Collects the environment facts every check in this spike cites.

Reads the connection string from the repo's own settings rather than a hardcoded
literal, so the recorded environment is the one the platform would actually use.
Prints no credentials: the connection string is reported as host/port only.
"""

import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from urllib.parse import urlsplit

from pymongo import MongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB_NAME = "aihub_beanie_spike"


def package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not installed"


def redacted_target(connection_string: str) -> str:
    parts = urlsplit(connection_string)
    host = parts.hostname or "?"
    port = parts.port or "?"
    return f"{host}:{port}"


def main() -> None:
    connection_string = MongoSettings().CONNECTION_STRING.get_secret_value()

    print("## Host")
    print(f"python            {sys.version.split()[0]}")
    print(f"platform          {platform.platform()}")
    print(f"utc_offset        {-__import__('time').timezone // 3600:+d}h (standard time)")

    print("\n## Packages")
    for name in ("beanie", "pymongo", "motor", "mongoengine", "pydantic"):
        print(f"{name:<18}{package_version(name)}")

    print("\n## Database")
    print(f"target            {redacted_target(connection_string)}")
    print(f"spike_db          {SPIKE_DB_NAME}")

    client: MongoClient = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
    build_info = client.admin.command("buildInfo")
    print(f"version           {build_info.get('version')}")
    print(f"ferretdb          {build_info.get('ferretdb', {})}")
    print(f"maxWireVersion    {client.admin.command('hello').get('maxWireVersion')}")
    print(f"databases         {sorted(client.list_database_names())}")
    print(f"spike_db_exists   {SPIKE_DB_NAME in client.list_database_names()}")
    client.close()


if __name__ == "__main__":
    main()
