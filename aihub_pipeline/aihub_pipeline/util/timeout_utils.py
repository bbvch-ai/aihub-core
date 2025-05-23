import signal
from contextlib import contextmanager


class RegexTimeoutError(Exception):
    """Custom exception for regex timeout"""

    pass


@contextmanager
def timeout(seconds):
    """Context manager to enforce timeout on operations"""

    def signal_handler(signum, frame):
        raise RegexTimeoutError("Regex operation timed out")

    old_handler = signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.signal(signal.SIGALRM, old_handler)
        signal.alarm(0)
