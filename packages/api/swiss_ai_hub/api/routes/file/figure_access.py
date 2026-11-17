import asyncio
import re
from typing import Annotated, ClassVar

from beanie.exceptions import DocumentNotFound
from bson import ObjectId
from fastapi import HTTPException, Request, status
from redis.asyncio import Redis
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.generative_ai import FIGURES_DIRECTORY_NAME, create_figures_folder_name
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import ThreadEntity

from swiss_ai_hub.api.routes.thread.thread_access import ThreadAccess

_FIGURE_NOT_AVAILABLE = "This figure is not available to you."


class FigureAccess:
    """Lets a viewer see a knowledge figure exactly when they can read the chunk it belongs to.

    The chunk reached them through a thread: the figure must be in grounding results an agent sent to that thread, and
    the viewer must still be allowed to view the thread and to use that agent. Namespace access would be the wrong
    rule, since a profile not restricted to the user's access shows chunks of collections the user cannot browse.

    A figure node's text comes from the document, and a markdown document can hold any `<figure>` reference, so a
    reference only counts when it lies in the figure folder of the node's own document. Otherwise one uploaded file
    could make this route read figures of any bucket with the platform's credentials.
    """

    GROUNDING_EVENT_NAMES: ClassVar[tuple[str, ...]] = ("KnowledgeSearchedEvent", "InOrderNodeCombinerEvent")
    FIGURE_CONTENT_TYPE: ClassVar[str] = "figure"
    RASTER_EXTENSIONS: ClassVar[frozenset[str]] = frozenset({"jpg", "jpeg", "png", "webp", "gif", "bmp"})
    ALLOWED_FETCH_DESTINATIONS: ClassVar[frozenset[str]] = frozenset({"image", "document"})
    CACHE_SECONDS: ClassVar[int] = 300
    _CACHE_PREFIX: ClassVar[str] = "figure_access:"
    # A figure node holds exactly one image; its folder path may contain spaces and brackets, which ingestion keeps.
    _FIGURE: ClassVar[re.Pattern[str]] = re.compile(r"\s*!\[[^\]]*\]\((s3://.+)\)\s*", re.DOTALL)

    @staticmethod
    def ensure_requested_from_openwebui(request: Request) -> None:
        """Only OpenWebUI's own pages may load a figure: an image tag, or opening the image in a new tab.

        The browser sets these headers itself, so script on another host of the same site cannot read a figure with
        the viewer's cookie, even where CORS would let it: a script's request is never an image or a document. A URL
        pasted into the address bar is not same-origin and is refused too.
        """
        headers = request.headers
        if (
            headers.get("sec-fetch-site") != "same-origin"
            or headers.get("sec-fetch-dest") not in FigureAccess.ALLOWED_FETCH_DESTINATIONS
        ):
            raise FigureAccess._not_available()

    @staticmethod
    async def ensure_may_view(
        tenant_id: Annotated[str, "Tenant the viewer acts in, as named in the URL"],
        thread_id: Annotated[str, "Thread the figure was shown in"],
        container: Annotated[str, "Knowledge bucket"],
        file_path: Annotated[str, "Key of the figure in the bucket"],
        user: Annotated[UserIdentity, "The viewer"],
        redis: Annotated[Redis, "Caches granted access"],
    ) -> None:
        if tenant_id == AuthHandler.ACTIVE_TENANT_SLUG:
            raise FigureAccess._not_available()
        FigureAccess._ensure_is_figure_key(file_path)
        cache_key = FigureAccess._cache_key(thread_id, container, file_path, user)
        if await redis.get(cache_key) is not None:
            return

        thread = await FigureAccess._thread(thread_id)
        if not ThreadAccess.can_view_entity(thread, user):
            raise FigureAccess._not_available()

        reference = f"s3://{container}/{file_path}"
        agent = await asyncio.to_thread(FigureAccess._agent_that_showed, thread_id, reference)
        if agent is None or not FigureAccess._may_use(user, *agent):
            raise FigureAccess._not_available()

        await redis.set(cache_key, "1", ex=FigureAccess.CACHE_SECONDS)

    @staticmethod
    def shows(
        node: Annotated[dict, "A grounding node as an event carries it"],
        reference: Annotated[str, "`s3://bucket/key` of a figure"],
    ) -> bool:
        """Whether the node is a figure whose own document's figure folder holds the reference."""
        source = node.get("source") or ""
        if node.get("content_type") != FigureAccess.FIGURE_CONTENT_TYPE or not source.startswith("s3://"):
            return False
        if not reference.startswith(f"{create_figures_folder_name(source)}/"):
            return False
        match = FigureAccess._FIGURE.fullmatch(node.get("content") or "")
        return match is not None and match.group(1) == reference

    @staticmethod
    def _ensure_is_figure_key(file_path: str) -> None:
        """Ingestion stores every figure under a `__figures__` folder; nothing else is ever served this way."""
        segments = file_path.split("/")
        extension = segments[-1].rsplit(".", 1)[-1].lower() if "." in segments[-1] else ""
        if (
            any(segment in {"", ".", ".."} for segment in segments)
            or FIGURES_DIRECTORY_NAME not in segments[:-1]
            or extension not in FigureAccess.RASTER_EXTENSIONS
        ):
            raise FigureAccess._not_available()

    @staticmethod
    async def _thread(thread_id: str) -> ThreadEntity:
        if not ObjectId.is_valid(thread_id):
            raise FigureAccess._not_available()
        try:
            return await ThreadEntity.get_thread_by_id(thread_id)
        except DocumentNotFound:
            raise FigureAccess._not_available()

    @staticmethod
    def _agent_that_showed(thread_id: str, reference: str) -> tuple[str, str] | None:
        for event_name in FigureAccess.GROUNDING_EVENT_NAMES:
            for event in PersistedAgentEventEntity.display_events_for_thread(thread_id, event_name=event_name):
                nodes = event.event_data.get("grounding_nodes") or []
                if any(FigureAccess.shows(node, reference) for node in nodes):
                    return event.agent_class, event.agent_id
        return None

    @staticmethod
    def _may_use(user: UserIdentity, agent_class: str, agent_id: str) -> bool:
        try:
            return AccessChecker.from_user(user).has_access_to_agent(agent_class, agent_id)
        except ValueError:
            return False

    @staticmethod
    def _cache_key(thread_id: str, container: str, file_path: str, user: UserIdentity) -> str:
        tenant_id = user.acting_within_tenant.id if user.acting_within_tenant else ""
        return f"{FigureAccess._CACHE_PREFIX}{user.id}:{tenant_id}:{thread_id}:{container}/{file_path}"

    @staticmethod
    def _not_available() -> HTTPException:
        """One answer for a missing thread, a foreign one and an unknown figure, so none can be probed apart."""
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_FIGURE_NOT_AVAILABLE)
