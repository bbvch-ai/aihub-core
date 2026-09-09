import logging
import re
import uuid
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import HTTPException
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from mongoengine import DoesNotExist, NotUniqueError, ValidationError
from nats.aio.client import Client as NATS
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.form import FormkitElement, Group, ModelSelect, Repeater
from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)
from swiss_ai_hub.core.generative_ai.document.types.file_type_config import FileTypeConfig
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoConnectionRegistry, trace_fn
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities import (
    BucketEntity,
    IngestorEntity,
    IngestorType,
    NamespaceEntity,
)
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc
from swiss_ai_hub.core.persistence.rag.vectors import VectorStoreFactory
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    DOCUMENT_ID,
    NAMESPACE,
    NODE_TYPE_CONTENT,
    NODE_TYPE_SUMMARY,
    TYPE,
    NodeTypeValue,
)
from swiss_ai_hub.core.publishers import SourceUpdatedPublisher

from swiss_ai_hub.api.routes.knowledge.dto.batch_delete_documents_response import (
    BatchDeleteDocumentsResponse,
    DocumentDeletionResult,
)
from swiss_ai_hub.api.routes.knowledge.dto.create_database_request import CreateDatabaseRequest
from swiss_ai_hub.api.routes.knowledge.dto.create_namespace_request import CreateNamespaceRequest
from swiss_ai_hub.api.routes.knowledge.dto.database_dto import DatabaseDTO
from swiss_ai_hub.api.routes.knowledge.dto.database_response import DatabaseResponse
from swiss_ai_hub.api.routes.knowledge.dto.document_dto import DocumentDTO
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_request import DocumentUploadRequest
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_response import DocumentUploadResponse
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_validation_request import DocumentUploadValidationRequest
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_validation_response import DocumentUploadValidationResponse
from swiss_ai_hub.api.routes.knowledge.dto.ingestor_dto import IngestorDTO
from swiss_ai_hub.api.routes.knowledge.dto.namespace_dto import NamespaceDTO
from swiss_ai_hub.api.routes.knowledge.dto.namespace_response import NamespaceResponse
from swiss_ai_hub.api.routes.knowledge.dto.node_summary_dto import NodeSummaryDTO
from swiss_ai_hub.api.routes.knowledge.dto.update_namespace_request import UpdateNamespaceRequest
from swiss_ai_hub.api.routes.model.model_service import ModelService
from swiss_ai_hub.api.routes.translation.translation_service import TranslationService
from swiss_ai_hub.api.services.model_creation_service import ModelCreationService
from swiss_ai_hub.api.util.config_authorization_service import ConfigAuthorizationService
from swiss_ai_hub.api.util.instance_config_helper import InstanceConfigHelper

logger = logging.getLogger(__name__)

_S3_URI_SCHEME = "s3://"

_SYSTEM_DATABASE_NAMES = frozenset({"admin", "local", "config"})


