import logging

import mongoengine
from fastapi import HTTPException

from aihub_api.routes.knowledge.dto.NamespaceDTO import NamespaceDTO
from aihub_api.services.TranslationService import TranslationService
from aihub_lib.generative_ai.document.types.IngestedDocument import IngestedDocument
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.azure.cosmos.docstore.CosmosDocstoreAccess import CosmosDocstoreAccess
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity
from aihub_lib.persistence.rag.documents.entities.RefDoc import RefDoc
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.documents.entities.NamespaceEntity import NamespaceEntity
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
from mongoengine import register_connection, DoesNotExist

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
    def get_databases(t: LocaleHandler) -> list[DatabaseDTO]:
        """
        Retrieves all databases (buckets) with their available namespaces with the number of documents in each.
        Gets buckets from BucketEntity and namespaces from NamespaceEntity in MongoDB,
        then enriches with document stats from docstore. Returns format compatible with web frontend.
        """
        database_dtos: list[DatabaseDTO] = []
        buckets = BucketEntity.get_all_buckets()

        for bucket in buckets:
            db_name = bucket.db_name
            KnowledgeService._ensure_db_exists(db_name)

            namespace_entities = NamespaceEntity.get_namespaces_by_bucket(str(bucket.id))

            namespaces = []
            for ns_entity in namespace_entities:
                document_count = RefDoc.count_by_namespace(db_alias=db_name, namespace=ns_entity.namespace_name)
                namespaces.append(NamespaceDTO.from_entity(entity=ns_entity, t=t, number_of_documents=document_count))

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

    async def _create_and_translate_locale_entity(
        text: str | None, t: LocaleHandler, llm_config: ChatLLMConfig | None
    ) -> LocaleStringEntity | None:
        """Helper to create and translate a LocaleStringEntity."""
        if not text:
            return None

        # Create the initial entity from the user's input and locale
        locale_string = LocaleString(**{t.locale: text})
        entity = LocaleStringEntity.from_locale_string(locale_string)

        # If an LLM is configured, attempt to translate to other locales
        if llm_config:
            try:
                # This returns the updated entity with translations
                entity = await TranslationService.translate_locale_string_entity(
                    entity=entity, llm_config=llm_config, t=t, source_locale=t.locale
                )
                logger.info(f"Successfully translated text snippet '{text[:30]}...'.")
            except Exception as e:
                logger.warning(f"Failed to auto-translate text snippet '{text[:30]}...': {e}")

        return entity

    @staticmethod
    async def create_namespace(
        request: CreateNamespaceRequest, t: LocaleHandler, llm_config: ChatLLMConfig | None = None
    ) -> NamespaceResponse:
        """
        Creates a new namespace (folder) in the specified database.
        """
        # 1. --- Validate Bucket ---
        try:
            bucket = BucketEntity.get_bucket_by_bucket_name(request.database_name)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Database '{request.database_name}' not found.")

        # 2. --- Prevent Duplicates (with specific error handling) ---
        try:
            NamespaceEntity.get_namespace_by_bucket_and_name(str(bucket.id), request.namespace_name)
            # If the above line doesn't raise an exception, the namespace already exists.
            raise HTTPException(
                status_code=409,
                detail=f"Folder '{request.namespace_name}' already exists in database '{request.database_name}'.",
            )
        except DoesNotExist:
            # This is the expected path for a new namespace, so we can proceed.
            pass

        # 3. --- Prepare Localized Data (using the helper method) ---
        display_name_entity = await KnowledgeService._create_and_translate_locale_entity(
            request.display_name, t, llm_config
        )
        description_entity = await KnowledgeService._create_and_translate_locale_entity(
            request.description, t, llm_config
        )

        # 4. --- Create the Namespace in the Database ---
        namespace_entity = NamespaceEntity.create_namespace(
            bucket_id=str(bucket.id),
            namespace_name=request.namespace_name,
            folder_name=request.folder_name,
            display_name=display_name_entity,
            description=description_entity,
        )

        # 5. --- Format and Return the Response ---
        return NamespaceResponse(
            id=str(namespace_entity.id),
            bucket_id=namespace_entity.bucket_id,
            namespace_name=namespace_entity.namespace_name,
            folder_name=namespace_entity.folder_name,
            display_name=t.extract(namespace_entity.display_name),
            description=t.extract(namespace_entity.description),
        )

    @staticmethod
    async def update_namespace(
        namespace_id: str, request: UpdateNamespaceRequest, t: LocaleHandler, llm_config: ChatLLMConfig | None = None
    ) -> NamespaceResponse:
        """
        Updates display name and description for an existing namespace.
        """
        from fastapi import HTTPException

        try:
            NamespaceEntity.get_namespace_by_id(namespace_id)
        except Exception:
            raise HTTPException(status_code=404, detail=f"Folder with ID '{namespace_id}' not found")

        display_name = None
        if request.display_name:
            # Create basic LocaleString with user's language
            locale_kwargs = {t.locale: request.display_name}
            locale_string = LocaleString(**locale_kwargs)
            display_name = LocaleStringEntity.from_locale_string(locale_string)

            # Auto-translate to missing locales if LLM config is provided
            if llm_config:
                try:
                    display_name = await TranslationService.translate_locale_string_entity(
                        entity=display_name, llm_config=llm_config, t=t, source_locale=t.locale
                    )
                    logger.info(f"Successfully translated display_name to all supported locales")
                except Exception as e:
                    logger.warning(f"Failed to translate display_name: {e}")

        description = None
        if request.description:
            # Create basic LocaleString with user's language
            locale_kwargs = {t.locale: request.description}
            locale_string = LocaleString(**locale_kwargs)
            description = LocaleStringEntity.from_locale_string(locale_string)

            # Auto-translate to missing locales if LLM config is provided
            if llm_config:
                try:
                    description = await TranslationService.translate_locale_string_entity(
                        entity=description, llm_config=llm_config, t=t, source_locale=t.locale
                    )
                    logger.info(f"Successfully translated description to all supported locales")
                except Exception as e:
                    logger.warning(f"Failed to translate description: {e}")

        updated_entity = NamespaceEntity.update_namespace(
            namespace_id=namespace_id,
            display_name=display_name,
            description=description,
        )

        return NamespaceResponse(
            id=str(updated_entity.id),
            bucket_id=updated_entity.bucket_id,
            namespace_name=updated_entity.namespace_name,
            folder_name=updated_entity.folder_name,
            display_name=t.extract(updated_entity.display_name) if updated_entity.display_name else None,
            description=t.extract(updated_entity.description) if updated_entity.description else None,
        )
