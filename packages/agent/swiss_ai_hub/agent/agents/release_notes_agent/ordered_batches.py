import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import Annotated


class OrderedBatches:
    """Runs one call per batch, a few at a time, and hands the results on in the batches' order.

    A result is handed on as soon as it and every one before it are done, so a chat streaming them waits about one
    call between chunks rather than for the whole release. A failing call cancels the others, as one failed embedding
    request does in `AttachedFileSections`.
    """

    @staticmethod
    async def run[TBatch, TResult](
        batches: Annotated[Sequence[TBatch], "The batches, in the order their results are handed on"],
        call: Annotated[Callable[[TBatch], Awaitable[TResult]], "The work for one batch"],
        on_result: Annotated[Callable[[TResult], Awaitable[None]], "Receives each result, in the batches' order"],
        concurrency: Annotated[int, "How many calls run at once"],
    ) -> list[TResult]:
        slots = asyncio.Semaphore(concurrency)

        async def in_a_slot(batch: TBatch) -> TResult:
            async with slots:
                return await call(batch)

        results: list[TResult] = []
        try:
            async with asyncio.TaskGroup() as group:
                tasks = [group.create_task(in_a_slot(batch)) for batch in batches]
                for task in tasks:
                    results.append(await task)
                    await on_result(results[-1])
        except ExceptionGroup as failure:
            raise failure.exceptions[0] from failure
        return results
