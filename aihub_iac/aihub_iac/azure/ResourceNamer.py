from aihub_iac.aihub_iac.azure.constants.resources import (
    APP_SERVICE_PLAN,
    V_NET,
    LOG_WORKSPACE,
    SUB_NET,
    POSTGRES,
    APP_SERVICE,
    STORAGE_ACCOUNT,
    COSMOS,
    USER_ASSIGNED_IDENTITY,
    CONTAINER_INSTANCE,
    SEARCH_SERVICE,
    CONTAINER_APP_ENVIRONMENT,
    CONTAINER_APP,
    VM,
    OPEN_AI,
)


class ResourceNamer:

    def __init__(self, project_name=None, location_short_name=None):
        self.project_name = "aihub"
        self.location_short_name = "sui"
        if project_name is not None:
            self.project_name = project_name
        if location_short_name is not None:
            self.location_short_name = location_short_name

    def app_service_plan(self):
        return f"{self.project_name}-{APP_SERVICE_PLAN}-{self.location_short_name}"

    def vnet(self):
        return f"{self.project_name}-{V_NET}-{self.location_short_name}"

    def log_workspace(self, name):
        return f"{self.project_name}-{LOG_WORKSPACE}-{self.location_short_name}-{name}"

    def snet(self):
        return f"{self.project_name}-{SUB_NET}-{self.location_short_name}"

    def snet_nats(self):
        return f"{self.project_name}-{SUB_NET}-{self.location_short_name}-{CONTAINER_INSTANCE}-nats"

    def snet_app(self):
        return f"{self.project_name}-{SUB_NET}-{self.location_short_name}-{APP_SERVICE}"

    def snet_capp(self):
        return f"{self.project_name}-{SUB_NET}-{self.location_short_name}-{CONTAINER_APP}"

    def snet_aci_agents(self):
        return f"{self.project_name}-{SUB_NET}-{self.location_short_name}-{CONTAINER_INSTANCE}-agents"

    def snet_pg(self):
        return f"{self.project_name}-{SUB_NET}-{self.location_short_name}-{POSTGRES}"

    def snet_vm(self):
        return f"{self.project_name}-{SUB_NET}-{self.location_short_name}-vm"

    def snet_priv_endpoint(self):
        return f"{self.project_name}-{SUB_NET}-{self.location_short_name}-priv-endpoint"

    def phoenix_postgres(self):
        return f"{self.project_name}-{POSTGRES}-{self.location_short_name}-phoenix"

    def phoenix_service(self):
        return f"{self.project_name}-{APP_SERVICE}-{self.location_short_name}-phoenix"

    def dagster_postgres(self):
        return f"{self.project_name}-{POSTGRES}-{self.location_short_name}-dagster"

    def openwebui_postgres(self):
        return f"{self.project_name}-{POSTGRES}-{self.location_short_name}-openwebui"

    def dagster_service(self):
        return f"{self.project_name}-{APP_SERVICE}-{self.location_short_name}-dagster"

    def data_lake(self):
        return f"{self.project_name}{STORAGE_ACCOUNT}{self.location_short_name}datalake"

    def api_service(self):
        return f"{self.project_name}-{APP_SERVICE}-{self.location_short_name}-api"

    def bot_service(self):
        return f"{self.project_name}-{APP_SERVICE}-{self.location_short_name}-bot"

    def api_cosmos(self):
        return f"{self.project_name}-{COSMOS}-{self.location_short_name}-api"

    def bot_cosmos(self):
        return f"{self.project_name}-{COSMOS}-{self.location_short_name}-bot"

    def nats_service(self):
        return f"{self.project_name}-{APP_SERVICE}-{self.location_short_name}-nats"

    def redis_service(self):
        return f"{self.project_name}-{APP_SERVICE}-{self.location_short_name}-redis"

    def agent_service(self, agent_name):
        return f"{self.project_name}-{APP_SERVICE}-{self.location_short_name}-{agent_name}"

    def agent_identity(self, agent_name):
        return f"{self.project_name}-{USER_ASSIGNED_IDENTITY}-{self.location_short_name}-{agent_name}"

    def nats_container_group(self):
        return f"{self.project_name}-{CONTAINER_INSTANCE}-{self.location_short_name}-nats"

    def agents_container_group(self, agent_name):
        return f"{self.project_name}-{CONTAINER_INSTANCE}-{self.location_short_name}-{agent_name}"

    def nats_blob(self):
        return f"{self.project_name}{STORAGE_ACCOUNT}{self.location_short_name}nats"

    def ai_search(self):
        return f"{self.project_name}-{SEARCH_SERVICE}-{self.location_short_name}"

    def doc_store(self):
        return f"{self.project_name}-{COSMOS}-{self.location_short_name}-docstore"

    def openwebui_blob(self):
        return f"{self.project_name}{STORAGE_ACCOUNT}{self.location_short_name}openwebui"

    def openwebui_postgres(self):
        return f"{self.project_name}-{POSTGRES}-{self.location_short_name}-openwebui"

    def openwebui_container_group(self):
        return f"{self.project_name}-{CONTAINER_INSTANCE}-{self.location_short_name}-openwebui"

    def openwebui_container_app(self):
        return f"{self.project_name}-{CONTAINER_APP}-{self.location_short_name}-openwebui"

    def openwebui_container_env(self):
        return f"{self.project_name}-{CONTAINER_APP_ENVIRONMENT}-{self.location_short_name}-openwebui"

    def vm(self, name):
        return f"{self.project_name}-{VM}-{self.location_short_name}-{name}"

    def disk(self, name):
        return f"{self.project_name}-disk-{self.location_short_name}-{name}"

    def openai(self):
        return f"{self.project_name}-{OPEN_AI}-{self.location_short_name}"

    def openai_swe(self):
        return f"{self.project_name}-{OPEN_AI}-swe"

    def openai_deployment(self, name):
        return f"{self.project_name}-{OPEN_AI}-{self.location_short_name}-{name}"

    def nat_gateway_public_ip(self):
        return f"{self.project_name}-pub-{self.location_short_name}-natgw"

    def nat_gateway(self, name):
        return f"{self.project_name}-natgw-{self.location_short_name}-{name}"
