from pulumi_azure_native import web


class WebAppCreator:
    def __init__(self, service_name, resource_group, location, app_service_plan_name):
        self.resource_group = resource_group
        self.location = location
        self.service_name = service_name
        self.app_service_plan = web.get_app_service_plan_output(
            resource_group_name=self.resource_group, name=app_service_plan_name
        )

    def create_webapp(self, docker_image, app_settings, identity, subnet_id):
        return web.WebApp(
            resource_name=self.service_name,
            name=self.service_name,
            resource_group_name=self.resource_group,
            location=self.location,
            kind="app,linux,container",
            site_config=web.SiteConfigArgs(
                linux_fx_version=docker_image,
                acr_use_managed_identity_creds=True,
                app_settings=app_settings,
            ),
            identity=identity,
            virtual_network_subnet_id=subnet_id,
            vnet_route_all_enabled=True,
            server_farm_id=self.app_service_plan.id,
        )
