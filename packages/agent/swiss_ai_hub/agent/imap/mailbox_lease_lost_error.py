class MailboxLeaseLostError(RuntimeError):
    """This run's claim on the mailbox expired while it was still working, so another run may hold it now.

    Raised instead of filing anyway. Filing is what moves messages out of the inbox, and it is the only thing
    stopping the next run from reprocessing them — so two runs filing the same batch is the one outcome the lease
    exists to prevent, and reaching this point means the guard has already failed at its own job.

    Loud rather than a quiet stop: a heartbeated lease only lapses when a single phase outran the whole TTL, which
    is an operational problem — a mailbox or a model slow enough to need a longer TTL, or a stalled connection —
    and not something a run should absorb silently.
    """
