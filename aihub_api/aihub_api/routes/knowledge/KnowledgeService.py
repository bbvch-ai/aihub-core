import logging

import mongoengine
from aihub_lib.generative_ai.document.types.IngestedDocument import IngestedDocument
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.azure.cosmos.docstore.CosmosDocstoreAccess import CosmosDocstoreAccess
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity
from aihub_lib.persistence.rag.documents.entities.RefDoc import RefDoc
from aihub_lib.persistence.rag.documents.entities.types.Namespace import Namespace
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from aihub_lib.persistence.rag.vectors import VectorStoreFactory
from aihub_lib.persistence.rag.vectors.node_metadata import (
    DOCUMENT_ID,
    NAMESPACE,
    NODE_TYPE_CONTENT,
    NODE_TYPE_SUMMARY,
    TYPE,
    NodeTypeValue,
)
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from mongoengine import register_connection
from pymongo import MongoClient

from aihub_api.routes.knowledge.dto.CreateNamespaceRequest import CreateNamespaceRequest
from aihub_api.routes.knowledge.dto.DatabaseDTO import DatabaseDTO
from aihub_api.routes.knowledge.dto.NamespaceResponse import NamespaceResponse
from aihub_api.routes.knowledge.dto.NodeSummaryDTO import NodeSummaryDTO
from aihub_api.routes.knowledge.dto.UpdateNamespaceRequest import UpdateNamespaceRequest

logger = logging.getLogger(__name__)


