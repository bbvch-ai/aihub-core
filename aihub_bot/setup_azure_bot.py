import argparse
import json
import subprocess
from typing import Optional

import sys
from azure.identity import DefaultAzureCredential
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.resource import SubscriptionClient
from pymongo import MongoClient


def run_command(cmd):
    """Run a shell command and return its stdout, or exit if the command fails."""
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    if result.returncode != 0:
        print(f"Error running command:\n{result.stderr}")
        sys.exit(result.returncode)
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
    api_endpoint: str,
    api_app_name: str,
    location: str,
    tenant_id: Optional[str],
):
    # Compute the bot endpoint similar to the original ARM template logic.
    bot_endpoint = f"https://{api_app_name}.azurewebsites.net{api_endpoint}"
    print(f"Creating Azure Bot resource with endpoint: {bot_endpoint} ...")
    # fmt: off
    cmd = [
        "az", "bot", "create",
        "--app-type", get_app_type(tenant_id),
        "--appid", app_id,
        "--name", bot_name,
        "--resource-group", resource_group,
        "--display-name", bot_name,
        "--endpoint", bot_endpoint,
        "--location", location,
        "--sku", "F0",
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


def save_credentials_in_cosmos(
    cosmos_name: str,
    api_endpoint: str,
    app_id: str,
    app_password: str,
    subscription_name: str,
    resource_group: str,
    tenant_id: Optional[str],
):
    print("Saving credentials in Cosmos DB...")
    credential = DefaultAzureCredential()
    subscription_client = SubscriptionClient(credential)
    subscriptions = subscription_client.subscriptions.list()
    subscription_id = None
    for subscription in subscriptions:
        if subscription.display_name == subscription_name:
            subscription_id = subscription.subscription_id
            break
    cosmos_client = CosmosDBManagementClient(credential, subscription_id)
    # Retrieve the connection string
    database_accounts = cosmos_client.database_accounts
    keys = database_accounts.list_connection_strings(resource_group, cosmos_name)
    connection_string = keys.connection_strings[0].connection_string
    client = MongoClient(connection_string)
    database = client["aihub_bot"]
    collection = database.get_collection("paths")
    document = {
        "path": api_endpoint,
        "credentials": {
            "APP_TYPE": get_app_type(tenant_id),
            "APP_ID": app_id,
            "APP_PASSWORD": app_password,
            "APP_TENANTID": tenant_id,
        },
    }
    _filter = {"path": api_endpoint}
    payload = {"$set": document}
    collection.update_one(_filter, payload, upsert=True)
    print("Credentials successfully saved in Cosmos DB.")


def main():
    parser = argparse.ArgumentParser(
        description="Set up an Azure Bot using the Azure CLI by creating an Azure AD app registration and saving its credentials to Cosmos DB."
    )
    parser.add_argument("--resource-group", "-rg", required=True, help="Name of the Azure resource group.")
    parser.add_argument("--bot-name", "-bot", required=True, help="Name for the Azure Bot.")
    parser.add_argument(
        "--api-endpoint", "-api", required=True, help="API endpoint for the bot (e.g. '/api/messages')."
    )
    parser.add_argument("--app-name", "-app", required=True, help="Name of the Bot API App (e.g. 'aihub-app-sui-bot').")
    parser.add_argument(
        "--location", "-loc", default="westeurope", help="Azure location for the bot (default: 'westeurope')."
    )
    parser.add_argument("--tenant-id", "-tid", default=None, help="Azure tenant ID for the Azure Bot (default: None).")

    # Cosmos DB parameters passed as arguments.
    parser.add_argument("--cosmos-name", "-cos", required=True, help="Cosmos DB account name.")
    parser.add_argument("--subscription-name", "-sub", required=True, help="Azure subscription name.")

    args = parser.parse_args()

    # Create the Azure AD app registration and reset its credentials.
    app_id = create_app_registration(args.bot_name, args.tenant_id)
    app_password = reset_app_credentials(app_id)
    print(f"Using newly created app registration credentials:\n  App ID: {app_id}\n  Password: {app_password}")

    # Save the credentials in Cosmos DB.
    save_credentials_in_cosmos(
        args.cosmos_name,
        args.api_endpoint,
        app_id,
        app_password,
        args.subscription_name,
        args.resource_group,
        args.tenant_id,
    )

    # Create the Azure Bot resource using a direct az command.
    create_bot_resource(
        args.resource_group,
        args.bot_name,
        app_id,
        args.api_endpoint,
        args.app_name,
        args.location,
        args.tenant_id,
    )


if __name__ == "__main__":
    main()
