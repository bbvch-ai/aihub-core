class MessageVanishedError(ValueError):
    """A listed UID no longer exists — another client expunged or moved it between the listing and this command.

    Subclasses ``ValueError`` so a caller that does not distinguish failure causes keeps working unchanged; a batch
    caller catches this specifically to skip the message instead of losing the whole batch to it. It must stay
    distinct from the ``max_message_bytes`` refusal, which is a real failure that has to stay loud.
    """
