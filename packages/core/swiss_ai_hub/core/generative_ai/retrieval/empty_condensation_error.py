class EmptyCondensationError(RuntimeError):
    """The condenser returned no usable standalone question.

    Raised rather than degraded because the condensed question is the only carrier of the user's intent
    downstream: it is what retrieval and memory search embed, what mem0 stores as the turn's user half, and
    what `ExpertRAGAgent` posts to a human. `FewShotAgent` goes further and drops the chat history and the
    original message from its final prompt, so an empty condensation there leaves the model classifying
    nothing at all.

    Every alternative produces an answer that looks grounded and is not. Falling back to the raw last user
    message is not one either: under a full-context chat client that message is the document-inlined prompt
    (issue #1753), and telling a clean message from an augmented one would mean coupling to the client's
    `RAG_TEMPLATE`.
    """