class KnowledgeService:
    @staticmethod
    def _ensure_db_exists(db: str):
        if db not in mongoengine.connection._connections:
            register_connection(alias=db, name=db, host=CosmosDocstoreAccess().get_connection_string())

    @staticmethod
    def get_paginated_documents(
        db: str, namespace: str, page: int = 1, page_size: int = 20
    ) -> tuple[int, list[IngestedDocument]]:
        """
        Retrieves paginated documents for a given namespace.
        """
        skip = (page - 1) * page_size

        KnowledgeService._ensure_db_exists(db)
        total = RefDoc.count_by_namespace(db_alias=db, namespace=namespace)

        ref_docs_page = RefDoc.get_paginated_by_namespace(db_alias=db, namespace=namespace, skip=skip, limit=page_size)

        document_dtos = [IngestedDocument.from_entity(doc) for doc in ref_docs_page]

        return total, document_dtos

    @staticmethod
    def get_document_by_id(db: str, document_id: str) -> IngestedDocument:
        """
        Retrieves a single document by its ID.
        """
        KnowledgeService._ensure_db_exists(db)
        ref_doc = RefDoc.by_id(db_alias=db, doc_id=document_id)
        return IngestedDocument.from_entity(ref_doc)

    @staticmethod
    def get_databases(mongo_client: MongoClient, t: LocaleHandler) -> list[DatabaseDTO]:
        """
        Retrieves all databases (buckets) with their available namespaces with the number of documents in each.
        Gets buckets from BucketEntity and namespaces from NamespaceEntity in MongoDB,
        then enriches with document stats from docstore. Returns format compatible with web frontend.
        """
        database_dtos: list[DatabaseDTO] = []

        # Get all buckets from BucketEntity (stored in main API database)
        buckets = BucketEntity.get_all_buckets()

        for bucket in buckets:
            try:
                db_name = bucket.db_name
                KnowledgeService._ensure_db_exists(db_name)

                # Get namespaces for this bucket from NamespaceEntity (stored in main API database)
                namespace_entities = NamespaceEntity.get_namespaces_by_bucket(str(bucket.id))

                namespaces = []
                for ns_entity in namespace_entities:
                    # Get document stats for this namespace from RefDoc in the docstore
                    document_stats = None
                    try:
                        namespace_data = RefDoc.get_namespaces(db_alias=db_name)
                        # Find matching namespace data by name
                        document_stats = next(
                            (ns_data for ns_data in namespace_data if ns_data["name"] == ns_entity.namespace_name), None
                        )
                    except Exception as e:
                        logger.warning(
                            f"Unable to load document stats for namespace {ns_entity.namespace_name} in database {db_name}: {e}"
                        )

                    # Create Namespace object compatible with frontend expectations
                    if document_stats:
                        namespaces.append(
                            Namespace(
                                database=db_name,
                                name=ns_entity.namespace_name,
                                number_of_documents=document_stats["number_of_documents"],
                                last_updated_at=document_stats["last_updated_at"],
                                last_inserted_at=document_stats["last_inserted_at"],
                                created_at=document_stats["created_at"],
                            )
                        )
                    else:
                        # Create empty namespace if no documents exist yet
                        namespaces.append(
                            Namespace(
                                database=db_name,
                                name=ns_entity.namespace_name,
                                number_of_documents=0,
                                last_updated_at=0,
                                last_inserted_at=0,
                                created_at=0,
                            )
                        )

                # Create DatabaseDTO with format expected by frontend
                database_dtos.append(DatabaseDTO(name=db_name, namespaces=namespaces))

            except Exception as e:
                logger.warning(f"Unable to process bucket {bucket.bucket_name}: {e}")
                continue

        return database_dtos

    @staticmethod
    def get_nodes(
        db: str,
        namespace: str,
        document_id: str,
        vector_store_factory: VectorStoreFactory,
        node_type: NodeTypeValue = NODE_TYPE_CONTENT,
    ) -> list[IngestedNode]:
        filters = MetadataFilters(
            filters=[
                MetadataFilter(key=DOCUMENT_ID, value=document_id),
                MetadataFilter(key=TYPE, value=node_type),
                MetadataFilter(key=NAMESPACE, value=namespace),
            ]
        )
        vector_store = vector_store_factory(db)
        raw_nodes = vector_store.get_nodes(filters=filters)
        nodes = [IngestedNode.from_llama_index_node(node) for node in raw_nodes]
        nodes.sort(key=lambda node: node.index or 1)
        return nodes

    @staticmethod
    def get_summary_nodes(
        db: str, namespace: str, document_id: str, vector_store_factory: VectorStoreFactory
    ) -> list[NodeSummaryDTO]:
        nodes = KnowledgeService.get_nodes(
            db, namespace, document_id, vector_store_factory, node_type=NODE_TYPE_SUMMARY
        )
        summaries: dict[int, NodeSummaryDTO] = {i: NodeSummaryDTO(level=i, nodes=[]) for i in range(0, 7)}
        for node in nodes:
            summaries[node.heading_level].nodes.append(node)
        for level in range(0, 7):
            summaries[level].nodes.sort(key=lambda node: node.index)
        return list(summaries.values())

    @staticmethod
    def create_namespace(request: CreateNamespaceRequest) -> NamespaceResponse:
        """
        Creates a new namespace (folder) in the specified database.
        """
        from fastapi import HTTPException

        # Get the bucket by database name
        try:
            bucket = BucketEntity.get_bucket_by_bucket_name(request.database_name)
        except Exception:
            raise HTTPException(status_code=404, detail=f"Database '{request.database_name}' not found")

        # Check if namespace already exists
        try:
            existing = NamespaceEntity.get_namespace_by_bucket_and_name(str(bucket.id), request.namespace_name)
            if existing:
                raise HTTPException(status_code=409, detail=f"Folder '{request.namespace_name}' already exists in database '{request.database_name}'")
        except Exception:
            # Namespace doesn't exist, which is what we want
            pass

        # Create LocaleStringEntity objects for display name and description
        display_name = None
        if request.display_name:
            display_name = LocaleStringEntity(
                en=request.display_name.en,
                de=request.display_name.de,
                fr=request.display_name.fr,
                it=request.display_name.it,
            )

        description = None
        if request.description:
            description = LocaleStringEntity(
                en=request.description.en,
                de=request.description.de,
                fr=request.description.fr,
                it=request.description.it,
            )

        # Create the namespace entity
        namespace_entity = NamespaceEntity.create_namespace(
            bucket_id=str(bucket.id),
            namespace_name=request.namespace_name,
            folder_name=request.folder_name,
            name=display_name,
            description=description,
        )

        # Convert LocaleStringEntity to DTO format
        display_name_dto = None
        if namespace_entity.name:
            from aihub_api.routes.knowledge.dto.NamespaceResponse import LocaleStrings
            display_name_dto = LocaleStrings(
                en=namespace_entity.name.en,
                de=namespace_entity.name.de,
                fr=namespace_entity.name.fr,
                it=namespace_entity.name.it,
            )

        description_dto = None
        if namespace_entity.description:
            from aihub_api.routes.knowledge.dto.NamespaceResponse import LocaleStrings
            description_dto = LocaleStrings(
                en=namespace_entity.description.en,
                de=namespace_entity.description.de,
                fr=namespace_entity.description.fr,
                it=namespace_entity.description.it,
            )

        return NamespaceResponse(
            id=str(namespace_entity.id),
            bucket_id=namespace_entity.bucket_id,
            namespace_name=namespace_entity.namespace_name,
            folder_name=namespace_entity.folder_name,
            display_name=display_name_dto,
            description=description_dto,
        )

    @staticmethod
    def update_namespace(namespace_id: str, request: UpdateNamespaceRequest) -> NamespaceResponse:
        """
        Updates display name and description for an existing namespace.
        """
        from fastapi import HTTPException

        # Get the existing namespace
        try:
            namespace_entity = NamespaceEntity.get_namespace_by_id(namespace_id)
        except Exception:
            raise HTTPException(status_code=404, detail=f"Folder with ID '{namespace_id}' not found")

        # Create LocaleStringEntity objects for display name and description
        display_name = None
        if request.display_name:
            display_name = LocaleStringEntity(
                en=request.display_name.en,
                de=request.display_name.de,
                fr=request.display_name.fr,
                it=request.display_name.it,
            )

        description = None
        if request.description:
            description = LocaleStringEntity(
                en=request.description.en,
                de=request.description.de,
                fr=request.description.fr,
                it=request.description.it,
            )

        # Update the namespace entity
        updated_entity = NamespaceEntity.update_namespace(
            namespace_id=namespace_id,
            name=display_name,
            description=description,
        )

        # Convert LocaleStringEntity to DTO format
        display_name_dto = None
        if updated_entity.name:
            from aihub_api.routes.knowledge.dto.NamespaceResponse import LocaleStrings
            display_name_dto = LocaleStrings(
                en=updated_entity.name.en,
                de=updated_entity.name.de,
                fr=updated_entity.name.fr,
                it=updated_entity.name.it,
            )

        description_dto = None
        if updated_entity.description:
            from aihub_api.routes.knowledge.dto.NamespaceResponse import LocaleStrings
            description_dto = LocaleStrings(
                en=updated_entity.description.en,
                de=updated_entity.description.de,
                fr=updated_entity.description.fr,
                it=updated_entity.description.it,
            )

        return NamespaceResponse(
            id=str(updated_entity.id),
            bucket_id=updated_entity.bucket_id,
            namespace_name=updated_entity.namespace_name,
            folder_name=updated_entity.folder_name,
            display_name=display_name_dto,
            description=description_dto,
        )
