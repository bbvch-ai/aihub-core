from datetime import datetime, timezone, timedelta

from bson import ObjectId
from mongoengine import connect, disconnect

from aihub_api.routes.token.TokenService import TokenService
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.user.UserEntity import UserEntity

cosmos_conn_singleton = CosmosAccess()
host = cosmos_conn_singleton.get_connection_string()
connect(db=ApiConfig().DB_NAME, host=host)

user_name = "AI-Hub Admin"
token_name = "AI-Hub Admin Token"
expiry = datetime.now(timezone.utc) + timedelta(days=365)
roles = ["AllAgents"]

user = AuthenticatedUser(
    oid=str(ObjectId()),
    name=user_name,
    preferred_username="admin@ai-hub.bbv.ch",
    roles=roles,
)
UserEntity.ensure_user_exists(
    oid=user.oid,
    name=user.name,
    email=user.preferred_username,
    roles=user.roles,
)

token = TokenService.create_token(token_name, expiry, user)
print(token.token)

disconnect()
