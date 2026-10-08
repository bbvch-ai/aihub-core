from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_record import RecordValue

Record = dict[str, RecordValue]


class RecordMerger:
    """Joins per-window records into one list, dropping the copies the window overlap produced.

    Only records of *adjacent* windows are compared, since only adjacent windows share text: two identical invoice
    lines far apart in a document are two lines, not a duplicate. Within one window nothing is dropped either, for the
    same reason. Records are matched as *compatible* rather than equal, because a window that cuts off the invoice
    header extracts the same line with the header fields set to null; the kept record takes the other's non-null
    values. Each record can absorb at most one record of the next window, so two real repeats in an overlap survive.
    """

    @staticmethod
    def merge(windows: list[list[Record]]) -> list[Record]:
        merged: list[Record] = []
        previous_window: list[int] = []
        for window in windows:
            unclaimed = list(previous_window)
            current_window = []
            for record in window:
                match = RecordMerger._first_compatible(record, unclaimed, merged)
                if match is None:
                    merged.append(dict(record))
                    current_window.append(len(merged) - 1)
                    continue
                unclaimed.remove(match)
                RecordMerger._fill_gaps(merged[match], record)
                current_window.append(match)
            previous_window = current_window
        return merged

    @staticmethod
    def _first_compatible(record: Record, candidates: list[int], merged: list[Record]) -> int | None:
        return next((index for index in candidates if RecordMerger._compatible(record, merged[index])), None)

    @staticmethod
    def _compatible(first: Record, second: Record) -> bool:
        shared = [name for name in first if first[name] is not None and second.get(name) is not None]
        return bool(shared) and all(RecordMerger._same(first[name], second[name]) for name in shared)

    @staticmethod
    def _same(first: RecordValue, second: RecordValue) -> bool:
        if isinstance(first, str) and isinstance(second, str):
            return first.strip().casefold() == second.strip().casefold()
        return first == second

    @staticmethod
    def _fill_gaps(kept: Record, duplicate: Record) -> None:
        for name, value in duplicate.items():
            if kept.get(name) is None:
                kept[name] = value
