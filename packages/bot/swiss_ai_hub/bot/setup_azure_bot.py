import argparse
import json
import subprocess
import sys

from pymongo import MongoClient


def run_command(cmd, parse_json=True):
    """
    Run a shell command and return its stdout, or exit if the command fails.
    If parse_json is True, attempt to parse the output as JSON.
    """
    cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
    print(f"Running command: {cmd_str}")

    # Use shell=False for security when passing command as a list
    shell_mode = isinstance(cmd, str)
    result = subprocess.run(cmd, capture_output=True, text=True, shell=shell_mode, check=True)

    output = result.stdout

    if parse_json:
        try:
            # Try to find JSON in the output - look for first '{' character
            json_start = output.find("{")
            if json_start >= 0:
                json_content = output[json_start:]
                return json.loads(json_content)
            else:
                print("No JSON content found in command output.")
                print(f"Output: {output}")
                sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Failed to parse command output as JSON: {e}")
            print(f"Raw output: {output}")
            sys.exit(1)

    return output


def create_app_registration(bot_name: str, tenant_id: str | None) -> str:
    print(f"Creating Azure AD app registration for bot '{bot_name}'...")

    sign_in_audience = "AzureADMyOrg" if tenant_id is not None else "AzureADandPersonalMicrosoftAccount"

    # First check if app already exists to avoid getting the welcome message
    check_cmd = ["az", "ad", "app", "list", "--display-name", bot_name, "--query", "[0].appId", "--output", "tsv"]

    try:
        existing_app_id = run_command(check_cmd, parse_json=False).strip()
        if existing_app_id and existing_app_id != "":
            print(f"Found existing Azure AD app with appId: {existing_app_id}")
            return existing_app_id
    except subprocess.CalledProcessError:
        # If command failed, app might not exist, continue to creation
        pass

    # fmt: off
    cmd = [
        "az", "ad", "app", "create",
        "--display-name", bot_name,
        "--sign-in-audience", sign_in_audience,
    ]
    # fmt: on

    app_info = run_command(cmd)
    app_id = app_info.get("appId")
    if not app_id:
        print("Failed to retrieve appId from app registration creation output.")
        sys.exit(1)
    print(f"Created Azure AD app with appId: {app_id}")

    # fmt: off
    cmd = [
        "az", "ad", "sp", "create",
        "--id", app_id,
    ]
    # fmt: on
    run_command(cmd)
    print(f"Created service principal for Azure AD app with appId: {app_id}")
    return app_id


def reset_app_credentials(app_id: str) -> str:
    print(f"Resetting credentials for Azure AD app '{app_id}'...")

    # fmt: off
    cmd = [
        "az", "ad", "app", "credential", "reset",
        "--id", app_id,
    ]
    # fmt: on

    app_creds = run_command(cmd)
    app_password = app_creds.get("password")
    if not app_password:
        print("Failed to retrieve password from app credential reset output.")
        sys.exit(1)
    print(f"Reset credentials for Azure AD app with password: {app_password}")
    return app_password


def get_app_type(tenant_id: str | None) -> str:
    return "SingleTenant" if tenant_id is not None else "MultiTenant"


def create_bot_resource(
    resource_group: str,
    bot_name: str,
    app_id: str,
    api_url: str,
    api_path: str,
    location: str,
    tenant_id: str | None,
    sku: str,
):
    print(f"Deleting existing Azure Bot resource '{bot_name}' if it exists...")
    # fmt: off
    delete_cmd = [
        "az", "bot", "delete",
        "--name", bot_name,
        "--resource-group", resource_group,
        "--yes",  # Auto-confirm the deletion
    ]
    # fmt: on
    try:
        run_command(delete_cmd, parse_json=False)
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

    bot_info = run_command(cmd)
    print(f"Created Azure Bot with info: {bot_info}")
    return bot_info


def save_credentials_in_mongo(
    connection_string: str,
    api_path: str,
    app_id: str,
    app_password: str,
    tenant_id: str | None,
    system_message: str | None = None,
    slack_token: str | None = None,
):
    print("Saving credentials in MongoDB...")
    client = MongoClient(connection_string)
    database = client["aihub"]
    collection = database.get_collection("bot_paths")
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
    if slack_token:
        document["slack_token"] = slack_token
    _filter = {"path": api_path}
    payload = {"$set": document}
    collection.update_one(_filter, payload, upsert=True)
    print("Credentials successfully saved in MongoDB.")


def main():
    parser = argparse.ArgumentParser(
        description="Set up an Azure Bot using the Azure CLI by creating an Azure AD app "
        "registration and saving its credentials to MongoDB."
    )
    parser.add_argument("--resource-group", "-rg", required=True, help="Name of the Azure resource group.")
    parser.add_argument("--bot-name", "-bot", required=True, help="Name for the Azure Bot.")
    parser.add_argument(
        "--token-path", "-path", required=True, help="API endpoint path for the bot (e.g. '/token/messages')."
    )
    parser.add_argument("--token-url", "-url", required=True, help="API URL for the bot (e.g. 'https://example.com').")
    parser.add_argument(
        "--location", "-loc", default="westeurope", help="Azure location for the bot (default: 'westeurope')."
    )
    parser.add_argument("--tenant-id", "-tid", default=None, help="Azure tenant ID for the Azure Bot (default: None).")
    parser.add_argument("--sku", "-sku", default="F0", help="Azure Bot SKU (default: 'F0').")

    # MongoDB parameters
    parser.add_argument(
        "--mongo-connection-string", "-mongo", required=True, help="MongoDB connection string (FerretDB compatible)."
    )

    # System message
    parser.add_argument("--system-message", "-sys", required=False, help="System message for the bot.")
    parser.add_argument("--system-message-file", "-sysf", required=False, help="File containing the system message.")

    # Slack OAuth token
    parser.add_argument("--slack-token", "-slack", required=False, help="Slack OAuth token for the bot.")

    args = parser.parse_args()

    app_id = create_app_registration(bot_name=args.bot_name, tenant_id=args.tenant_id)
    app_password = reset_app_credentials(app_id=app_id)
    print(f"Using app registration credentials:\n  App ID: {app_id}\n  Password: {app_password}")

    system_message = None
    if args.system_message:
        system_message = args.system_message
    elif args.system_message_file:
        with open(args.system_message_file) as f:
            system_message = f.read()

    save_credentials_in_mongo(
        connection_string=args.mongo_connection_string,
        api_path=args.token_path,
        app_id=app_id,
        app_password=app_password,
        tenant_id=args.tenant_id,
        system_message=system_message,
        slack_token=args.slack_token,
    )

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
