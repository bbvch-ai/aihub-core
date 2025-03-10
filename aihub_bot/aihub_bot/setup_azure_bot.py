import argparse
import json
import subprocess
from typing import Optional

import sys
from azure.identity import DefaultAzureCredential
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from pymongo import MongoClient


def run_command(cmd):
    """Run a shell command and return its stdout, or exit if the command fails."""
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True, check=True)
    return result.stdout


def create_app_registration(bot_name: str, tenant_id: Optional[str]) -> str:
    print(f"Creating Azure AD app registration for bot '{bot_name}'...")

    sign_in_audience = "AzureADMyOrg" if tenant_id is not None else "AzureADandPersonalMicrosoftAccount"

    # fmt: off
    cmd = [ "az", "ad", "app", "create",
        "--display-name", bot_name,
        "--sign-in-audience", sign_in_audience,
    ]
    # fmt: on

    output = run_command(cmd)
    try:
        app_info = json.loads(output)
    except json.JSONDecodeError:
        print("Failed to parse app creation output.")
        sys.exit(1)
    app_id = app_info.get("appId")
    if not app_id:
        print("Failed to retrieve appId from app registration creation output.")
        sys.exit(1)
    print(f"Created Azure AD app with appId: {app_id}")
    return app_id


def reset_app_credentials(app_id: str) -> str:
    print(f"Resetting credentials for Azure AD app '{app_id}'...")

    # fmt: off
    cmd = [
        "az", "ad", "app", "credential", "reset",
        "--id", app_id,
    ]
    # fmt: on

    output = run_command(cmd)
    try:
        app_creds = json.loads(output)
    except json.JSONDecodeError:
        print("Failed to parse app credential reset output.")
        sys.exit(1)
    app_password = app_creds.get("password")
    if not app_password:
        print("Failed to retrieve password from app credential reset output.")
        sys.exit(1)
    print(f"Reset credentials for Azure AD app with password: {app_password}")
    return app_password


def get_app_type(tenant_id: Optional[str]) -> str:
    return "SingleTenant" if tenant_id is not None else "MultiTenant"


def create_bot_resource(
    resource_group: str,
    bot_name: str,
    app_id: str,
    api_url: str,
    api_path: str,
    location: str,
    tenant_id: Optional[str],
    sku: str,
):
    print(f"Deleting existing Azure Bot resource '{bot_name}' if it exists...")
    # fmt: off
    delete_cmd = [
        "az", "bot", "delete",
        "--name", bot_name,
        "--resource-group", resource_group,
    ]
    # fmt: on
    try:
        run_command(delete_cmd)
        print(f"Deleted existing Azure Bot resource '{bot_name}'.")
    except subprocess.CalledProcessError:
        print(f"No existing Azure Bot resource '{bot_name}' found.")

    api_endpoint = f"{api_url}{api_path}"
    print(f"Creating Azure Bot resource with endpoint: {api_endpoint} ...")
    # fmt: off
    cmd = [
        "az", "bot", "create",
        "--app-type", get_app_type(tenant_id),
        "--appid", app_id,
        "--name", bot_name,
        "--resource-group", resource_group,
        "--display-name", bot_name,
        "--endpoint", api_endpoint,
        "--location", location,
        "--sku", sku,
    ]
    if tenant_id is not None:
        cmd.extend(["--tenant-id", tenant_id])
    # fmt: on

    output = run_command(cmd)
    try:
        bot_info = json.loads(output)
    except json.JSONDecodeError:
        print("Failed to parse bot creation output.")
        sys.exit(1)
    print(f"Created Azure Bot with info: {bot_info}")
    return bot_info


def save_credentials_in_mongo(
    connection_string: str,
    api_path: str,
    app_id: str,
    app_password: str,
    tenant_id: Optional[str],
    system_message: Optional[str] = None,
):
    print("Saving credentials in MongoDB...")
    client = MongoClient(connection_string)
    database = client["aihub_bot"]
    collection = database.get_collection("paths")
    document = {
        "path": api_path,
        "credentials": {
            "APP_TYPE": get_app_type(tenant_id),
            "APP_ID": app_id,
            "APP_PASSWORD": app_password,
            "APP_TENANTID": tenant_id,
        },
    }
    if system_message:
        document["system_message"] = system_message
    _filter = {"path": api_path}
    payload = {"$set": document}
    collection.update_one(_filter, payload, upsert=True)
    print("Credentials successfully saved in MongoDB.")


