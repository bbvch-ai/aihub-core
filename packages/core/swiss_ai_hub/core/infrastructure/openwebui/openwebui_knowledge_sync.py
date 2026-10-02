import asyncio
import logging
from typing import Any

import httpx
from scim2_models import Group

from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference
from swiss_ai_hub.core.generative_ai.retrievers.knowledge_collection_label import KnowledgeCollectionLabel
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.openwebui.access_grant import AccessGrant
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_client import OpenWebuiClient
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_group_access import (
    OpenWebuiGroupAccess,
    RoleAccessRules,
    TenantAccessRules,
)
from swiss_ai_hub.core.persistence.openwebui.openwebui_knowledge_entry_entity import OpenWebuiKnowledgeEntryEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity
from swiss_ai_hub.core.persistence.rag.datalake.knowledge_visibility import KnowledgeVisibility

logger = logging.getLogger(__name__)

type Listing = dict[tuple[str, str], tuple[str, str]]
"""Maps (database, namespace) to the entry's name and description."""


class OpenWebuiKnowledgeSync:
    """Keeps one OpenWebUI knowledge entry per collection of ours, so users can reference it with `#` in a chat.

    An entry holds no content and OpenWebUI runs no retrieval on it: agent models do not read files, and a
    referenced entry reaches the agent as a reference to our collection. Each entry is readable by exactly the role
    groups whose rules let them read the collection; entries whose collection is gone are removed.
    """

    def __init__(self, openwebui: OpenWebuiClient, locale: str) -> None:
        self._openwebui = openwebui
        self._locale = locale

    async def sync(
        self,
        http: httpx.AsyncClient,
        groups: list[Group],
        tenant_rules: TenantAccessRules,
        role_rules: RoleAccessRules,
    ) -> None:
        listing = await asyncio.to_thread(self.listing)
        entries = {
            (entry.database, entry.namespace): entry
            for entry in await asyncio.to_thread(OpenWebuiKnowledgeEntryEntity.current_entries)
        }
        existing = {knowledge["id"]: knowledge for knowledge in await self._openwebui.list_own_knowledge(http)}

        for key, (name, description) in listing.items():
            reference = KnowledgeReference(database=key[0], namespace=key[1])
            grants = OpenWebuiGroupAccess.read_grants(
                groups,
                tenant_rules,
                role_rules,
                lambda checker, database=key[0], namespace=key[1]: checker.has_access_to_knowledge_namespace(
                    database, namespace
                ),
            )
            entry = entries.get(key)
            current = existing.get(entry.openwebui_id) if entry else None
            if current is None:
                created = await self._openwebui.create_knowledge(http, name, description, grants)
                await asyncio.to_thread(OpenWebuiKnowledgeEntryEntity.record, created["id"], reference)
                logger.info("OpenWebUI: Created knowledge entry '%s'", name)
            elif self._differs(current, name, description, grants):
                await self._openwebui.update_knowledge(http, current["id"], name, description, grants)
                logger.info("OpenWebUI: Updated knowledge entry '%s'", name)

        await self._remove_stale(http, listing, entries, existing)

    async def _remove_stale(
        self,
        http: httpx.AsyncClient,
        listing: Listing,
        entries: dict[tuple[str, str], OpenWebuiKnowledgeEntryEntity],
        existing: dict[str, dict[str, Any]],
    ) -> None:
        """Entries whose collection is gone, and ones the service account created but nothing maps any more.

        An entry OpenWebUI no longer has, because an administrator deleted it there, is only retired: OpenWebUI
        refuses to delete an id it does not know, and that refusal would stop every later sync at the same entry.
        The second kind is left behind by a sync that created an entry and stopped before recording it; removing it
        keeps the `#` picker from listing a collection twice.
        """
        for key, entry in entries.items():
            if key not in listing:
                if entry.openwebui_id in existing:
                    await self._openwebui.delete_knowledge(http, entry.openwebui_id)
                await asyncio.to_thread(OpenWebuiKnowledgeEntryEntity.retire, entry.openwebui_id)
                logger.info("OpenWebUI: Removed knowledge entry for '%s/%s'", *key)
        for knowledge_id in set(existing) - {entry.openwebui_id for entry in entries.values()}:
            await self._openwebui.delete_knowledge(http, knowledge_id)
            logger.info("OpenWebUI: Removed unmapped knowledge entry '%s'", knowledge_id)

    def listing(self) -> Listing:
        """Every live collection the knowledge page offers, named "Database / Collection" in the deployment's
        model-name locale."""
        handler = LocaleHandler(self._locale)
        listing: Listing = {}
        for bucket in BucketEntity.get_all_buckets():
            if bucket.deleting or not KnowledgeVisibility.is_browsable(bucket):
                continue
            for namespace in NamespaceEntity.get_namespaces_by_bucket(str(bucket.id)):
                if namespace.deleting:
                    continue
                description = (handler.extract(namespace.description) or "") if namespace.description else ""
                listing[(bucket.db_name, namespace.namespace_name)] = (
                    KnowledgeCollectionLabel.of(bucket, namespace, self._locale),
                    description,
                )
        return listing

    @staticmethod
    def _differs(current: dict[str, Any], name: str, description: str, grants: list[AccessGrant]) -> bool:
        current_grants = {
            (grant.get("principal_type"), grant.get("principal_id"), grant.get("permission"))
            for grant in current.get("access_grants") or []
        }
        wanted = {(grant.principal_type, grant.principal_id, grant.permission) for grant in grants}
        return (
            current.get("name") != name or (current.get("description") or "") != description or current_grants != wanted
        )
