from typing import Optional

import pulumi
from pulumi_azure_native import dbforpostgresql, documentdb, network, search

from aihub_iac.azure.constants.resources import AI_SEARCH_SERVICE, COSMOS, POSTGRES, SUB_NET
from aihub_iac.azure.modules.dagster.DagsterConfig import DagsterConfig
from aihub_iac.azure.modules.network.NetworkConfig import NetworkConfig
from aihub_iac.azure.modules.phoenix.PhoenixConfig import PhoenixConfig
from aihub_iac.azure.modules.stores.StoresConfig import StoresConfig
from aihub_iac.azure.modules.webui.WebUIConfig import WebUIConfig
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider
from aihub_iac.azure.providers.PrivateEndpointProvider import PrivateEndpointProvider


class Stores(pulumi.ComponentResource):
    """
    Manages data storage resources including:
    - Vector database (Azure Cognitive Search)
    - Document store (Cosmos DB)
    - API database (Cosmos DB)
    - PostgreSQL server
    """

    def __init__(
        self,
        stack: str,
        name: str,
        config: StoresConfig = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        super().__init__(f"{stack}:{name}", name, None, opts)

        # Create configuration from environment or use provided config
        self.name = name
        self.stack = stack
        self.config = config

        self.network_provider = NetworkProvider(
            self.config.resource_group, self.config.project_name, self.config.location, self.config.location_short
        )

        # Initialize private endpoint manager
        self.pe_manager = PrivateEndpointProvider(
            self.config.resource_group, self.config.location, self.network_provider, self.stack, self
        )

        # Initialize resources
        self.vector_db = None
        self.document_db = None
        self.api_db = None
        self.postgres_db = None

        # Create resources
        self._create_resources()

    @property
    def api_cosmos_subnet_name(self):
        return f"{self.config.project_name}-{SUB_NET}-{self.config.location_short}-{COSMOS}-api"

    @property
    def cosmos_subnet_name(self):
        return f"{self.config.project_name}-{SUB_NET}-{self.config.location_short}-{COSMOS}-store"

    @property
    def search_subnet_name(self):
        return f"{self.config.project_name}-{SUB_NET}-{self.config.location_short}-{AI_SEARCH_SERVICE}-store"

    @property
    def pg_subnet_name(self):
        return f"{self.config.project_name}-{SUB_NET}-{self.config.location_short}-{POSTGRES}"

    def _create_api_cosmos_subnet(self) -> network.Subnet:
        public_access_rules = [
            network.SecurityRuleArgs(
                name="AllowVPN1ToProxy",
                priority=200,
                direction="Inbound",
                access="Allow",
                protocol="Tcp",
                source_address_prefix="192.168.35.145/32",
                source_port_range="*",
                destination_address_prefix="*",
                destination_port_range="*",
            )
        ]
        nsg = self.network_provider.create_subnet_nsg(
            parent=self,
            stack=self.stack,
            subnet_name=self.api_cosmos_subnet_name,
            source_prefixes=[NetworkConfig.APP_SUBNET_CIDR],
            additional_rules=public_access_rules,
        )
        subnet = network.Subnet(
            name=self.api_cosmos_subnet_name,
            resource_name=self.api_cosmos_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=self.config.API_COSMOS_SUBNET_CIDR,
            network_security_group={"id": nsg.id},
        )
        return subnet

    def _create_search_subnet(self) -> network.Subnet:
        nsg = self.network_provider.create_subnet_nsg(
            parent=self,
            stack=self.stack,
            subnet_name=self.search_subnet_name,
            source_prefixes=[NetworkConfig.AGENTS_SUBNET_CIDR, DagsterConfig.DAGSTER_SUBNET_CIDR],
        )
        subnet = network.Subnet(
            name=self.search_subnet_name,
            resource_name=self.search_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=self.config.SEARCH_SUBNET_CIDR,
            network_security_group={"id": nsg.id},
        )
        return subnet

    def _create_pg_subnet(self) -> network.Subnet:
        nsg = self.network_provider.create_subnet_nsg(
            parent=self,
            stack=self.stack,
            subnet_name=self.pg_subnet_name,
            source_prefixes=[
                DagsterConfig.DAGSTER_SUBNET_CIDR,
                PhoenixConfig.PHOENIX_SUBNET_CIDR,
                WebUIConfig.WEBUI_SUBNET_CIDR,
            ],
        )
        subnet = network.Subnet(
            name=self.pg_subnet_name,
            resource_name=self.pg_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=self.config.PG_SUBNET_CIDR,
            delegations=[
                network.DelegationArgs(
                    name="postgres-delegation",
                    service_name="Microsoft.DBforPostgreSQL/flexibleServers",
                )
            ],
            network_security_group={"id": nsg.id},
        )

        return subnet

    def _create_stores_cosmos_subnet(self) -> network.Subnet:
        nsg = self.network_provider.create_subnet_nsg(
            parent=self,
            stack=self.stack,
            subnet_name=self.cosmos_subnet_name,
            source_prefixes=[NetworkConfig.AGENTS_SUBNET_CIDR, DagsterConfig.DAGSTER_SUBNET_CIDR],
        )
        subnet = network.Subnet(
            name=self.cosmos_subnet_name,
            resource_name=self.cosmos_subnet_name,
            resource_group_name=self.config.resource_group,
            virtual_network_name=self.vnet.name,
            address_prefix=self.config.COSMOS_SUBNET_CIDR,
            network_security_group={"id": nsg.id},
        )
        return subnet

    def _create_resources(self):
        """Create all data service resources"""
        # Create search service (vector database)
        self.vnet = self.network_provider.get_vnet()

        self.search_subnet = self._create_search_subnet()
        self.search_dns_zone = self.pe_manager.create_dns_zone("search", "privatelink.search.windows.net")
        self.vector_db = self._create_search_service()

        self.search_private_endpoint = pulumi.Output.all(subnet_id=self.search_subnet.id).apply(
            lambda args: self.pe_manager.create_private_endpoint(
                name=self.config.ai_search_service_name,
                resource_id=self.vector_db.id,
                subnet_id=args["subnet_id"],
                group_id="searchService",
                dns_zone=self.search_dns_zone,
                depends_on=[self.vector_db],
            )
        )

        # Create Cosmos DB resources
        self.cosmos_subnet = self._create_stores_cosmos_subnet()
        self.cosmos_dns_zone = self.pe_manager.create_dns_zone("cosmos", "privatelink.mongo.cosmos.azure.com")

        # Create document store (Cosmos DB)
        self.document_db = self._create_document_db()
        self.document_db_private_endpoint = pulumi.Output.all(subnet_id=self.cosmos_subnet.id).apply(
            lambda args: self.pe_manager.create_private_endpoint(
                name=self.config.doc_store_name,
                resource_id=self.document_db.id,
                subnet_id=args["subnet_id"],
                group_id="MongoDB",
                dns_zone=self.cosmos_dns_zone,
                depends_on=[self.document_db],
            )
        )

        # Create API database (Cosmos DB)
        self.api_cosmos_subnet = self._create_api_cosmos_subnet()
        self.api_db = self._create_api_db()

        self.api_db_private_endpoint = pulumi.Output.all(subnet_id=self.api_cosmos_subnet.id).apply(
            lambda args: self.pe_manager.create_private_endpoint(
                name=self.config.store_name,
                resource_id=self.api_db.id,
                subnet_id=args["subnet_id"],
                group_id="MongoDB",
                dns_zone=self.cosmos_dns_zone,
                depends_on=[self.api_db],
            )
        )

        # Create PostgreSQL resources
        self.postgres_subnet = self._create_pg_subnet()
        self.postgres_dns_zone = self.pe_manager.create_dns_zone(
            "postgres", f"privatelink.{self.config.location.lower()}.postgres.database.azure.com"
        )
        self.postgres_db = self._create_postgres_server()

        # Export outputs
        self._register_outputs()

    def _create_search_service(self) -> search.Service:
        """Create the Azure Cognitive Search service"""
        return search.Service(
            resource_name=self.config.ai_search_service_name,
            search_service_name=self.config.ai_search_service_name,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            sku=search.SkuArgs(name=search.SkuName.STANDARD),
            replica_count=1,
            partition_count=1,
            public_network_access=search.PublicNetworkAccess.DISABLED,
            tags={
                "Stack": self.stack,
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_document_db(self) -> documentdb.DatabaseAccount:
        """Create the document store Cosmos DB account"""
        return documentdb.DatabaseAccount(
            resource_name=self.config.doc_store_name,
            account_name=self.config.doc_store_name,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            kind="MongoDB",
            database_account_offer_type=documentdb.DatabaseAccountOfferType.STANDARD,
            api_properties=documentdb.ApiPropertiesArgs(server_version="4.2"),
            locations=[documentdb.LocationArgs(location_name=self.config.location, failover_priority=0)],
            capabilities=[documentdb.CapabilityArgs(name="EnableServerless")],
            public_network_access=documentdb.PublicNetworkAccess.DISABLED,
            tags={
                "Stack": self.stack,
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_api_db(self) -> documentdb.DatabaseAccount:
        """Create the API Cosmos DB account"""
        return documentdb.DatabaseAccount(
            resource_name=self.config.store_name,
            account_name=self.config.store_name,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            kind="MongoDB",
            database_account_offer_type=documentdb.DatabaseAccountOfferType.STANDARD,
            api_properties=documentdb.ApiPropertiesArgs(server_version="4.2"),
            locations=[documentdb.LocationArgs(location_name=self.config.location, failover_priority=0)],
            capabilities=[documentdb.CapabilityArgs(name="EnableServerless")],
            public_network_access=documentdb.PublicNetworkAccess.DISABLED,
            tags={
                "Stack": self.stack,
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_postgres_server(self) -> dbforpostgresql.Server:
        """Create the PostgreSQL server"""
        server = dbforpostgresql.Server(
            resource_name=self.config.postgres_name,
            server_name=self.config.postgres_name,
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            administrator_login=self.config.postgres_username,
            administrator_login_password=self.config.postgres_password,
            version="16",
            backup=dbforpostgresql.BackupArgs(
                backup_retention_days=7,
                geo_redundant_backup="Disabled",
            ),
            storage=dbforpostgresql.StorageArgs(
                storage_size_gb=64,
            ),
            high_availability=dbforpostgresql.HighAvailabilityArgs(
                mode="Disabled",
            ),
            sku=dbforpostgresql.SkuArgs(
                name="Standard_B2s",
                tier="Burstable",
            ),
            network=dbforpostgresql.NetworkArgs(
                delegated_subnet_resource_id=self.postgres_subnet.id,
                private_dns_zone_arm_resource_id=self.postgres_dns_zone.id,
            ),
            tags={
                "Stack": self.stack,
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Configure vector extension
        self._add_vector_extension(server)

        return server

    def _add_vector_extension(self, server: dbforpostgresql.Server):
        """Add the vector extension to PostgreSQL"""
        dbforpostgresql.Configuration(
            resource_name="azure-extensions",
            configuration_name="azure.extensions",
            resource_group_name=self.config.resource_group,
            server_name=self.config.postgres_name,
            value="vector",  # If you have other extensions, add them with commas
            source="user-override",
            opts=pulumi.ResourceOptions(parent=self, depends_on=[server]),
        )

    def _register_outputs(self):
        """Register outputs for this component"""
        self.register_outputs(
            {
                "vector_db_id": self.vector_db.id,
                "vector_db_name": self.vector_db.name,
                "document_db_id": self.document_db.id,
                "document_db_name": self.document_db.name,
                "document_db_endpoint": self.document_db.document_endpoint,
                "api_db_id": self.api_db.id,
                "api_db_name": self.api_db.name,
                "api_db_endpoint": self.api_db.document_endpoint,
                "postgres_id": self.postgres_db.id,
                "postgres_name": self.postgres_db.name,
            }
        )
