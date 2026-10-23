import asyncio
from typing import ClassVar
from weakref import WeakKeyDictionary


class ExtractionSlots:
    """Bounds on one agent replica's extraction work, per profile: model calls at once, and documents held at once.

    Every document is one or more model calls, and a request fans out to all of its documents and their windows at
    once; without a bound, one large request saturates the model gateway for every other user of that model, or holds
    every document's text in memory. The two bounds are separate semaphores, so a document waiting for its windows
    never holds the slot a window needs. A semaphore lives in one event loop, so the slots are kept per loop, per
    name and per cap: a profile whose cap is edited gets new slots.
    """

    _slots: ClassVar[WeakKeyDictionary[asyncio.AbstractEventLoop, dict[tuple[str, int], asyncio.Semaphore]]] = (
        WeakKeyDictionary()
    )

    @classmethod
    def of(cls, name: str, size: int) -> asyncio.Semaphore:
        per_loop = cls._slots.setdefault(asyncio.get_running_loop(), {})
        return per_loop.setdefault((name, size), asyncio.Semaphore(size))

    @classmethod
    def calls(cls, agent_id: str, size: int) -> asyncio.Semaphore:
        """Model calls the profile's extractions make at once on this replica."""
        return cls.of(f"{agent_id}:calls", size)

    @classmethod
    def documents(cls, agent_id: str, size: int) -> asyncio.Semaphore:
        """Documents loaded and extracted at once; twice the calls, so loading overlaps with the model's work."""
        return cls.of(f"{agent_id}:documents", size * 2)
