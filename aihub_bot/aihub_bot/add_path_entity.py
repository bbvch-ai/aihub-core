"""
Script to add the bot_in_the_loop PathEntity to MongoDB.

Usage:
    uv run python aihub_bot/add_path_entity.py

Reads credentials from environment variables (or .env file):
    - BOT_APP_ID
    - BOT_APP_PASSWORD
    - BOT_TENANT_ID
    - MONGO_CONNECTION_STRING
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

"""
Each path entity is associated with a specific API endpoint and has its own set of credentials.

BITL PATH: /api/v1/bot_in_the_loop/response
OPENAI PATH: /api/v1/openai/chat/completions/json?model_name=<model>
OPENAI STREAMING PATH: /api/v1/openai/chat/completions/stream?model_name=<model>
"""
MODEL = "text-generation/gpt-oss-120b"
PATH = f"/api/v1/openai/chat/completions/json?model_name={MODEL}"


def main():
    client = MongoClient(os.environ["MONGO_CONNECTION_STRING"])
    collection = client["aihub"]["bot_paths"]

    document = {
        "path": PATH,
        "credentials": {
            "APP_TYPE": "SingleTenant",
            "APP_ID": os.environ["BOT_APP_ID"],
            "APP_PASSWORD": os.environ["BOT_APP_PASSWORD"],
            "APP_TENANTID": os.environ["BOT_TENANT_ID"],
        },
    }

    result = collection.update_one({"path": PATH}, {"$set": document}, upsert=True)
    print(f"{'Created' if result.upserted_id else 'Updated'} path entity for '{PATH}'")


if __name__ == "__main__":
    main()
