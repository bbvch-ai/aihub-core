from enum import Enum


class ROLES(Enum):
    """
    Enum representing globally defined roles in Azure.

    These IDs correspond to specific roles that can be assigned to users or service principals
    within the Azure ecosystem. They are used to manage permissions and access control across
    various Azure resources. Each role is identified by a unique GUID globally on Azure.
    See the list of roles and their Ids at:
    https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
    """

    OPENAI_USER = "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"
    CONTRIBUTOR_ROLE_ID = "b24988ac-6180-42a0-ab88-20f7382dd24c"
    DB_ACCOUNT_CONTRIBUTOR_ROLE_ID = "5bd9cd88-fe45-4216-938b-f97437e15450"
    SEARCH_INDEX_DATA_CONTRIBUTOR = "8ebe5a00-799e-43f5-93ac-243d3dce84a7"
    STORAGE_BLOB_DATA_CONTRIBUTOR = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"
    STORAGE_BLOB_DATA_READER = "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1"
    STORAGE_BLOB_DELEGATOR = "db58b8e5-c6ad-4a2a-8342-4190687cbf4a"
    KEY_VAULT_SECRETS_USER = "4633458b-17de-408a-b874-0445c86b69e6"
