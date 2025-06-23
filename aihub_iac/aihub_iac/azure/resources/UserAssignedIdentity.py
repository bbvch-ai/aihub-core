from pulumi_azure_native import cognitiveservices, cosmosdb, managedidentity, search, storage

from aihub_iac.azure.constants.roles import ROLES
from aihub_iac.azure.providers.RoleProvider import RoleProvider
from aihub_iac.azure.resources.AISearch import AISearch
from aihub_iac.azure.resources.CosmosDocstore import CosmosDocstore
from aihub_iac.azure.resources.DataLakeStorage import DataLakeStorage
from aihub_iac.azure.resources.OpenAI import OpenAI


class UserAssignedIdentity:
    def __init__(
        self,
        resource_group,
        location,
        subscription_id,
        stack,
        project_name=None,
        location_short_name=None,
        id_name=None,
    ):
        self.resource_group = resource_group
        self.location = location
        self.project_name = project_name
        self.location_short_name = location_short_name
        self.user_identity_name = f"{self.project_name}-id-{self.location_short_name}-{id_name}"
        self.user_identity = managedidentity.UserAssignedIdentity(
            resource_name=self.user_identity_name,
            resource_group_name=self.resource_group,
            location=self.location,
            tags={
                "Stack": stack,
            },
        )
        self.role_assigner = RoleProvider(subscription_id)

    def assign_role_to_identity(self, role: ROLES, scope_id, scope_name):
        self.role_assigner.assign(
            resource_name=f"{self.user_identity_name}_{role.name}_{scope_name}",
            role_id=role.value,
            assignee_principal_id=self.user_identity.principal_id,
            scope_id=scope_id,
        )

    def assign_openai_user(self, account_name: str | None = None, resource_group: str | None = None):
        openai_account = cognitiveservices.get_account(
            resource_group_name=resource_group or self.resource_group,
            account_name=account_name or OpenAI.name(self.project_name, self.location_short_name),
        )
        self.assign_role_to_identity(ROLES.OPENAI_USER, openai_account.id, openai_account.name)

    def assign_ai_search_roles(self, account_name: str | None = None, resource_group: str | None = None):
        aisearch_account = search.get_service(
            resource_group_name=resource_group or self.resource_group,
            search_service_name=account_name or AISearch.name(self.project_name, self.location_short_name),
        )
        self.assign_role_to_identity(ROLES.CONTRIBUTOR_ROLE_ID, aisearch_account.id, aisearch_account.name)
        self.assign_role_to_identity(ROLES.SEARCH_INDEX_DATA_CONTRIBUTOR, aisearch_account.id, aisearch_account.name)

    def assign_docstore_roles(self, account_name: str | None = None, resource_group: str | None = None):
        docstore_account = cosmosdb.get_database_account(
            resource_group_name=resource_group or self.resource_group,
            account_name=account_name or CosmosDocstore.name(self.project_name, self.location_short_name),
        )
        self.assign_role_to_identity(ROLES.CONTRIBUTOR_ROLE_ID, docstore_account.id, docstore_account.name)
        self.assign_role_to_identity(ROLES.DB_ACCOUNT_CONTRIBUTOR_ROLE_ID, docstore_account.id, docstore_account.name)

    def assign_datalake_roles(
        self,
        account_name: str | None = None,
        resource_group: str | None = None,
        role: ROLES = ROLES.STORAGE_BLOB_DATA_CONTRIBUTOR,
    ):
        data_lake_account = storage.get_storage_account(
            account_name=account_name or DataLakeStorage.name(self.project_name, self.location_short_name),
            resource_group_name=resource_group or self.resource_group,
        )
        self.assign_role_to_identity(role, data_lake_account.id, data_lake_account.name)

    @property
    def client_id(self):
        return self.user_identity.client_id
