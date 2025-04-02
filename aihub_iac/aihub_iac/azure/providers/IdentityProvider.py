from aihub_iac.azure.resources.UserAssignedIdentity import UserAssignedIdentity


class IdentityProvider:
    def __init__(self, resource_group, location, subscription_id, project_name, location_short):
        self.resource_group = resource_group
        self.location = location
        self.subscription_id = subscription_id
        self.project_name = project_name
        self.location_short = location_short

    def create_identity(self, id_name):
        return UserAssignedIdentity(
            resource_group=self.resource_group,
            location=self.location,
            subscription_id=self.subscription_id,
            project_name=self.project_name,
            location_short_name=self.location_short,
            id_name=id_name,
        )
