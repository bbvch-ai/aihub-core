import logging

import mongoengine
from aihub_lib.generative_ai.document.types.IngestedDocument import IngestedDocument
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.rag.documents.entities.RefDoc import RefDoc
from aihub_lib.persistence.rag.documents.entities.types.Namespace import Namespace
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
from pymongo import AsyncMongoClient

from aihub_api.routes.knowledge.dto.DatabaseDTO import DatabaseDTO
from aihub_api.routes.knowledge.dto.NodeSummaryDTO import NodeSummaryDTO

logger = logging.getLogger(__name__)


class KnowledgeService:
    @staticmethod
    def _ensure_db_exists(db: str):
        if db not in mongoengine.connection._connections:
            register_connection(alias=db, name=db, host=MongoSettings().CONNECTION_STRING.get_secret_value())

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
    async def get_databases(mongo_client: AsyncMongoClient) -> list[DatabaseDTO]:
        """
        Retrieves all databases with their available namespaces with the number of documents in each.
        Uses a MongoDB aggregation pipeline to get this information in a single query.
        """
        database_names = await mongo_client.list_database_names()
        user_dbs = [db_name for db_name in database_names if db_name not in ["admin", "local", "config"]]

        database_dtos: list[DatabaseDTO] = []
        for db_name in user_dbs:
            KnowledgeService._ensure_db_exists(db_name)
            namespace_data = RefDoc.get_namespaces(db_alias=db_name)
            try:
                namespaces = [Namespace(database=db_name, **ns_data) for ns_data in namespace_data]
            except Exception:
                logger.warning(f"Unable to load documents from database {db_name}, skipping")
                continue

            if len(namespaces) > 0:
                database_dtos.append(DatabaseDTO(name=db_name, namespaces=namespaces))

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