def save_credentials_in_cosmos(
    cosmos_name: str,
    api_path: str,
    app_id: str,
    app_password: str,
    subscription_id: str,
    resource_group: str,
    tenant_id: Optional[str],
    system_message: Optional[str] = None,
):
    print("Saving credentials in Cosmos DB...")
    credential = DefaultAzureCredential()
    cosmos_client = CosmosDBManagementClient(credential, subscription_id)
    # Retrieve the connection string
    database_accounts = cosmos_client.database_accounts
    keys = database_accounts.list_connection_strings(resource_group, cosmos_name)
    connection_string = keys.connection_strings[0].connection_string

    save_credentials_in_mongo(connection_string, api_path, app_id, app_password, tenant_id, system_message)
    print("Credentials successfully saved in Cosmos DB.")


def main():
    parser = argparse.ArgumentParser(
        description="Set up an Azure Bot using the Azure CLI by creating an Azure AD app registration and saving its credentials to Cosmos DB."
    )
    parser.add_argument("--resource-group", "-rg", required=True, help="Name of the Azure resource group.")
    parser.add_argument("--bot-name", "-bot", required=True, help="Name for the Azure Bot.")
    parser.add_argument(
        "--api-path", "-path", required=True, help="API endpoint path for the bot (e.g. '/api/messages')."
    )
    parser.add_argument("--api-url", "-url", required=True, help="API URL for the bot (e.g. 'https://example.com').")
    parser.add_argument(
        "--location", "-loc", default="westeurope", help="Azure location for the bot (default: 'westeurope')."
    )
    parser.add_argument("--tenant-id", "-tid", default=None, help="Azure tenant ID for the Azure Bot (default: None).")
    parser.add_argument("--sku", "-sku", default="F0", help="Azure Bot SKU (default: 'F0').")

    # Cosmos DB parameters
    parser.add_argument("--cosmos-name", "-cos", required=False, help="Cosmos DB account name.")
    parser.add_argument("--subscription-id", "-sub", required=False, help="Azure subscription ID.")

    # MongoDB parameters
    parser.add_argument("--mongo-connection-string", "-mongo", required=False, help="MongoDB connection string.")

    # System message
    parser.add_argument("--system-message", "-sys", required=False, help="System message for the bot.")
    parser.add_argument("--system-message-file", "-sysf", required=False, help="File containing the system message.")

    args = parser.parse_args()

    # Create the Azure AD app registration and reset its credentials.
    app_id = create_app_registration(bot_name=args.bot_name, tenant_id=args.tenant_id)
    app_password = reset_app_credentials(app_id=app_id)
    print(f"Using newly created app registration credentials:\n  App ID: {app_id}\n  Password: {app_password}")

    system_message = None
    if args.system_message:
        system_message = args.system_message
    elif args.system_message_file:
        with open(args.system_message_file, "r") as f:
            system_message = f.read()

    if args.mongo_connection_string:
        assert all(
            [not args.cosmos_name, not args.subscription_id]
        ), "Must specify either MongoDB connection string or Cosmos DB parameters."
        # Save the credentials in MongoDB.
        save_credentials_in_mongo(
            connection_string=args.mongo_connection_string,
            api_path=args.api_path,
            app_id=app_id,
            app_password=app_password,
            tenant_id=args.tenant_id,
            system_message=system_message,
        )
    else:
        assert all(
            [args.cosmos_name, args.subscription_id]
        ), "Must specify Cosmos DB parameters or MongoDB connection string."
        # Save the credentials in Cosmos DB.
        save_credentials_in_cosmos(
            cosmos_name=args.cosmos_name,
            api_path=args.api_path,
            app_id=app_id,
            app_password=app_password,
            subscription_id=args.subscription_id,
            resource_group=args.resource_group,
            tenant_id=args.tenant_id,
            system_message=system_message,
        )

    # Create the Azure Bot resource using a direct az command.
    create_bot_resource(
        resource_group=args.resource_group,
        bot_name=args.bot_name,
        app_id=app_id,
        api_url=args.api_url,
        api_path=args.api_path,
        location=args.location,
        tenant_id=args.tenant_id,
        sku=args.sku,
    )


if __name__ == "__main__":
    main()
