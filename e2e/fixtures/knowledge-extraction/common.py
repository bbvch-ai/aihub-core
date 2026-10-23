"""Shared constants and clients for the knowledge extraction e2e fixtures. Run every script from the repository root
with .env loaded (see README.md)."""

import os
from pathlib import Path

import boto3
import httpx
from mongoengine import connect
from mongoengine.connection import ConnectionFailure, get_connection

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "corpus"
GROUND_TRUTH = ROOT / "ground_truth.json"
GROUND_TRUTH_CONTRACTS = ROOT / "ground_truth_contracts.json"
GROUND_TRUTH_SLAS = ROOT / "ground_truth_slas.json"
API = os.environ.get("E2E_API_URL", "http://localhost:8000/api/v1") + "/default"
HEADERS = {"Authorization": f"Bearer {os.environ['SUPERUSER_TOKEN']}"}

DB_MAIN = "kxe2e"
DB_OTHER = "kxe2eb"

COLLECTIONS = {
    "finance": (DB_MAIN, "finance"),
    "legal": (DB_MAIN, "legal"),
    "hr": (DB_OTHER, "hr"),
}

BULK_FILES = 30

DATABASE_CONFIGURATION = {
    "llm_model": "text-generation/gemma-4-31B-it",
    "embedding_model": "embedding/bge-m3",
    "with_summary_nodes": False,
    "with_table_refinement": False,
    "with_figure_descriptions": False,
}


def seeded() -> dict[str, list[str]]:
    """Every file of the corpus, by collection, as the generator wrote it."""
    return {
        collection: sorted(str(path.relative_to(CORPUS / collection)) for path in (CORPUS / collection).rglob("*") if path.is_file())
        for collection in COLLECTIONS
        if (CORPUS / collection).exists()
    }


def api() -> httpx.Client:
    return httpx.Client(base_url=API, headers=HEADERS, timeout=600)


def s3():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_STORAGE_ENDPOINT"],
        aws_access_key_id=os.environ["S3_STORAGE_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_STORAGE_SECRET_KEY"],
        region_name="us-east-1",
    )


def connect_like_an_agent() -> None:
    try:
        get_connection()
    except ConnectionFailure:
        connect(
            db=os.environ.get("AIHUB_MONGO_MAIN_DB_NAME", "aihub"),
            host=os.environ["MONGO_CONNECTION_STRING"],
            uuidRepresentation="standard",
        )


def object_key(collection: str, path: str) -> str:
    return f"{COLLECTIONS[collection][1]}/{path}"


def source(collection: str, path: str) -> str:
    db, folder = COLLECTIONS[collection]
    return f"s3://{db}/{folder}/{path}"
