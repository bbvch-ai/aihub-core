import argparse
import json
import subprocess

import sys


def run_command(cmd):
    """Run a shell command and return its stdout, or exit if the command fails."""
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    if result.returncode != 0:
        print(f"Error running command:\n{result.stderr}")
        sys.exit(result.returncode)
    return result.stdout


def create_app_registration(bot_name) -> str:
    print(f"Creating Azure AD app registration for bot '{bot_name}'...")
    cmd = [
        "az",
        "ad",
        "app",
        "create",
        "--display-name",
        bot_name,
        "--sign-in-audience",
        "AzureADMyOrg",
    ]
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


def reset_app_credentials(app_id) -> str:
    print(f"Resetting credentials for Azure AD app '{app_id}'...")
    cmd = [
        "az",
        "ad",
        "app",
        "credential",
        "reset",
        "--id",
        app_id,
    ]
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


def create_bot_resource(resource_group, bot_name, app_id, api_endpoint, api_app_name, location):
    # Compute the bot endpoint similar to the original ARM template logic.
    bot_endpoint = f"https://{api_app_name}.azurewebsites.net{api_endpoint}"
    print(f"Creating Azure Bot resource with endpoint: {bot_endpoint} ...")

    # fmt: off
    cmd = [
        "az", "bot", "create",
        "--app-type", "MultiTenant",
        "--appid", app_id,
        "--name", bot_name,
        "--resource-group", resource_group,
        "--display-name", bot_name,
        "--endpoint", bot_endpoint,
        "--location", location,
        "--sku", "F0"
    ]
    # fmt: on

    output = run_command(cmd)
    try:
        bot_info = json.loads(output)
    except json.JSONDecodeError:
        print("Failed to parse bot creation output.")
        sys.exit(1)
    print(f"Created Azure Bot with info: {bot_info}")
    return bot_info


def main():
    parser = argparse.ArgumentParser(
        description="Set up an Azure Bot in a specified resource group using the Azure CLI, including creating an Azure AD app registration."
    )
    parser.add_argument("--resource-group", "-rg", required=True, help="Name of the Azure resource group.")
    parser.add_argument("--bot-name", "-bn", required=True, help="Name for the Azure Bot.")
    parser.add_argument(
        "--api-endpoint",
        "-api",
        required=True,
        help="API endpoint for the bot (e.g. '/api/messages').",
    )
    parser.add_argument(
        "--app-name",
        "-app",
        required=True,
        help="Name of the Bot API App (e.g. 'aihub-app-sui-bot').",
    )
    parser.add_argument(
        "--location", "-loc", default="westeurope", help="Azure location for the bot (default: 'westeurope')."
    )
    args = parser.parse_args()

    # Create the Azure AD app registration and reset its credentials.
    app_id = create_app_registration(args.bot_name)
    app_password = reset_app_credentials(app_id)
    print(f"Using newly created app registration credentials:\n  App ID: {app_id}\n  Password: {app_password}")

    # Create the Azure Bot resource using a direct az command.
    create_bot_resource(args.resource_group, args.bot_name, app_id, args.api_endpoint, args.app_name, args.location)


if __name__ == "__main__":
    main()
