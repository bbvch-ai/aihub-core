import hashlib

from pulumi import Output
from pulumi_azure_native import authorization


class RoleProvider:
    def __init__(self, subscription_id=None, location_short_name=None):
        if subscription_id is not None:
            self.subscription_id = subscription_id

    @staticmethod
    def generate_deterministic_guid(*args):
        combined_string = "-".join(map(str, args))
        return hashlib.md5(combined_string.encode("utf-8")).hexdigest()[:32]

    def assign(self, resource_name: str, role_id: str, assignee_principal_id, scope_id):
        role_assignment_name = Output.all(resource_name, assignee_principal_id, role_id, scope_id).apply(
            lambda args: self.generate_deterministic_guid(*args)
        )

        authorization.RoleAssignment(
            resource_name=resource_name,
            role_assignment_name=role_assignment_name,
            scope=scope_id,
            principal_id=assignee_principal_id,
            principal_type=authorization.PrincipalType.SERVICE_PRINCIPAL,
            role_definition_id=f"/subscriptions/{self.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/{role_id}",
        )
