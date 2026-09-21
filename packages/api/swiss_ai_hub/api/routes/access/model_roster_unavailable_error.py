class ModelRosterUnavailableError(RuntimeError):
    """Raised when the live model roster cannot be read, so a tenant's default ceiling cannot be derived.

    Distinct from a transport error so callers can translate it into an actionable response instead of
    writing a tenant whose ceiling silently grants no models at all.
    """
