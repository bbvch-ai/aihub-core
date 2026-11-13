import asyncio
import inspect
import logging
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, PrivateAttr

from aihub_mods.mod_run_context import ModRunContext


class ModRun(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    filters: list[tuple[Any, ModRunContext]]
    _bound: bool = PrivateAttr(default=False)

    def bind_task(self) -> None:
        if not self._bound:
            task = asyncio.current_task()
            if task is None:
                raise RuntimeError("Mod hooks require an active async task")
            task.add_done_callback(self._finished)
            self._bound = True

    def _finished(self, task: asyncio.Task[Any]) -> None:
        for _, context in self.filters:
            context.close()
        closing = asyncio.create_task(self._emit_end())
        closing.add_done_callback(self._report_end)

    async def _emit_end(self) -> None:
        if self.filters:
            context = self.filters[0][1]
            if context.event_emitter and context.execution_id:
                await context.event_emitter({"type": "aihub:mods:end", "data": context.scope()})

    @staticmethod
    def _report_end(task: asyncio.Task[None]) -> None:
        if not task.cancelled() and (error := task.exception()):
            logging.getLogger(__name__).error("Failed to deliver mod execution end", exc_info=(type(error), error, error.__traceback__))

    async def apply(self, hook: Literal["inlet", "request", "stream", "outlet"], value: Any) -> Any:
        for instance, context in self.filters:
            handler = getattr(instance, hook, None)
            if handler is None:
                continue
            if not inspect.iscoroutinefunction(handler):
                raise TypeError(f"Mod {context.mod_id} {hook} must be async. Please contact your administrator.")
            value = await handler(value, context)
            if hook == "stream" and value is None:
                return None
            if not isinstance(value, dict):
                raise TypeError(f"Mod {context.mod_id} {hook} must return a dictionary. Please contact your administrator.")
        return value
