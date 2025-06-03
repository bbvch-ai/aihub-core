import subprocess
from datetime import datetime, timezone, timedelta

from mongoengine import connect, disconnect

from aihub_api.routes.token.TokenService import TokenService
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.user.UserEntity import UserEntity


def get_azure_cli_user_info():
    """Fetches user information using Azure CLI."""
    try:
        oid_process = subprocess.run(
            ["az", "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"],
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        )
        user_oid = oid_process.stdout.strip()

        name_process = subprocess.run(
            ["az", "ad", "signed-in-user", "show", "--query", "displayName", "-o", "tsv"],
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        )
        user_name_cli = name_process.stdout.strip()

        preferred_username_process = subprocess.run(
            ["az", "ad", "signed-in-user", "show", "--query", "userPrincipalName", "-o", "tsv"],
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        )
        user_preferred_username = preferred_username_process.stdout.strip()

        if not all([user_oid, user_name_cli, user_preferred_username]):
            raise ValueError("Failed to retrieve complete user information from Azure CLI.")

        return user_oid, user_name_cli, user_preferred_username

    except subprocess.CalledProcessError as e:
        print(f"Azure CLI command failed: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return None, None, None
    except FileNotFoundError:
        print("Azure CLI not found. Make sure it's installed and in your PATH.")
        return None, None, None
    except ValueError as e:
        print(e)
        return None, None, None



cli_user_oid, cli_user_name, cli_user_preferred_username = get_azure_cli_user_info()

if not all([cli_user_oid, cli_user_name, cli_user_preferred_username]):
    print("Exiting script due to missing Azure CLI user information.")
    exit()

cosmos_conn_singleton = CosmosAccess()
host = cosmos_conn_singleton.get_connection_string()
connect(db=ApiConfig().DB_NAME, host=host)

user_name = cli_user_name
token_name = f"{cli_user_name} Token"
expiry = datetime.now(timezone.utc) + timedelta(days=365)
roles = ["AllAgents"]

user = AuthenticatedUser(
    oid=cli_user_oid,
    name=cli_user_name,
    preferred_username=cli_user_preferred_username,
    roles=roles,
)
UserEntity.ensure_user_exists(
    oid=user.oid,
    name=user.name,
    email=user.preferred_username,
    roles=user.roles,
)

token = TokenService.create_token(token_name, expiry, user)
print(f"Generated token for user {user.name} ({user.preferred_username}):")
print(token.token)

disconnect()
