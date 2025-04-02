import os


class EnvVariableProvider:

    @staticmethod
    def get_environment_variables():
        project_name = os.getenv("APP_NAME", "aihub")
        location = os.getenv("LOCATION", "SwitzerlandNorth")
        location_short = os.getenv("LOCATION_SHORT", "sui")
        resource_group = os.getenv("RESOURCE_GROUP", "default_location")
        subscription_id = os.getenv("ARM_SUBSCRIPTION_ID", "default_location")
        return project_name, location, location_short, resource_group, subscription_id
