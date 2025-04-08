from typing import Optional

import pulumi
from pulumi_azure_native import search, documentdb, dbforpostgresql, network

from aihub_iac.azure.modules.stores.StoresConfig import StoresConfig
from aihub_iac.azure.providers.NetworkProvider import NetworkProvider


class Stores(pulumi.ComponentResource):

    def __init__(
        self,
        stack: str,
        name: str,
        config: StoresConfig = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        super().__init__(f"{stack}:{name}", name, None, opts)

        # Create configuration from environment or use provided config
        self.config = config

        self.network_provider = NetworkProvider(
            self.config.resource_group, self.config.project_name, self.config.location_short
        )

        # Initialize resources
        self.vector_db = None
        self.document_db = None
        self.api_db = None

        # Create resources
        self._create_resources()

    def _create_resources(self):
        """Create all data service resources"""
        # Create search service (vector database)
        self.vector_db = self._create_search_service()

        # Create document store (Cosmos DB)
        self.document_db = self._create_document_db()

        # Create API database (Cosmos DB)
        self.api_db = self._create_api_db()

        # Create POSTGRES server

        self.subnet = self.network_provider.get_pg_subnet()
        self.dns_zone = self._create_dns_zone()
        self.zone_link = self._create_zone_link()
        self.postgres_db = self._create_postgres_server()

        # Export outputs
        self._register_outputs()

    def _create_search_service(self) -> search.Service:
        """Create the Azure Cognitive Search service"""
        return search.Service(
            resource_name=self.config.ai_search_service_name(),
            search_service_name=self.config.ai_search_service_name(),
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            sku=search.SkuArgs(name=search.SkuName.STANDARD),
            replica_count=1,
            partition_count=1,
            tags={},
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_document_db(self) -> documentdb.DatabaseAccount:
        """Create the document store Cosmos DB account"""
        return documentdb.DatabaseAccount(
            resource_name=self.config.doc_store_name(),
            account_name=self.config.doc_store_name(),
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            kind="MongoDB",
            database_account_offer_type=documentdb.DatabaseAccountOfferType.STANDARD,
            api_properties=documentdb.ApiPropertiesArgs(server_version="4.2"),
            locations=[documentdb.LocationArgs(location_name=self.config.location, failover_priority=0)],
            capabilities=[documentdb.CapabilityArgs(name="EnableServerless")],
            tags=self.config.document_db_config.tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_api_db(self) -> documentdb.DatabaseAccount:
        """Create the API Cosmos DB account"""
        return documentdb.DatabaseAccount(
            resource_name=self.config.api_store_name(),
            account_name=self.config.api_store_name(),
            resource_group_name=self.config.resource_group,
            location=self.config.location,
            kind="MongoDB",
            database_account_offer_type=self.config.api_db_config.offer_type,
            api_properties=documentdb.ApiPropertiesArgs(server_version="4.2"),
            locations=[documentdb.LocationArgs(location_name=self.config.location, failover_priority=0)],
            capabilities=[documentdb.CapabilityArgs(name="EnableServerless")],
            tags=self.config.document_db_config.tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_postgres_server(self) -> dbforpostgresql.Server:
        return dbforpostgresql.Server(
            resource_name=self.config.postgres_name(),
            server_name=self.config.postgres_name(),
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
                storage_size_gb=32,
            ),
            high_availability=dbforpostgresql.HighAvailabilityArgs(
                mode="Disabled",
            ),
            sku=dbforpostgresql.SkuArgs(
                name="Standard_B1ms",
                tier="Burstable",
            ),
            network=dbforpostgresql.NetworkArgs(
                delegated_subnet_resource_id=self.subnet.id, private_dns_zone_arm_resource_id=self.dns_zone.id
            ),
        )

    def _add_vector_extension(self):
        dbforpostgresql.Configuration(
            configuration_name="vector-extension",
            resource_group_name=self.config.resource_group,
            server_name=self.config.postgres_name(),
            value="vector",
            source="pgvector",
        )

    def _create_dns_zone(self):
        return network.PrivateZone(
            resource_name="postgresDnsZone",
            private_zone_name="aihub.postgres.database.azure.com",
            resource_group_name=self.config.resource_group,
            location="Global",
        )

    def _create_zone_link(self):
        return network.VirtualNetworkLink(
            "vnetLink",
            resource_group_name=self.config.resource_group,
            private_zone_name=self.dns_zone.name,
            registration_enabled=False,
            virtual_network=network.SubResourceArgs(
                id=self.network_provider.get_vnet().id,
            ),
            location="Global",
        )

    def _register_outputs(self):
        """Register outputs for this component"""
        self.register_outputs(
            {
                "vector_db_id": self.vector_db.id,
                "vector_db_name": self.vector_db.name,
                "vector_db_endpoint": self.vector_db.host_name.apply(lambda host_name: f"https://{host_name}"),
                "document_db_id": self.document_db.id,
                "document_db_name": self.document_db.name,
                "document_db_endpoint": self.document_db.document_endpoint,
                "api_db_id": self.api_db.id,
                "api_db_name": self.api_db.name,
                "api_db_endpoint": self.api_db.document_endpoint,
            }
        )
