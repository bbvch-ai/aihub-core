from datetime import datetime, timezone, timedelta

from bson import ObjectId
from mongoengine import connect, disconnect

from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.access.entities.BearerToken import BearerToken, ApiUser

cosmos_conn_singleton = CosmosAccess()
host = cosmos_conn_singleton.get_connection_string()
connect(db=ApiConfig().DB_NAME, host=host)

user_name = "AI-Hub Admin"
token_name = "AI-Hub Admin Token"
expiry = datetime.now(timezone.utc) + timedelta(days=365)
roles = ["AllAgents"]

user = ApiUser(
    oid=str(ObjectId()),
    name=user_name,
    preferred_username="admin@ai-hub.bbv.ch",
    roles=roles,
)
token_obj = BearerToken.create_new_token(token_name, expiry, user, roles)
print(token_obj.token)

disconnect()
