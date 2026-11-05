"""Create the e2e knowledge databases and collections through the API, as an administrator would."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import COLLECTIONS, DATABASE_CONFIGURATION, DB_MAIN, DB_OTHER, api  # noqa: E402


def main() -> None:
    with api() as client:
        for database in (DB_MAIN, DB_OTHER):
            response = client.post(
                f"/knowledge/databases/{database}",
                json={
                    "ingestor": "document_ingestion",
                    "configuration": {
                        "name": {"en": f"#1888 e2e {database}"},
                        "description": {"en": "Throwaway database for the knowledge extraction e2e"},
                        **DATABASE_CONFIGURATION,
                    },
                },
            )
            print("create database", database, response.status_code, response.text[:300])
            response.raise_for_status()

        for namespace, (database, folder) in COLLECTIONS.items():
            response = client.post(
                f"/knowledge/databases/{database}/namespaces/{namespace}",
                json={"folder_name": folder, "display_name": f"{namespace} ({folder})"},
            )
            print("create namespace", database, namespace, folder, response.status_code, response.text[:200])
            response.raise_for_status()

        listed = {db["name"]: [ns["name"] for ns in db["namespaces"]] for db in client.get("/knowledge/databases").json()}
        print({db: listed.get(db) for db in (DB_MAIN, DB_OTHER)})


if __name__ == "__main__":
    main()
