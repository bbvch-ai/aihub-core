class OpenTerminalError(Exception):
    """The sandbox refused a request; the message carries its reason so a model can correct the call."""