class KnowledgeService:
    @staticmethod
    def _ensure_db_exists(db: str):
        MongoConnectionRegistry.ensure_alias(db)

    @staticmethod
    @trace_fn
    def get_paginated_documents(
        db: str,
        namespace: str,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        sort_field: str | None = None,
        sort_order: int = 1,
    ) -> tuple[int, list[DocumentDTO]]:
        """Retrieves paginated documents for a namespace.

        Default sort is by updated_at (newest first).
        Use sort_field=is_ingested to see pending documents first.
        """
        skip = (page - 1) * page_size
        KnowledgeService._ensure_db_exists(db)

        if search:
            total = RefDoc.count_search_in_namespace(db_alias=db, namespace=namespace, query=search)
            if skip >= total:
                return total, []
            ref_docs = RefDoc.search_in_namespace(
                db_alias=db,
                namespace=namespace,
                query=search,
                skip=skip,
                limit=page_size,
                sort_field=sort_field,
                sort_order=sort_order,
            )
        else:
            total = RefDoc.count_by_namespace(db_alias=db, namespace=namespace)
            if skip >= total:
                return total, []
            ref_docs = RefDoc.get_all_in_namespace(
                db_alias=db,
                namespace=namespace,
                skip=skip,
                limit=page_size,
                sort_field=sort_field,
                sort_order=sort_order,
            )

        return total, [DocumentDTO.from_ref_doc(doc) for doc in ref_docs]

    @staticmethod
    @trace_fn
    def get_document_by_id(db: str, document_id: str) -> DocumentDTO:
        """Retrieves a single document by its ID from the knowledge database."""
        KnowledgeService._ensure_db_exists(db)
        ref_doc = RefDoc.by_id(db_alias=db, doc_id=document_id)
        return DocumentDTO.from_ref_doc(ref_doc)

    @staticmethod
    @trace_fn
    def get_databases(t: LocaleHandler) -> list[DatabaseDTO]:
        """
        Retrieves all databases (buckets) with their available namespaces with the number of documents in each.

        Gets buckets from BucketEntity and namespaces from NamespaceEntity in MongoDB,
        then enriches with document counts from RefDoc (both pending and ingested).
        """
        database_dtos: list[DatabaseDTO] = []
        buckets = BucketEntity.get_all_buckets()
        show_legacy = AIHubSettings().SHOW_LEGACY_KNOWLEDGE

        for bucket in buckets:
            # A bucket flagged for teardown is being purged by the pipeline; hide it so it disappears
            # from the UI immediately and cannot be re-selected while the teardown job runs.
            if bucket.deleting:
                continue

            # The legacy default_rag / shared_rag databases are obsolete once their deploy-bound pipelines
            # are switched off, so they are hidden unless a deployment opts back in via SHOW_LEGACY_KNOWLEDGE.
            if not show_legacy and KnowledgeService._is_legacy_bucket(bucket):
                continue

            db_name = bucket.db_name
            KnowledgeService._ensure_db_exists(db_name)

            namespace_entities = NamespaceEntity.get_namespaces_by_bucket(str(bucket.id))

            namespaces = []
            for ns_entity in namespace_entities:
                if ns_entity.deleting:
                    continue
                total_count = RefDoc.count_by_namespace(db_alias=db_name, namespace=ns_entity.namespace_name)
                namespaces.append(NamespaceDTO.from_entity(entity=ns_entity, t=t, number_of_documents=total_count))

            display_name = KnowledgeService._safe_extract_locale_string(bucket.name, t)
            database_dtos.append(
                DatabaseDTO(
                    name=db_name,
                    display_name=display_name,
                    auto_sync=bucket.auto_sync,
                    deletable=KnowledgeService._is_database_deletable(bucket),
                    ingestor=bucket.ingestor,
                    namespaces=namespaces,
                )
            )

        return database_dtos

    @staticmethod
    @trace_fn
    def get_nodes(
        db: str,
        namespace: str,
        document_id: str,
        vector_store_factory: VectorStoreFactory,
        t: LocaleHandler,
        node_type: NodeTypeValue = NODE_TYPE_CONTENT,
    ) -> list[IngestedNode]:
        """Retrieves nodes for a document from the vector store."""
        filters = MetadataFilters(
            filters=[
                MetadataFilter(key=DOCUMENT_ID, value=document_id),
                MetadataFilter(key=TYPE, value=node_type),
                MetadataFilter(key=NAMESPACE, value=namespace),
            ]
        )
        vector_store = vector_store_factory(db)
        raw_nodes = vector_store.get_nodes(filters=filters, namespaces=[namespace])
        nodes = [IngestedNode.from_llama_index_node(node) for node in raw_nodes]
        nodes.sort(key=lambda node: node.index or 1)
        return nodes

    @staticmethod
    @trace_fn
    def get_summary_nodes(
        db: str, namespace: str, document_id: str, vector_store_factory: VectorStoreFactory, t: LocaleHandler
    ) -> list[NodeSummaryDTO]:
        nodes = KnowledgeService.get_nodes(
            db, namespace, document_id, vector_store_factory, t=t, node_type=NODE_TYPE_SUMMARY
        )
        summaries: dict[int, NodeSummaryDTO] = {i: NodeSummaryDTO(level=i, nodes=[]) for i in range(0, 7)}
        for node in nodes:
            summaries[node.heading_level].nodes.append(node)
        for level in range(0, 7):
            summaries[level].nodes.sort(key=lambda node: node.index)
        return list(summaries.values())

    @staticmethod
    def _safe_extract_locale_string(entity: LocaleStringEntity | None, t: LocaleHandler) -> str | None:
        if not entity:
            return None

        try:
            result = t.extract(entity.to_locale_string())
            return result if result and result.strip() else None
        except (ValueError, AttributeError):
            return None

    @staticmethod
    async def _create_and_translate_locale_entity(
        text: str | None, t: LocaleHandler, llm_config: LLMConfig, user: UserIdentity
    ) -> LocaleStringEntity | None:
        """Helper to create and translate a LocaleStringEntity."""
        if not text or text.strip() == "":
            return None

        locale_string = LocaleString(**{t.locale: text})

        translated_locale_string = await TranslationService.translate(
            locale_string=locale_string, llm_config=llm_config, t=t, user=user, source_locale=t.locale
        )
        return LocaleStringEntity.from_locale_string(translated_locale_string)

    @staticmethod
    def _knowledge_admin_role_name(database: str, namespace: str | None = None) -> str:
        """Per-resource admin role name, e.g. ``KnowledgeResearchDocsReportsAdmin``.

        The ``Knowledge`` prefix keeps these from colliding with the per-agent-instance roles, which are
        named from the agent id alone.
        """
        segments = [database, namespace] if namespace else [database]
        pascal_case = "".join(
            word[:1].upper() + word[1:] for segment in segments for word in re.split(r"[^0-9A-Za-z]+", segment) if word
        )
        return f"Knowledge{pascal_case}Admin"

    @staticmethod
    def _grant_knowledge_access(
        admin_rule: Annotated[str, "Concrete admin permission for the resource just created"],
        role_name: Annotated[str, "Per-resource admin role to bind the creator to"],
        role_description: Annotated[str, "Human-readable description stored on the role"],
        user: UserIdentity,
        rollback: Annotated[Callable[[], Any], "Undoes the resource creation if the grant fails"],
        resource_label: Annotated[str, "Resource named in the error message"],
    ) -> None:
        """Grants the creating tenant and creator admin on the new resource, rolling back on failure.

        Without this, creating a knowledge database left it usable only by a holder of the global
        ``aihub.admin.knowledge.>`` wildcard — the creator could not see what they had just made.
        """
        tenant = user.acting_within_tenant
        granted_tenant_rule = False
        created_role = False
        try:
            if not AccessChecker.rules_grant_admin(tenant.access_rules, admin_rule):
                TenantMetadataEntity.grant_access_rule(tenant.id, admin_rule)
                granted_tenant_rule = True
            created_role = KnowledgeService._ensure_admin_role(role_name, admin_rule, tenant.id, role_description)
            UserTenantRoleEntity.add_roles(user.id, tenant.id, [role_name])
        except Exception as error:
            if created_role:
                KnowledgeService._best_effort(
                    lambda: RoleEntity.delete_role_from_all_tenants(role_name), f"delete role {role_name}"
                )
            if granted_tenant_rule:
                KnowledgeService._best_effort(
                    lambda: TenantMetadataEntity.revoke_access_rule_from_all_tenants([admin_rule]),
                    f"revoke {admin_rule}",
                )
            KnowledgeService._best_effort(rollback, f"roll back {resource_label}")
            raise HTTPException(
                status_code=500,
                detail=(f"{resource_label} was created but access could not be granted; the creation was rolled back."),
            ) from error

    @staticmethod
    def _ensure_admin_role(role_name: str, admin_rule: str, tenant_id: str, description: str) -> bool:
        """Creates the per-resource admin role if absent. Returns whether it was created."""
        if RoleEntity.objects(name=role_name, tenant_id=tenant_id).first():
            return False
        RoleEntity.create_tenant_role(
            name=role_name, description=description, access_rules=[admin_rule], tenant_id=tenant_id
        )
        return True

    @staticmethod
    def _revoke_knowledge_access(
        rules: Annotated[list[str], "User and admin rules to revoke from every tenant"],
        role_names: Annotated[list[str], "Per-resource admin roles to delete"],
    ) -> None:
        """Removes the grants a create made, so a deleted resource leaves no inert rules behind.

        Best-effort throughout: teardown is already under way by the time this runs, and a stale rule
        must not block it.
        """
        KnowledgeService._best_effort(
            lambda: TenantMetadataEntity.revoke_access_rule_from_all_tenants(rules), f"revoke {rules}"
        )
        for role_name in role_names:
            KnowledgeService._best_effort(
                lambda name=role_name: RoleEntity.delete_role_from_all_tenants(name), f"delete role {role_name}"
            )

    @staticmethod
    def _best_effort(action: Callable[[], Any], description: str) -> None:
        """Runs a compensating action, swallowing and logging any failure so it cannot mask the outcome."""
        try:
            action()
        except Exception:
            logger.exception("Best-effort step failed: %s", description)

    @staticmethod
    async def _validated_model(
        field_path: Annotated[str, "Where on the form the model was chosen, named in any rejection"],
        model_name: str,
        expected_mode: Annotated[str, "LiteLLM mode the picker requires, e.g. 'chat' or 'embedding'"],
        user: UserIdentity,
    ) -> None:
        """Rejects a model this deployment does not serve, the caller cannot use, or that cannot do the job.

        Goes through ``ModelService`` rather than LiteLLM directly so the tenant's own model access rules
        apply: a database must not be bound to a model its creator is not allowed to use.
        """
        model = await ModelService.get_model_by_name(user, model_name)
        if model.model_info.mode != expected_mode:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Configuration validation failed: {field_path}: '{model_name}' is a "
                    f"'{model.model_info.mode}' model and cannot be used where a '{expected_mode}' model is required."
                ),
            )
        if expected_mode == "embedding" and model.model_info.output_vector_size is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Configuration validation failed: {field_path}: embedding model '{model_name}' declares no "
                    "output_vector_size, so the vector collection's dimension cannot be derived from it. "
                    "Add it to the LiteLLM model config."
                ),
            )

    @staticmethod
    async def _validate_model_selections(
        elements: list[FormkitElement], config: dict[str, Any], user: UserIdentity, prefix: str = ""
    ) -> None:
        """Every ``ModelSelect`` the ingestor announced is checked against LiteLLM, wherever it sits on the form.

        The API knows nothing about a pipeline's field names; it knows which elements are model pickers and what
        mode each requires, which is all the check needs.
        """
        for element in elements:
            name = getattr(element, "name", None)
            if name:
                await KnowledgeService._validate_element(element, f"{prefix}{name}", config.get(name), user)

    @staticmethod
    async def _validate_element(element: FormkitElement, field_path: str, value: Any, user: UserIdentity) -> None:
        """One element of an announced form: a container to walk into, a model picker to check, or nothing."""
        if isinstance(element, Group) and isinstance(value, dict):
            await KnowledgeService._validate_model_selections(element.children, value, user, f"{field_path}.")
        elif isinstance(element, Repeater) and isinstance(value, list):
            await KnowledgeService._validate_repeated_entries(element, field_path, value, user)
        elif isinstance(element, ModelSelect) and value is not None:
            await KnowledgeService._validated_model(field_path, value, element.mode, user)

    @staticmethod
    async def _validate_repeated_entries(
        element: Repeater, field_path: str, entries: list[Any], user: UserIdentity
    ) -> None:
        for index, entry in enumerate(entries):
            if isinstance(entry, dict):
                await KnowledgeService._validate_model_selections(
                    element.children, entry, user, f"{field_path}.{index}."
                )

    @staticmethod
    @trace_fn
    def get_ingestors(t: LocaleHandler) -> list[IngestorDTO]:
        """The ingestion pipelines a user may pick when creating a knowledge database, with their forms.

        Every deployed pipeline — the platform's own included — registers itself from its own container, so what
        is offered is exactly what is running, localized from the labels and form it announced.
        """
        return [IngestorDTO.from_ingestor(ingestor, t) for ingestor in IngestorEntity.all()]

    @staticmethod
    async def create_database(
        database: str,
        request: CreateDatabaseRequest,
        t: LocaleHandler,
        s3_service: S3AnonymousFileAccessService,
        user: UserIdentity,
    ) -> DatabaseResponse:
        """
        Creates a new self-service knowledge database (bucket).

        The database name doubles as the S3 bucket, Mongo store, and Milvus collection name. The bucket
        records the ingestor that owns it, so the matching deployed pipeline picks it up without any
        redeployment, and the configuration that ingestor's announced form produced — validated here against
        the schema it announced, the way an agent instance is validated against its class.

        The S3 bucket is provisioned (with browser-upload CORS) up front so documents can be uploaded
        immediately, before the pipeline's first lazy ingest.
        """
        # First, so a rejected name costs neither a translation call nor a storage probe.
        try:
            BucketEntity.validate_new_database_name(database)
        except ValidationError as invalid_name:
            raise HTTPException(status_code=400, detail=str(invalid_name)) from None

        ingestor = IngestorEntity.find(request.ingestor)
        if ingestor is None or ingestor.config_specs is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Ingestor '{request.ingestor}' cannot be assigned to a self-service database: no running "
                    "pipeline has announced it with a configuration form."
                ),
            )

        try:
            BucketEntity.get_bucket_by_bucket_name(database)
            raise HTTPException(status_code=409, detail=f"Database '{database}' already exists.")
        except DoesNotExist:
            pass

        if s3_service.container_exists(database):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Storage container '{database}' already exists but is not a knowledge database. "
                    "Choose a different name."
                ),
            )

        config = InstanceConfigHelper.normalize_form_configuration(request.configuration)
        config_model = ModelCreationService.create_config_model(ingestor.config_specs.to_specs())
        config_instance = InstanceConfigHelper.validate_config_for_create(config, config_model)
        await ConfigAuthorizationService.validate_for_user_or_raise(
            form_elements=ingestor.form, config=config, user=user, t=t
        )
        await KnowledgeService._validate_model_selections(ingestor.form_elements, config, user)

        metadata = InstanceConfigHelper.extract_config_metadata(config_instance, fallback_icon="")
        locale = InstanceConfigHelper.build_locale_entities(metadata.name, metadata.description, database, "")
        configuration = {
            key: value for key, value in config.items() if key not in InstanceConfigHelper.IDENTITY_LOCALE_FIELDS
        }

        # Persist the entity before provisioning storage: the unique bucket_name index serialises
        # concurrent admin calls (the loser gets NotUniqueError, not a second bucket), so any failure
        # before this point leaves no orphan. If provisioning fails, roll back both the container and
        # the row so a retry starts clean.
        try:
            bucket = BucketEntity.create_bucket(
                bucket_name=database,
                db_name=database,
                name=locale.name,
                description=locale.description,
                ingestor=request.ingestor,
                configuration=configuration,
            )
        except NotUniqueError:
            raise HTTPException(status_code=409, detail=f"Database '{database}' already exists.") from None

        def undo_provisioning() -> None:
            s3_service.delete_container(database)
            BucketEntity.delete_bucket(str(bucket.id))

        try:
            s3_service.ensure_bucket_with_cors(database)
        except Exception:
            undo_provisioning()
            raise

        if user.acting_within_tenant is not None:
            KnowledgeService._grant_knowledge_access(
                admin_rule=AccessChecker.knowledge_database_admin_rule(database),
                role_name=KnowledgeService._knowledge_admin_role_name(database),
                role_description=f"Admin access to knowledge database {database}",
                user=user,
                rollback=undo_provisioning,
                resource_label=f"Knowledge database '{database}'",
            )

        return DatabaseResponse(
            name=bucket.db_name,
            bucket_name=bucket.bucket_name,
            ingestor=bucket.ingestor,
            configuration=bucket.configuration,
            display_name=KnowledgeService._safe_extract_locale_string(bucket.name, t),
            description=KnowledgeService._safe_extract_locale_string(bucket.description, t),
        )

    @staticmethod
    async def create_namespace(
        database: str,
        namespace: str,
        request: CreateNamespaceRequest,
        t: LocaleHandler,
        user: UserIdentity,
        llm_config: LLMConfig | None = None,
    ) -> NamespaceResponse:
        """
        Creates a new namespace (folder) in the specified database.
        """
        bucket = BucketEntity.get_bucket_by_db_name(database)

        try:
            NamespaceEntity.get_namespace_by_bucket_and_name(str(bucket.id), namespace)
            raise HTTPException(
                status_code=409,
                detail=f"Folder '{namespace}' already exists in database '{database}'.",
            )
        except DoesNotExist:
            pass

        display_name_entity = await KnowledgeService._create_and_translate_locale_entity(
            text=request.display_name, t=t, llm_config=llm_config, user=user
        )
        description_entity = await KnowledgeService._create_and_translate_locale_entity(
            request.description, t, llm_config, user
        )

        namespace_entity = NamespaceEntity.create_namespace(
            bucket_id=str(bucket.id),
            namespace_name=namespace,
            folder_name=request.folder_name,
            display_name=display_name_entity,
            description=description_entity,
        )

        if user.acting_within_tenant is not None:
            KnowledgeService._grant_knowledge_access(
                admin_rule=AccessChecker.knowledge_namespace_admin_rule(database, namespace),
                role_name=KnowledgeService._knowledge_admin_role_name(database, namespace),
                role_description=f"Admin access to knowledge folder {database}/{namespace}",
                user=user,
                rollback=lambda: NamespaceEntity.delete_namespace(str(namespace_entity.id)),
                resource_label=f"Knowledge folder '{database}/{namespace}'",
            )

        return NamespaceResponse(
            id=str(namespace_entity.id),
            bucket_id=namespace_entity.bucket_id,
            namespace_name=namespace_entity.namespace_name,
            folder_name=namespace_entity.folder_name,
            display_name=KnowledgeService._safe_extract_locale_string(namespace_entity.display_name, t),
            description=KnowledgeService._safe_extract_locale_string(namespace_entity.description, t),
        )

    @staticmethod
    async def update_namespace(
        namespace_id: str,
        request: UpdateNamespaceRequest,
        t: LocaleHandler,
        user: UserIdentity,
        llm_config: LLMConfig | None = None,
    ) -> NamespaceResponse:
        """
        Updates display name and description for an existing namespace.
        """
        try:
            NamespaceEntity.get_namespace_by_id(namespace_id)
        except Exception:
            raise HTTPException(status_code=404, detail=f"Folder with ID '{namespace_id}' not found")

        display_name_entity = await KnowledgeService._create_and_translate_locale_entity(
            text=request.display_name, t=t, llm_config=llm_config, user=user
        )
        description_entity = await KnowledgeService._create_and_translate_locale_entity(
            request.description, t, llm_config, user
        )

        updated_entity = NamespaceEntity.update_namespace(
            namespace_id=namespace_id,
            display_name=display_name_entity,
            description=description_entity,
        )

        return NamespaceResponse(
            id=str(updated_entity.id),
            bucket_id=updated_entity.bucket_id,
            namespace_name=updated_entity.namespace_name,
            folder_name=updated_entity.folder_name,
            display_name=KnowledgeService._safe_extract_locale_string(updated_entity.display_name, t),
            description=KnowledgeService._safe_extract_locale_string(updated_entity.description, t),
        )

    @staticmethod
    async def initiate_document_upload(
        database: str, namespace: str, request: DocumentUploadRequest, s3_service: S3AnonymousFileAccessService
    ) -> DocumentUploadResponse:
        """
        Initiates document upload by generating a presigned URL for the globally configured datalake.

        This method resolves logical database/namespace names to physical storage locations,
        validates the upload request, generates a unique object key, and creates a presigned URL
        for direct upload to the configured datalake storage.
        """

        try:
            bucket_entity = BucketEntity.get_bucket_by_db_name(database)
            namespace_entity = NamespaceEntity.get_namespace_by_bucket_and_name(
                bucket_id=str(bucket_entity.id), namespace_name=namespace
            )
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Database '{database}' or namespace '{namespace}' not found",
            ) from e

        container = bucket_entity.bucket_name
        folder = namespace_entity.folder_name

        upload_id = str(uuid.uuid4())
        object_key = f"{folder}/{request.filename}"

        presigned_url = s3_service.generate_upload_url(
            container=container,
            file_path=object_key,
            content_type=request.content_type,
            lifetime_hours=1,  # 1 hour expiration
        )

        return DocumentUploadResponse(
            upload_url=presigned_url,
            upload_id=upload_id,
            container=container,
            object_key=object_key,
            expires_in=3600,  # 1 hour in seconds
            folder=folder,
        )

    @staticmethod
    async def validate_document_upload(
        nc: NATS,
        database: str,
        namespace: str,
        request: DocumentUploadValidationRequest,
        s3_service: S3AnonymousFileAccessService,
    ) -> DocumentUploadValidationResponse:
        """
        Validates whether a file was successfully uploaded to the globally configured datalake.

        This method verifies that the uploaded file exists in the datalake storage, creates
        a placeholder RefDoc to track the file with status=pending, and publishes a
        SourceUpdatedEvent to NATS to trigger downstream pipeline processing via Dagster sensors.
        """
        try:
            bucket_entity = BucketEntity.get_bucket_by_db_name(database)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Database '{database}' or namespace '{namespace}' not found",
            ) from e

        container = bucket_entity.bucket_name
        object_key = request.file_path

        exists = s3_service.verify_file_exists(container=container, file_path=object_key)

        if exists:
            KnowledgeService._ensure_db_exists(database)
            source = f"{_S3_URI_SCHEME}{container}/{object_key}"
            document_title = object_key.split("/")[-1]

            try:
                RefDoc.get_or_create_placeholder(
                    db_alias=database,
                    source=source,
                    namespace=namespace,
                    document_title=document_title,
                )
            except Exception as e:
                logger.warning(f"Failed to create placeholder for {object_key}: {e}")

            # Publish event to trigger pipeline - this must succeed or upload fails
            try:
                await SourceUpdatedPublisher.publish(nc, bucket_entity, object_key)
            except Exception as e:
                logger.exception(f"Failed to publish event for {object_key}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Upload succeeded but processing could not be initiated. Please try again.",
                ) from e

        return DocumentUploadValidationResponse(exists=exists, file_path=object_key, container=container)

    @staticmethod
    @trace_fn
    def get_document_url(
        db: str,
        namespace: str,
        document_id: str,
        s3_service: S3AnonymousFileAccessService,
        as_attachment: bool = False,
    ) -> str:
        """Generates a presigned S3 URL for a document's source file.

        `as_attachment` forces a browser download via `Content-Disposition: attachment`
        instead of inline preview (requires SeaweedFS ≥ 4.01 to honor the override).
        """
        KnowledgeService._ensure_db_exists(db)
        try:
            ref_doc = RefDoc.by_id_and_namespace(db_alias=db, doc_id=document_id, namespace=namespace)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Document not found")
        source = ref_doc.data.metadata.source
        source = source.removeprefix(_S3_URI_SCHEME)
        parts = source.split("/", 1)
        container = parts[0]
        file_path = parts[1] if len(parts) > 1 else ""
        content_disposition = None
        if as_attachment:
            filename = file_path.rsplit("/", 1)[-1]
            content_disposition = f'attachment; filename="{filename}"'
        return s3_service.generate_sas_url(container, file_path, response_content_disposition=content_disposition)

    @staticmethod
    def get_supported_file_types() -> list[str]:
        return FileTypeConfig().get_unique_extensions()

    @staticmethod
    @trace_fn
    async def delete_document(
        nc: NATS,
        db: str,
        namespace: str,
        document_id: str,
        s3_service: S3AnonymousFileAccessService,
    ) -> None:
        """
        Schedules permanent deletion of a document by removing its source file from the data lake.

        Only the S3 file (and its figures) is deleted directly. The published SourceUpdatedEvent
        triggers the pipeline's observe job, which drops the partition; the chained remove job
        then cleans the doc store and vector store. Keeping the pipeline as the single writer for
        those stores avoids races with in-flight ingestion runs.
        """
        KnowledgeService._ensure_db_exists(db)
        try:
            ref_doc = RefDoc.by_id_and_namespace(db_alias=db, doc_id=document_id, namespace=namespace)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Document not found")

        source = ref_doc.data.metadata.source
        _, file_path = KnowledgeService._delete_source_from_data_lake(s3_service, source)
        await SourceUpdatedPublisher.publish(nc, BucketEntity.get_bucket_by_db_name(db), file_path)

    @staticmethod
    def _delete_source_from_data_lake(s3_service: S3AnonymousFileAccessService, source: str) -> tuple[str, str]:
        if not source.startswith(_S3_URI_SCHEME):
            raise HTTPException(status_code=500, detail=f"Document source '{source}' is not an {_S3_URI_SCHEME} URI")

        parts = source.removeprefix(_S3_URI_SCHEME).split("/", 1)
        container = parts[0]
        file_path = parts[1] if len(parts) > 1 else ""
        if not file_path:
            raise HTTPException(status_code=500, detail=f"Document source '{source}' has no object key")

        s3_service.delete_file(container=container, file_path=file_path)
        return container, file_path

    @staticmethod
    @trace_fn
    async def batch_delete_documents(
        nc: NATS,
        db: str,
        namespace: str,
        document_ids: list[str],
        s3_service: S3AnonymousFileAccessService,
    ) -> BatchDeleteDocumentsResponse:
        """Best-effort batch deletion: each document is scheduled independently with a per-document result."""
        results = []
        for document_id in document_ids:
            try:
                await KnowledgeService.delete_document(nc, db, namespace, document_id, s3_service)
                status = "scheduled"
            except HTTPException as e:
                status = "not_found" if e.status_code == 404 else "failed"
            except Exception:
                logger.exception(f"Failed to schedule deletion of document {document_id} in {db}/{namespace}")
                status = "failed"
            results.append(DocumentDeletionResult(document_id=document_id, status=status))
        return BatchDeleteDocumentsResponse(results=results)

    @staticmethod
    def _is_legacy_bucket(bucket: BucketEntity) -> bool:
        """Whether the bucket belongs to a legacy deploy-bound pipeline (``default_rag`` / ``shared_rag``)."""
        return bucket.ingestor in (IngestorType.DEFAULT_RAG.value, IngestorType.SHARED_RAG.value)

    @staticmethod
    def reserved_database_names() -> frozenset[str]:
        """Names a new knowledge database may never be created on.

        A database's name doubles as its Mongo store and Milvus collection, so Mongo's own system databases
        and the application's main database would collide, and the two legacy names would put a new database
        on top of a frozen corpus that has no migration path. Spelled out rather than derived from
        ``non_browsable_database_names``, so that widening one policy cannot silently widen the other.
        """
        aihub_settings = AIHubSettings()
        return _SYSTEM_DATABASE_NAMES | {
            aihub_settings.MONGO_MAIN_DB_NAME,
            aihub_settings.DEFAULT_BUCKET_NAME,
            aihub_settings.SHARED_BUCKET_NAME,
        }

    @staticmethod
    def non_browsable_database_names() -> frozenset[str]:
        """Names no caller may read from or delete in, whatever access rules they hold.

        Reserving a name for creation is not a reason to refuse reads of the database already on it, so the
        legacy names appear here only when the deployment hides legacy knowledge, making hidden mean
        unreadable rather than merely unlisted. Uploads and namespace creation stay open either way.
        """
        # Keyed on the two configured names, while get_databases hides by the bucket's ingestor. The two
        # agree unless a deployment renamed its buckets after seeding, which would leave such a bucket
        # unlisted yet readable by name; closing that would cost a bucket lookup on every guarded read.
        aihub_settings = AIHubSettings()
        system_names = _SYSTEM_DATABASE_NAMES | {aihub_settings.MONGO_MAIN_DB_NAME}
        if aihub_settings.SHOW_LEGACY_KNOWLEDGE:
            return frozenset(system_names)
        return frozenset(system_names | {aihub_settings.DEFAULT_BUCKET_NAME, aihub_settings.SHARED_BUCKET_NAME})

    @staticmethod
    def _is_database_deletable(bucket: BucketEntity) -> bool:
        """Whether the database *itself* may be torn down.

        Auto-synced databases are refilled by their source. A legacy ``default_rag`` / ``shared_rag`` bucket is
        re-provisioned by three separate paths — the API's bucket seeder, the S3 init script, and its own
        pipeline's definitions build — so removing it needs the code location retired afterwards, which the
        platform cannot do for the operator. Its namespaces and its documents are deletable; only the
        database as a whole is not.
        """
        return not bucket.auto_sync and not KnowledgeService._is_legacy_bucket(bucket)

    @staticmethod
    def _reject_if_auto_synced(bucket: BucketEntity) -> None:
        """Guard shared by database and namespace deletion: an auto-synced database's content is owned by its
        external source and would just be re-synced, so nothing in it may be deleted from the UI."""
        if bucket.auto_sync:
            raise HTTPException(
                status_code=403, detail=f"Database '{bucket.db_name}' is auto-synced and cannot be deleted."
            )

    @staticmethod
    def _reject_undeletable_database(bucket: BucketEntity) -> None:
        """Whole-database deletion guard: auto-synced and legacy databases are protected.

        Mongo-internal / main-db names are rejected earlier, at the controller, via the hidden-name guard.
        """
        KnowledgeService._reject_if_auto_synced(bucket)
        if KnowledgeService._is_legacy_bucket(bucket):
            raise HTTPException(status_code=403, detail=f"Legacy database '{bucket.db_name}' cannot be deleted.")

    @staticmethod
    @trace_fn
    def delete_database(database: str) -> None:
        """Flag a knowledge database (and its namespaces) for teardown; the pipeline does the heavy purge.

        The synchronous work is O(1): flip the ``deleting`` flag, which excludes the rows from every
        enumeration path so ingestion stops at once. The flag *is* the durable teardown request — the
        pipeline's teardown sensor reads it directly, so there is no message that could be published,
        acknowledged and then lost, leaving the database hidden but never purged. The Dagster job drops the
        Milvus collection, the doc-store database and the S3 bucket, and hard-deletes the rows last.
        """
        try:
            bucket = BucketEntity.get_bucket_by_db_name(database)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Database '{database}' not found") from None

        KnowledgeService._reject_undeletable_database(bucket)

        # Revoke first, while the namespace rows are still enumerable: once the flags are set the
        # teardown job may hard-delete them, and their rules would then have nothing left to name.
        namespaces = NamespaceEntity.get_namespaces_by_bucket(str(bucket.id))
        KnowledgeService._revoke_knowledge_access(
            rules=[
                AccessChecker.knowledge_database_user_rule(database),
                AccessChecker.knowledge_database_admin_rule(database),
                *[
                    rule
                    for entity in namespaces
                    for rule in (
                        AccessChecker.knowledge_namespace_user_rule(database, entity.namespace_name),
                        AccessChecker.knowledge_namespace_admin_rule(database, entity.namespace_name),
                    )
                ],
            ],
            role_names=[
                KnowledgeService._knowledge_admin_role_name(database),
                *[
                    KnowledgeService._knowledge_admin_role_name(database, entity.namespace_name)
                    for entity in namespaces
                ],
            ],
        )

        BucketEntity.mark_deleting(str(bucket.id))
        NamespaceEntity.mark_all_deleting_for_bucket(str(bucket.id))

    @staticmethod
    @trace_fn
    def delete_namespace(database: str, namespace: str) -> None:
        """Flag a single namespace for teardown; the bucket and its other namespaces survive.

        Same flag-as-request shape as ``delete_database``. The teardown job deletes the namespace's S3
        folder, its doc-store rows and its Milvus vectors (by metadata filter — never a partition drop,
        since namespaces share hashed partitions), then hard-deletes the row.
        """
        try:
            bucket = BucketEntity.get_bucket_by_db_name(database)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Database '{database}' not found") from None

        # Only auto-sync is refused. A legacy database's namespaces are deletable: its frozen images carry the
        # teardown sensor from v0.320.1, so the flag this sets is a queue something actually reads.
        KnowledgeService._reject_if_auto_synced(bucket)

        try:
            namespace_entity = NamespaceEntity.get_namespace_by_bucket_and_name(str(bucket.id), namespace)
        except DoesNotExist:
            raise HTTPException(
                status_code=404, detail=f"Folder '{namespace}' not found in database '{database}'"
            ) from None

        KnowledgeService._revoke_knowledge_access(
            rules=[
                AccessChecker.knowledge_namespace_user_rule(database, namespace_entity.namespace_name),
                AccessChecker.knowledge_namespace_admin_rule(database, namespace_entity.namespace_name),
            ],
            role_names=[
                KnowledgeService._knowledge_admin_role_name(database, namespace_entity.namespace_name),
            ],
        )

        NamespaceEntity.mark_deleting(str(namespace_entity.id))
