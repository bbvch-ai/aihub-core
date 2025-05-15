from typing import List, Tuple

from aihub_api.routes.knowledge.dto.DocumentDTO import DocumentDTO
from aihub_lib.persistence.rag.documents.entities.RefDoc import RefDoc
from aihub_lib.persistence.rag.documents.entities.types.Namespace import Namespace


class KnowledgeService:

    @staticmethod
    def get_paginated_documents(namespace: str, page: int = 1, page_size: int = 20) -> Tuple[int, List[DocumentDTO]]:
        """
        Retrieves paginated documents for a given namespace.
        """
        skip = (page - 1) * page_size
        total = RefDoc.count_by_namespace(namespace=namespace)

        ref_docs_page = RefDoc.get_paginated_by_namespace(
            namespace=namespace,
            skip=skip,
            limit=page_size
        )

        document_dtos = [DocumentDTO.from_entity(doc) for doc in ref_docs_page]

        return total, document_dtos

    @staticmethod
    def get_document_by_id(document_id: str) -> DocumentDTO:
        """
        Retrieves a single document by its ID.
        """
        ref_doc = RefDoc.by_id(doc_id=document_id)
        return DocumentDTO.from_entity(ref_doc)

    @staticmethod
    def get_all_namespaces() -> List[Namespace]:
        """
        Retrieves all available namespaces with the number of documents in each.
        Uses a MongoDB aggregation pipeline to get this information in a single query.
        """
        namespace_data = RefDoc.get_namespaces_with_counts()

        # Convert the dictionaries to Namespace objects
        namespace_objects = [Namespace(**ns_data) for ns_data in namespace_data]

        return namespace_objects
