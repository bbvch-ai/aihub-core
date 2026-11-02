from datetime import datetime

from mongoengine import DateTimeField, Document, StringField

from swiss_ai_hub.core.discovery.discovery_kind import DiscoveryKind
from swiss_ai_hub.core.discovery.discovery_settings import DiscoverySettings
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class DiscoveryRoundEntity(Document):
    """One discovery round that completed, kept so online status can be judged against rounds, not the clock.

    A round that fails or stalls is never written, so it moves no class towards offline. One document per
    round rather than a capped array keeps every write an insert, which needs no `$push`/`$slice` support
    from FerretDB. Rows are not tagged by writer, so only one API process may record rounds: with several,
    "the last N rounds" would span a fraction of the configured time. The discovery service holds a Redis
    lease for that.

    `started_at` is naive **local** time, the clock `last_discovered` is stamped with (see #1968). It is the
    round's start, not its end: a class that answered is stamped after the response wait, so it always
    lies at or after the start of the round it answered.
    """

    meta = {
        "collection": "discovery_rounds",
        "indexes": [{"fields": ["kind", "-started_at"]}],
    }

    kind = StringField(required=True, choices=[kind.value for kind in DiscoveryKind])
    started_at = DateTimeField(required=True)

    @classmethod
    @trace_fn
    def record_completed(cls, kind: DiscoveryKind, started_at: datetime, settings: DiscoverySettings) -> None:
        """Adds the round and drops those no threshold can reach any more."""
        cls(kind=kind.value, started_at=started_at).save()
        oldest_needed = cls._nth_most_recent(kind, settings.MISSED_ROUNDS_BEFORE_OFFLINE)
        if oldest_needed is not None:
            cls.objects(kind=kind.value, started_at__lt=oldest_needed.started_at).delete()

    @classmethod
    @trace_fn
    def online_threshold(cls, kind: DiscoveryKind, settings: DiscoverySettings | None = None) -> datetime:
        """The oldest `last_discovered` that still counts as online.

        That is the start of the round `MISSED_ROUNDS_BEFORE_OFFLINE` completed rounds back: a class stamped
        before it has missed every round since. Until that many rounds exist — a fresh install — the
        wall-clock window those rounds would span stands in.

        It is never older than `MAX_SILENCE_SECONDS`: a fault that fails every round — NATS down for good, the
        database rejecting the round — would otherwise freeze it and keep dead classes online indefinitely,
        and so would the rounds left from before the API was down.
        """
        settings = settings or DiscoverySettings()
        now = datetime.now()
        oldest_counted = cls._nth_most_recent(kind, settings.MISSED_ROUNDS_BEFORE_OFFLINE)
        if oldest_counted is None:
            return now - settings.cold_start_window
        return max(oldest_counted.started_at, now - settings.max_silence)

    @classmethod
    def _nth_most_recent(cls, kind: DiscoveryKind, n: int) -> "DiscoveryRoundEntity | None":
        return cls.objects(kind=kind.value).order_by("-started_at").skip(n - 1).first()
